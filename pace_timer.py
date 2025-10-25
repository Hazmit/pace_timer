#!/usr/bin/env python3
"""
Pace Timer – Raspberry Pi fullscreen display + HTTP API + Web viewer

UI:
  - Fullscreen pygame
  - Large running timer (top-right, pill border)
  - Optional logo (top-left) via PACE_LOGO_URL
  - Single row of N boxes filling left→right over time
  - Moving arrow/label "You should be here" above the current end
  - Instruction panel with auto-fit text (clipped so nothing overflows)

API:
  GET  /status
  GET  /view                    -> browser mirror of the UI
  POST /reset
  POST /pause
  POST /resume
  POST /set_remaining?seconds=... | ?time=H:MM:SS
  POST /set_total?seconds=...     | ?time=H:MM:SS
  POST /set_ends?count=N

Env:
  PACE_TOTAL_SECONDS (default 7200), PACE_NUM_ENDS (default 8),
  PACE_PORT (default 5000), PACE_LOGO_URL (optional)
"""

import os
import io
import time
import threading
import json
from typing import Optional

from flask import Flask, request, jsonify, Response, render_template, send_from_directory
import pygame


# -------------------
# Config
# -------------------
DEFAULT_TOTAL_SECONDS = 2 * 60 * 60  # 2 hours
DEFAULT_NUM_ENDS = 8
DEFAULT_PORT = 5000
CONFIG_FILE = "pace_timer_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "total_seconds": DEFAULT_TOTAL_SECONDS,
    "num_ends": DEFAULT_NUM_ENDS,
    "logo_url": "",
    "message": "Each end is 15 minutes alotted to complete a game in two hours. If you are playing too slowly then the timer will show an end that you haven't played yet. You should play faster to stay on pace."
}

