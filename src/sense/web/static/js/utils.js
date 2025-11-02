// Utility functions for formatting and calculations

function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  if (hours === 0) {
    return `${mins}m`;
  }
  return `${hours}h ${mins}m`;
}

function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatTime(date) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function getToday() {
  return formatDate(new Date());
}

function calculateTotalDuration(events) {
  return events.reduce((sum, event) => sum + event.duration_seconds / 60, 0);
}

function showError(message) {
  // TODO: Better error UI
  console.error(message);
  alert(`Error: ${message}`);
}

function setText(selector, text) {
  const element = document.querySelector(selector);
  if (element) {
    element.textContent = text;
  }
}

function shortenAppName(bundleId) {
  const appNameMap = {
    'com.apple.Safari': 'Safari',
    'com.tinyspeck.slackmacgap': 'Slack',
    'com.jetbrains.intellij': 'IntelliJ',
    'com.apple.Terminal': 'Terminal',
    'com.microsoft.VSCode': 'VSCode',
    'com.apple.radar.gm': 'Radar',
    'com.apple.iCal': 'Calendar',
    'Cisco-Systems.Spark': 'Webex',
    'com.apple.iWork.Keynote': 'Keynote',
    'com.apple.finder': 'Finder',
    'com.apple.mail': 'Mail',
    'com.jetbrains.datagrip': 'DataGrip'
  };

  return appNameMap[bundleId] || bundleId;
}
