// Configuration page JavaScript

let currentConfig = {};

// Load current configuration when page loads
async function loadConfig() {
  try {
    const response = await fetch('/config');
    const config = await response.json();
    currentConfig = config;
    
    // Populate form fields
    document.getElementById('totalTime').value = config.total_seconds;
    document.getElementById('numEnds').value = config.num_ends;
    document.getElementById('logoUrl').value = config.logo_url || '';
    document.getElementById('messageText').value = config.message || '';
    
  } catch (error) {
    console.error('Error loading configuration:', error);
    showMessage('Error loading configuration', 'error');
  }
}

// Save configuration
async function saveConfig() {
  const form = document.getElementById('configForm');
  const formData = new FormData(form);
  
  const configData = {
    total_seconds: parseInt(formData.get('total_seconds')),
    num_ends: parseInt(formData.get('num_ends')),
    logo_url: formData.get('logo_url'),
    message: formData.get('message')
  };
  
  try {
    const response = await fetch('/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(configData)
    });
    
    const result = await response.json();
    
    if (result.ok) {
      showMessage('Configuration saved successfully!', 'success');
      currentConfig = configData;
    } else {
      showMessage(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    console.error('Error saving configuration:', error);
    showMessage('Error saving configuration', 'error');
  }
}

// Reset form to defaults
function resetForm() {
  document.getElementById('totalTime').value = 7200; // 2 hours default
  document.getElementById('numEnds').value = 8;
  document.getElementById('logoUrl').value = '';
  document.getElementById('messageText').value = 'Each end is 15 minutes alotted to complete a game in two hours. If you are playing too slowly then the timer will show an end that you haven\'t played yet. You should play faster to stay on pace.';
  
  // Save the reset configuration
  const configData = {
    total_seconds: 7200,
    num_ends: 8,
    logo_url: '',
    message: 'Each end is 15 minutes alotted to complete a game in two hours. If you are playing too slowly then the timer will show an end that you haven\'t played yet. You should play faster to stay on pace.'
  };
  
  // Send reset configuration to server
  fetch('/config', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(configData)
  }).then(response => response.json())
    .then(result => {
      if (result.ok) {
        showMessage('Configuration reset to defaults and saved', 'success');
      } else {
        showMessage(`Error resetting configuration: ${result.error}`, 'error');
      }
    })
    .catch(error => {
      console.error('Error resetting configuration:', error);
      showMessage('Error resetting configuration', 'error');
    });
}

// Show status message
function showMessage(message, type) {
  const statusDiv = document.getElementById('statusMessage');
  statusDiv.textContent = message;
  statusDiv.className = `status-message ${type}`;
  
  // Auto-hide success messages after 3 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 3000);
  }
}

// Format time input helper
function formatTimeInput(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
  loadConfig();
  
  // Handle form submission
  document.getElementById('configForm').addEventListener('submit', function(e) {
    e.preventDefault();
    saveConfig();
  });
  
  // Add time format helper to total time input
  const totalTimeInput = document.getElementById('totalTime');
  totalTimeInput.addEventListener('blur', function() {
    const seconds = parseInt(this.value);
    if (seconds && seconds > 0) {
      // Show formatted time as placeholder or helper text
      const formatted = formatTimeInput(seconds);
      console.log(`Formatted time: ${formatted}`);
    }
  });
});