# Load configuration from file or environment variables
def load_config():
    """Load configuration from file, falling back to environment variables and defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from file first
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    # Override with environment variables if they exist
    if "PACE_TOTAL_SECONDS" in os.environ:
        config["total_seconds"] = int(os.environ.get("PACE_TOTAL_SECONDS", DEFAULT_TOTAL_SECONDS))
    if "PACE_NUM_ENDS" in os.environ:
        config["num_ends"] = int(os.environ.get("PACE_NUM_ENDS", DEFAULT_NUM_ENDS))
    if "PACE_LOGO_URL" in os.environ:
        config["logo_url"] = os.environ.get("PACE_LOGO_URL", "").strip()
    
    return config

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def reload_config():
    """Reload configuration from file and update global variables"""
    global TOTAL_SECONDS, NUM_ENDS, LOGO_URL, MESSAGE_TEXT
    try:
        current_config = load_config()
        with state_lock:
            TOTAL_SECONDS = current_config["total_seconds"]
            NUM_ENDS = current_config["num_ends"]
            LOGO_URL = current_config["logo_url"]
            MESSAGE_TEXT = current_config["message"]
        print(f"Configuration reloaded: {current_config}")
        return True
    except Exception as e:
        print(f"Error reloading config: {e}")
        return False

# Load initial configuration
config = load_config()
TOTAL_SECONDS = config["total_seconds"]
NUM_ENDS = config["num_ends"]
API_PORT = int(os.environ.get("PACE_PORT", DEFAULT_PORT))
LOGO_URL = config["logo_url"]
MESSAGE_TEXT = config["message"]


# -------------------
# Shared state
# -------------------
state_lock = threading.Lock()
_start_epoch = time.time()
_manual_elapsed_offset = 0.0
_paused = False
_pause_epoch = None


def total_seconds() -> int:
    with state_lock:
        return int(TOTAL_SECONDS)


def num_ends() -> int:
    with state_lock:
        return int(NUM_ENDS)


def now_elapsed() -> float:
    with state_lock:
        if _paused:
            return max(0.0, (_pause_epoch - _start_epoch) + _manual_elapsed_offset)
        return max(0.0, (time.time() - _start_epoch) + _manual_elapsed_offset)


def set_elapsed(seconds: float):
    global _start_epoch, _manual_elapsed_offset
    with state_lock:
        _start_epoch = time.time()
        _manual_elapsed_offset = float(seconds)


def reset_timer():
    global _start_epoch, _manual_elapsed_offset
    with state_lock:
        _start_epoch = time.time()
        _manual_elapsed_offset = 0.0


def pause_timer():
    global _paused, _pause_epoch
    with state_lock:
        if not _paused:
            _paused = True
            _pause_epoch = time.time()


def resume_timer():
    global _paused, _pause_epoch, _start_epoch
    with state_lock:
        if _paused:
            paused_duration = time.time() - _pause_epoch
            _start_epoch += paused_duration
            _paused = False
            _pause_epoch = None


def parse_hms_to_seconds(s: str) -> int:
    parts = s.strip().split(":")
    if len(parts) == 1:
        return int(parts[0])
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + int(sec)
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + int(sec)
    raise ValueError("Invalid time format")


def format_seconds_clock(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"


# -------------------
# Flask API
# -------------------
app = Flask(__name__, template_folder='templates', static_folder='static')


@app.get("/status")
def status():
    el = int(now_elapsed())
    tot = total_seconds()
    rem = max(0, tot - el)
    with state_lock:
        paused = _paused
        logo = LOGO_URL
    return jsonify(
        {
            "elapsed_seconds": el,
            "remaining_seconds": rem,
            "total_seconds": tot,
            "num_ends": num_ends(),
            "paused": paused,
            "logo_url": logo,
            "message": MESSAGE_TEXT,
        }
    )


@app.post("/reset")
def reset():
    reset_timer()
    return jsonify({"ok": True, "message": "timer reset"})


@app.post("/pause")
def pause():
    pause_timer()
    return jsonify({"ok": True, "message": "timer paused"})


@app.post("/resume")
def resume():
    resume_timer()
    return jsonify({"ok": True, "message": "timer resumed"})


@app.post("/set_remaining")
def set_remaining():
    tot = total_seconds()
    seconds_param = request.args.get("seconds")
    time_param = request.args.get("time")
    if seconds_param is None and time_param is None:
        return (
            jsonify({"ok": False, "error": "Provide seconds or time query param"}),
            400,
        )
    try:
        if seconds_param is not None:
            rem = float(seconds_param)
        else:
            rem = float(parse_hms_to_seconds(time_param))
        rem = max(0.0, min(rem, float(tot)))
        elapsed_to_set = tot - rem
        set_elapsed(elapsed_to_set)
        return jsonify(
            {"ok": True, "message": "remaining set", "remaining_seconds": int(rem)}
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/set_total")
def set_total():
    global TOTAL_SECONDS
    seconds_param = request.args.get("seconds")
    time_param = request.args.get("time")
    if seconds_param is None and time_param is None:
        return jsonify({"ok": False, "error": "Provide seconds or time query param"}), 400
    try:
        if seconds_param is not None:
            new_total = int(float(seconds_param))
        else:
            new_total = int(parse_hms_to_seconds(time_param))
        if new_total <= 0:
            return jsonify({"ok": False, "error": "total must be > 0"}), 400
        el = now_elapsed()
        with state_lock:
            TOTAL_SECONDS = new_total
            if el > TOTAL_SECONDS:
                set_elapsed(TOTAL_SECONDS)
        return jsonify({"ok": True, "total_seconds": total_seconds()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/set_ends")
def set_ends():
    global NUM_ENDS
    count = request.args.get("count")
    if not count:
        return jsonify({"ok": False, "error": "Provide count=N"}), 400
    try:
        n = int(count)
        if n < 1:
            return jsonify({"ok": False, "error": "count must be >= 1"}), 400
        with state_lock:
            NUM_ENDS = n
        return jsonify({"ok": True, "num_ends": num_ends()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/add_time")
def add_time():
    """Add 1 minute to the elapsed time"""
    try:
        current_elapsed = now_elapsed()
        new_elapsed = current_elapsed + 60  # Add 1 minute
        set_elapsed(new_elapsed)
        return jsonify({"ok": True, "message": "Added 1 minute", "elapsed_seconds": int(new_elapsed)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/subtract_time")
def subtract_time():
    """Subtract 1 minute from the elapsed time"""
    try:
        current_elapsed = now_elapsed()
        new_elapsed = max(0, current_elapsed - 60)  # Subtract 1 minute, don't go below 0
        set_elapsed(new_elapsed)
        return jsonify({"ok": True, "message": "Subtracted 1 minute", "elapsed_seconds": int(new_elapsed)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/config")
def get_config():
    """Get current configuration settings"""
    with state_lock:
        current_config = load_config()
        return jsonify({
            "total_seconds": current_config["total_seconds"],
            "num_ends": current_config["num_ends"],
            "logo_url": current_config["logo_url"],
            "message": current_config["message"]
        })

@app.get("/debug")
def debug_config():
    """Debug endpoint to check current configuration state"""
    with state_lock:
        current_config = load_config()
        return jsonify({
            "file_config": current_config,
            "global_vars": {
                "TOTAL_SECONDS": TOTAL_SECONDS,
                "NUM_ENDS": NUM_ENDS,
                "LOGO_URL": LOGO_URL,
                "MESSAGE_TEXT": MESSAGE_TEXT
            },
            "config_file_exists": os.path.exists(CONFIG_FILE)
        })


@app.post("/config")
def update_config():
    """Update configuration settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "No JSON data provided"}), 400
        
        # Load current configuration
        current_config = load_config()
        updated = False
        
        # Update total seconds
        if "total_seconds" in data:
            new_total = int(data["total_seconds"])
            if new_total <= 0:
                return jsonify({"ok": False, "error": "Total seconds must be > 0"}), 400
            current_config["total_seconds"] = new_total
            updated = True
        
        # Update number of ends
        if "num_ends" in data:
            new_ends = int(data["num_ends"])
            if new_ends < 1:
                return jsonify({"ok": False, "error": "Number of ends must be >= 1"}), 400
            current_config["num_ends"] = new_ends
            updated = True
        
        # Update logo URL
        if "logo_url" in data:
            current_config["logo_url"] = str(data["logo_url"]).strip()
            updated = True
        
        # Update message text
        if "message" in data:
            current_config["message"] = str(data["message"]).strip()
            updated = True
        
        if updated:
            # Save configuration to file
            if save_config(current_config):
                # Reload configuration to ensure it's applied to running app
                if reload_config():
                    return jsonify({"ok": True, "message": "Configuration updated and saved"})
                else:
                    return jsonify({"ok": False, "error": "Configuration saved but could not reload"}), 500
            else:
                return jsonify({"ok": False, "error": "Configuration updated but could not save to file"}), 500
        else:
            return jsonify({"ok": False, "error": "No valid configuration fields provided"}), 400
            
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/view")
def view():
    """
    Template-based HTML mirror. JS pulls /status and injects the logo, timer, boxes, fills, and pointer.
    """
    return render_template('view.html')


