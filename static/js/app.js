async function getStatus() {
  const r = await fetch('/status', { cache: 'no-store' });
  return r.json();
}

function ensureBoxes(n) {
  const row = document.getElementById('row');
  if (row.children.length !== n) {
    row.innerHTML = '';
    for (let i = 0; i < n; i++) {
      const box = document.createElement('div');
      box.className = 'box';
      const fill = document.createElement('div');
      fill.className = 'fill';
      const label = document.createElement('div');
      label.textContent = (i + 1);
      box.appendChild(fill);
      box.appendChild(label);
      row.appendChild(box);
    }
  }
}

function clockString(el) {
  const h = Math.floor(el / 3600);
  const m = Math.floor((el % 3600) / 60);
  const s = el % 60;
  return h > 0 
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function updatePointer(currentIdx) {
  const wrap = document.getElementById('rowWrap');
  const boxes = document.querySelectorAll('.box');
  const ptr = document.getElementById('pointer');
  if (!boxes[currentIdx]) return;
  const r = boxes[currentIdx].getBoundingClientRect();
  const w = wrap.getBoundingClientRect();
  const centerX = r.left + r.width / 2 - w.left;
  const topY = Math.max(0, r.top - w.top - 34);
  ptr.style.left = centerX + 'px';
  ptr.style.top = topY + 'px';
}

function updateView(s) {
  // logo (from /status)
  const logoHost = document.getElementById('logo');
  if (s.logo_url && !logoHost.dataset.set) {
    logoHost.innerHTML = `<img src="${s.logo_url}" alt="logo"/>`;
    logoHost.dataset.set = '1';
  }

  // timer
  const el = Math.min(s.elapsed_seconds, s.total_seconds);
  document.getElementById('timer').textContent = clockString(el) + (s.paused ? ' (paused)' : '');

  // boxes, fills
  ensureBoxes(s.num_ends);
  const frac = Math.max(0, Math.min(1, el / Math.max(1, s.total_seconds)));
  const endUnits = frac * s.num_ends;
  const full = Math.floor(endUnits);
  const partial = endUnits - full;
  const boxes = document.querySelectorAll('.box');
  boxes.forEach((b, i) => {
    const fill = b.querySelector('.fill');
    let pct = 0;
    if (i < full) pct = 100;
    else if (i === full) pct = Math.round(partial * 100);
    else pct = 0;
    fill.style.width = pct + '%';
  });

  // pointer over current end
  const currentIdx = Math.min(s.num_ends - 1, Math.max(0, full));
  updatePointer(currentIdx);

  // message
  document.getElementById('message').textContent = s.message || '';

  // Update mobile control button states
  updateMobileControls(s);
}

function updateMobileControls(s) {
  const pauseBtn = document.getElementById('pauseBtn');
  const resumeBtn = document.getElementById('resumeBtn');
  
  if (s.paused) {
    pauseBtn.style.display = 'none';
    resumeBtn.style.display = 'inline-block';
  } else {
    pauseBtn.style.display = 'inline-block';
    resumeBtn.style.display = 'none';
  }
}

// Mobile control functions
async function resetTimer() {
  try {
    const response = await fetch('/reset', { method: 'POST' });
    const result = await response.json();
    if (result.ok) {
      console.log('Timer reset successfully');
    } else {
      console.error('Failed to reset timer:', result.error);
    }
  } catch (error) {
    console.error('Error resetting timer:', error);
  }
}

async function togglePause() {
  try {
    const response = await fetch('/pause', { method: 'POST' });
    const result = await response.json();
    if (result.ok) {
      console.log('Timer paused successfully');
    } else {
      console.error('Failed to pause timer:', result.error);
    }
  } catch (error) {
    console.error('Error pausing timer:', error);
  }
}

async function resumeTimer() {
  try {
    const response = await fetch('/resume', { method: 'POST' });
    const result = await response.json();
    if (result.ok) {
      console.log('Timer resumed successfully');
    } else {
      console.error('Failed to resume timer:', result.error);
    }
  } catch (error) {
    console.error('Error resuming timer:', error);
  }
}

async function addTime() {
  try {
    const response = await fetch('/add_time', { method: 'POST' });
    const result = await response.json();
    if (result.ok) {
      console.log('Added 1 minute successfully');
    } else {
      console.error('Failed to add time:', result.error);
    }
  } catch (error) {
    console.error('Error adding time:', error);
  }
}

async function subtractTime() {
  try {
    const response = await fetch('/subtract_time', { method: 'POST' });
    const result = await response.json();
    if (result.ok) {
      console.log('Subtracted 1 minute successfully');
    } else {
      console.error('Failed to subtract time:', result.error);
    }
  } catch (error) {
    console.error('Error subtracting time:', error);
  }
}

async function tick() {
  try {
    const s = await getStatus();
    updateView(s);
  } catch (e) {
    console.error('Error fetching status:', e);
  }
  setTimeout(tick, 500);
}

// Initialize the app
window.addEventListener('resize', () => {
  getStatus().then(updateView).catch(() => {});
});

// Start the update loop
tick();