@app.get("/configure")
def configure():
    """
    Configuration page for app settings.
    """
    return render_template('configure.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


def run_api():
    time.sleep(1)
    app.run(host="0.0.0.0", port=API_PORT, debug=False, threaded=True)


# -------------------
# Pygame UI
# -------------------
def try_load_logo_from_url(url: str, max_h: int) -> Optional[pygame.Surface]:
    if not url:
        return None
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        raw = io.BytesIO(data)
        img = pygame.image.load(raw).convert_alpha()
        w, h = img.get_size()
        if h > max_h:
            scale = max_h / float(h)
            img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
        return img
    except Exception as e:
        print("[logo] load failed:", e)
        return None


def draw_wrapped_text(surface, font, text, color, rect, line_height=1.3):
    """Render word-wrapped text inside rect; returns used height."""
    words = text.split()
    y = rect.top
    line = ""
    used = 0
    for w in words:
        trial = (line + " " + w).strip()
        if font.size(trial)[0] <= rect.width:
            line = trial
        else:
            surf = font.render(line, True, color)
            surface.blit(surf, (rect.left, y))
            y += int(font.get_linesize() * line_height)
            used = y - rect.top
            line = w
    if line:
        surf = font.render(line, True, color)
        surface.blit(surf, (rect.left, y))
        used = (y - rect.top) + font.get_linesize()
    return used


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Pace Timer")
    clock = pygame.time.Clock()

    # Colors
    BG = (10, 12, 16)
    FG = (230, 235, 240)
    ACCENT = (80, 180, 255)
    FILL = (70, 200, 120)
    PANEL_BG = (20, 22, 28)

    sw, sh = screen.get_size()
    outer_margin = int(0.035 * sw)
    box_margin = int(0.015 * sw)
    top_area_h = max(80, int(sh * 0.16))
    grid_h = max(120, int(sh * 0.38))
    msg_area_h = max(140, int(sh * 0.24))

    grid_top = outer_margin + top_area_h
    grid_left = outer_margin
    grid_right = sw - outer_margin
    grid_bottom = sh - outer_margin - msg_area_h
    grid_width = grid_right - grid_left

    # nonlocal bindings for inner recompute function
    box_rects = []
    number_font = pygame.font.SysFont(None, 100)

    def recompute_boxes(N: int):
        nonlocal box_rects, number_font
        N = max(1, N)
        box_w = int((grid_width - (N + 1) * box_margin) / N)
        box_h = int(min(grid_h, grid_bottom - grid_top))
        box_y = grid_top + (grid_bottom - grid_top - box_h) // 2
        rects = []
        for i in range(N):
            x = grid_left + box_margin + i * (box_w + box_margin)
            rects.append(pygame.Rect(x, box_y, box_w, box_h))
        number_font = pygame.font.SysFont(None, max(64, int(box_h * 0.55)))
        return rects

    box_rects = recompute_boxes(num_ends())
    timer_font = pygame.font.SysFont(None, max(42, int(top_area_h * 0.55)))
    msg_font_sz = max(28, int(msg_area_h * 0.34))
    msg_font = pygame.font.SysFont(None, msg_font_sz)
    pointer_font = pygame.font.SysFont(None, max(24, int(top_area_h * 0.28)))
    logo_surface = try_load_logo_from_url(LOGO_URL, max_h=int(top_area_h * 0.95))

    running = True
    while running:
        if len(box_rects) != num_ends():
            box_rects = recompute_boxes(num_ends())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_r:
                    reset_timer()
                elif event.key == pygame.K_SPACE:
                    with state_lock:
                        if _paused:
                            resume_timer()
                        else:
                            pause_timer()

        screen.fill(BG)

        # Timer pill (top-right)
        el = now_elapsed()
        elapsed_int = int(el)
        show_seconds = min(elapsed_int, total_seconds())
        timer_text = format_seconds_clock(show_seconds)
        with state_lock:
            if _paused:
                timer_text += "  (paused)"
        t_surf = timer_font.render(timer_text, True, FG)
        pad_x, pad_y = 16, 10
        tr = t_surf.get_rect()
        tr.top = outer_margin + (top_area_h - tr.height) // 2
        tr.right = sw - outer_margin
        timer_bg_rect = pygame.Rect(
            tr.left - pad_x, tr.top - pad_y, tr.width + 2 * pad_x, tr.height + 2 * pad_y
        )
        pygame.draw.rect(screen, PANEL_BG, timer_bg_rect, border_radius=14)
        pygame.draw.rect(screen, ACCENT, timer_bg_rect, width=2, border_radius=14)
        screen.blit(t_surf, tr)

        # Logo (top-left)
        if logo_surface:
            lr = logo_surface.get_rect()
            lr.left = outer_margin
            lr.centery = outer_margin + top_area_h // 2
            screen.blit(logo_surface, lr)

        # Boxes row & fill
        tot = float(total_seconds()) or 1.0
        frac = max(0.0, min(1.0, el / tot))
        N = len(box_rects)
        end_units = frac * N
        full_boxes = int(end_units)
        partial = end_units - full_boxes

        for idx, rect in enumerate(box_rects):
            pygame.draw.rect(screen, ACCENT, rect, width=3, border_radius=16)
            if idx < full_boxes:
                fill_w = rect.width - 6
            elif idx == full_boxes:
                fill_w = int((rect.width - 6) * partial)
            else:
                fill_w = 0
            if fill_w > 0:
                fill_rect = pygame.Rect(rect.left + 3, rect.top + 3, fill_w, rect.height - 6)
                pygame.draw.rect(screen, FILL, fill_rect, border_radius=12)
            txt = number_font.render(str(idx + 1), True, FG)
            screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2),
            )

        # Pointer arrow + label above current end
        current_idx = min(N - 1, max(0, full_boxes))
        current_rect = box_rects[current_idx]
        cx = current_rect.centerx
        arrow_tip_y = current_rect.top - 20
        arrow_half = 12
        arrow_height = 18
        points = [
            (cx, arrow_tip_y),
            (cx - arrow_half, arrow_tip_y + arrow_height),
            (cx + arrow_half, arrow_tip_y + arrow_height),
        ]
        pygame.draw.polygon(screen, ACCENT, points)

        label_text = "You should be here"
        label_surf = pointer_font.render(label_text, True, FG)
        label_bg = label_surf.get_rect()
        label_bg.midbottom = (cx, arrow_tip_y - 6)
        bg_rect = pygame.Rect(
            label_bg.left - 10, label_bg.top - 6, label_bg.width + 20, label_bg.height + 12
        )
        pygame.draw.rect(screen, PANEL_BG, bg_rect, border_radius=10)
        pygame.draw.rect(screen, ACCENT, bg_rect, width=2, border_radius=10)
        screen.blit(label_surf, label_bg)

        # Message panel (clipped, shrink-to-fit)
        msg_outer = pygame.Rect(
            outer_margin, sh - msg_area_h, sw - 2 * outer_margin, msg_area_h - outer_margin
        )
        inner = msg_outer.inflate(-20, -20)
        pygame.draw.rect(screen, PANEL_BG, msg_outer, border_radius=12)
        pygame.draw.rect(screen, ACCENT, msg_outer, width=2, border_radius=12)

        prev_clip = screen.get_clip()
        screen.set_clip(msg_outer)  # ensure nothing draws outside the panel

        # Attempt shrinking until it fits
        trial_size = msg_font_sz
        while trial_size >= 18:
            font = pygame.font.SysFont(None, trial_size)
            # clear interior each pass so we don't stack lines
            pygame.draw.rect(screen, PANEL_BG, msg_outer.inflate(-2, -2), border_radius=12)
            used = draw_wrapped_text(
                screen,
                font,
                MESSAGE_TEXT,
                FG,
                pygame.Rect(inner.left + 8, inner.top + 8, inner.width - 16, inner.height - 16),
                line_height=1.28,
            )
            if used <= inner.height - 12:
                break
            trial_size -= 2

        screen.set_clip(prev_clip)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    main()

