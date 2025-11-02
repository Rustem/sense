/**
 * Main dashboard controller
 *
 * Orchestrates data fetching, processing, and rendering
 */

let currentDate = getToday();
let allSwitches = [];

async function initDashboard() {
  setupDatePicker();
  setupSwitchesFilter();
  await loadDashboard(currentDate);
}

function setupDatePicker() {
  const datePicker = document.getElementById('date-picker');
  if (!datePicker) return;

  // Get activity dates from server-rendered data
  const activityDates = window.ACTIVITY_DATES || [];

  // Initialize Flatpickr
  flatpickr(datePicker, {
    dateFormat: 'Y-m-d',
    defaultDate: currentDate,
    maxDate: 'today',
    onChange: async (selectedDates, dateStr) => {
      if (dateStr) {
        currentDate = dateStr;
        await loadDashboard(currentDate);
      }
    },
    onDayCreate: (dObj, dStr, fp, dayElem) => {
      const dateStr = formatDate(dayElem.dateObj);

      // Highlight dates with activity
      if (activityDates.includes(dateStr)) {
        dayElem.classList.add('has-activity');
      }
    }
  });
}

/**
 * Load all dashboard data for a specific date
 * @param {string} date - Date in YYYY-MM-DD format
 */
async function loadDashboard(date) {
  try {
    showLoadingState();

    // Fetch all data in parallel
    const [timeline, focus, switches, interruptions] = await Promise.all([
      fetchTimeline(date),
      fetchFocusSessions(date),
      fetchContextSwitches(date),
      fetchInterruptions(date)
    ]);

    // Check if there's any activity for this date
    if (timeline.total_events === 0) {
      showNoActivityState(date);
      hideLoadingState();
      return;
    }

    // Process and aggregate data
    const dashboardData = processDashboardData({
      timeline,
      focus,
      switches,
      interruptions
    });

    // Show normal dashboard
    hideNoActivityState();

    // Render all sections
    renderMetrics(dashboardData.metrics);
    renderInsights(dashboardData.insights);
    renderFocusChart(dashboardData.focusByApp);
    renderInterruptionPatternsChart(dashboardData.topInterruptionPatterns);
    renderSwitchPatternsChart(dashboardData.topSwitchPatterns);
    renderSwitchesChart(dashboardData.hourlySwitches);
    renderTimeline(timeline.events, focus.apps, interruptions.interruptions, switches.switches);

    hideLoadingState();
  } catch (error) {
    showError(`Failed to load dashboard: ${error.message}`);
    hideLoadingState();
  }
}

function processDashboardData(data) {
  const { timeline, focus, switches, interruptions } = data;

  // Calculate metrics
  const activeTime = calculateTotalDuration(timeline.events);
  const focusSessionCount = focus.apps.reduce((sum, app) => sum + app.total_sessions, 0);
  const deepFocusCount = countDeepFocusSessions(focus.apps);

  const metrics = {
    activeTime,
    focusSessionCount,
    contextSwitchCount: switches.total_switches,
    interruptionCount: interruptions.total_interruptions,
    deepFocusCount
  };

  // Aggregate focus time by app (top 5)
  const focusByApp = focus.apps
    .sort((a, b) => b.total_time_minutes - a.total_time_minutes)
    .slice(0, 5)
    .map(app => ({
      app: shortenAppName(app.app_name),
      minutes: app.total_time_minutes
    }));

  // Top interruption patterns (A ↔ B)
  const topInterruptionPatterns = buildInterruptionPatterns(interruptions.interruptions)
    .slice(0, 5)
    .map(pattern => {
      const app1 = shortenAppName(pattern.app1);
      const app2 = shortenAppName(pattern.app2);
      return {
        pattern: `${app1} ↔ ${app2}`,
        count: pattern.count
      };
    });

  // Hourly context switches
  const hourlySwitches = aggregateSwitchesByHour(switches.switches);

  // Top context switch patterns (A → B)
  const topSwitchPatterns = buildSwitchPatterns(switches.switches)
    .slice(0, 5)
    .map(pattern => {
      const from = shortenAppName(pattern.from_app);
      const to = shortenAppName(pattern.to_app);
      return {
        pattern: `${from} → ${to}`,
        count: pattern.count
      };
    });

  // Hourly data for insights
  const hourlyData = buildHourlyData(timeline.events, focus.apps, interruptions.interruptions, switches.switches);

  // Generate insights
  const insights = generateInsights({
    metrics,
    hourlyData,
    interruptions: interruptions.interruptions,
    focusApps: focus.apps
  });

  return {
    metrics,
    insights,
    focusByApp,
    topInterruptionPatterns,
    topSwitchPatterns,
    hourlySwitches,
    timeline: timeline.events,
    hourlyData
  };
}

function buildInterruptionPatterns(interruptions) {
  if (!interruptions || interruptions.length === 0) {
    return [];
  }

  const patterns = {};
  interruptions.forEach(i => {
    // Normalize pattern: use alphabetical order so A↔B and B↔A are the same
    const apps = [i.interrupted_app, i.interrupting_app].sort();
    const key = `${apps[0]}↔${apps[1]}`;

    if (!patterns[key]) {
      patterns[key] = {
        app1: apps[0],
        app2: apps[1],
        count: 0
      };
    }
    patterns[key].count++;
  });

  return Object.values(patterns)
    .sort((a, b) => b.count - a.count);
}

function buildSwitchPatterns(switches) {
  if (!switches || switches.length === 0) {
    return [];
  }

  const patterns = {};
  switches.forEach(sw => {
    const key = `${sw.from_app}→${sw.to_app}`;
    if (!patterns[key]) {
      patterns[key] = {
        from_app: sw.from_app,
        to_app: sw.to_app,
        count: 0
      };
    }
    patterns[key].count++;
  });

  return Object.values(patterns)
    .sort((a, b) => b.count - a.count);
}

function countDeepFocusSessions(apps) {
  return apps.reduce((count, app) => {
    const deepSessions = app.focus_sessions.filter(s => s.duration_minutes > 25);
    return count + deepSessions.length;
  }, 0);
}

function aggregateSwitchesByHour(switches) {
  const hourlyCount = {};

  switches.forEach(sw => {
    const hour = new Date(sw.time).getHours();
    hourlyCount[hour] = (hourlyCount[hour] || 0) + 1;
  });

  // Create array for all 24 hours
  const result = [];
  for (let hour = 0; hour < 24; hour++) {
    result.push({
      hour: `${hour}:00`,
      count: hourlyCount[hour] || 0
    });
  }

  return result;
}

/**
 * Build hourly data combining events, focus, and interruptions
 * @param {Array<Object>} events - Timeline events
 * @param {Array<Object>} focusApps - Focus apps data
 * @param {Array<Object>} interruptions - Interruption events
 * @param {Array<Object>} switches - Context switches
 * @returns {Array<Object>} Hourly aggregated data
 */
function buildHourlyData(events, focusApps, interruptions, switches) {
  const hourlyData = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    focusSessions: 0,
    interruptions: 0,
    switches: 0
  }));

  // Count focus sessions by hour
  focusApps.forEach(app => {
    app.focus_sessions.forEach(session => {
      const hour = new Date(session.start).getHours();
      hourlyData[hour].focusSessions++;
    });
  });

  // Count interruptions by hour
  interruptions.forEach(interruption => {
    const hour = new Date(interruption.time).getHours();
    hourlyData[hour].interruptions++;
  });

  // Count switches by hour
  switches.forEach(sw => {
    const hour = new Date(sw.time).getHours();
    hourlyData[hour].switches++;
  });

  return hourlyData;
}

function renderMetrics(metrics) {
  setText('#active-time', formatDuration(metrics.activeTime));
  setText('#focus-sessions', metrics.focusSessionCount);
  setText('#context-switches', metrics.contextSwitchCount);
  setText('#interruptions', metrics.interruptionCount);
}

function renderInsights(insights) {
  const container = document.getElementById('insights-list');
  if (!container) return;

  container.innerHTML = insights
    .map((insight, idx) => {
      switch (insight.type) {
        case 'deep-focus':
          return renderDeepFocusInsight(insight, idx);
        case 'interruption-patterns':
          return renderInterruptionPatternsInsight(insight, idx);
        case 'peak-switching':
          return renderPeakSwitchingInsight(insight, idx);
        default:
          return `<li class="text-gray-700">• ${insight.message || ''}</li>`;
      }
    })
    .join('');

  // Add click handlers for expandable items
  setupInsightExpanders();
}

function renderDeepFocusInsight(insight, idx) {
  const sessionsHtml = insight.sessions.map(s => {
    const startTime = formatTime(s.start);
    const endTime = formatTime(s.end);
    const duration = Math.round(s.duration);
    const interruptions = s.interruptions > 0 ? `, ${s.interruptions} interruptions` : '';
    const appName = shortenAppName(s.app);

    return `<div class="text-sm">• ${startTime}-${endTime} - ${appName} (${duration} min${interruptions})</div>`;
  }).join('');

  return renderExpandableInsight(insight.title, sessionsHtml, idx);
}

function renderInterruptionPatternsInsight(insight, idx) {
  const patternsHtml = insight.patterns.map(p => {
    const interrupted = shortenAppName(p.interrupted);
    const interrupter = shortenAppName(p.interrupter);
    return `<div class="text-sm">• ${interrupted} → ${interrupter} (${p.count} times)</div>`;
  }).join('');

  return renderExpandableInsight(insight.title, patternsHtml, idx);
}

function renderPeakSwitchingInsight(insight, idx) {
  const hoursHtml = insight.hours.map(h => {
    return `<div class="text-sm">• ${h.hour} (${h.switches} switches)</div>`;
  }).join('');

  return renderExpandableInsight(insight.title, hoursHtml, idx);
}

function renderExpandableInsight(title, contentHtml, idx) {
  return `
    <li class="text-gray-700">
      <button class="insight-expander w-full text-left hover:text-gray-900 transition-colors flex items-center justify-between" data-target="insight-${idx}">
        <span>• ${title}</span>
        <svg class="w-4 h-4 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
      <div id="insight-${idx}" class="hidden mt-2 ml-4 p-3 bg-gray-50 rounded space-y-1">
        ${contentHtml}
      </div>
    </li>
  `;
}

function setupInsightExpanders() {
  document.querySelectorAll('.insight-expander').forEach(button => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-target');
      const target = document.getElementById(targetId);
      const svg = button.querySelector('svg');

      if (target) {
        target.classList.toggle('hidden');
        svg.classList.toggle('rotate-180');
      }
    });
  });
}

function renderTimeline(events, focusApps, interruptions, switches) {
  allSwitches = switches; // Store for filtering
  renderTimelineView(events, focusApps, interruptions);
  renderSwitchesView(switches, false); // Default: exclude web switches
  renderInterruptionsView(interruptions);
}

function setupSwitchesFilter() {
  const checkbox = document.querySelector('input[type="checkbox"][x-model="includeWebSwitches"]');
  if (checkbox) {
    checkbox.addEventListener('change', (e) => {
      renderSwitchesView(allSwitches, e.target.checked);
    });
  }
}

function renderTimelineView(events, focusApps, interruptions) {
  const container = document.getElementById('timelineVis');
  if (!container) return;

  container.innerHTML = '';

  if (events.length === 0) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400">No events for this date</div>';
    return;
  }

  // Calculate total time per app
  const appTotals = {};
  events.forEach(e => {
    appTotals[e.app_name] = (appTotals[e.app_name] || 0) + e.duration_seconds;
  });

  // Keep only top 15 apps by total time
  const topApps = Object.entries(appTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([app]) => app);

  // Create groups from top apps only
  const groups = new vis.DataSet(
    topApps.map(app => ({ id: app, content: shortenAppName(app) }))
  );

  // Collect all focus sessions for top apps (blue/green)
  const items = [];
  let itemId = 0;

  focusApps.forEach(app => {
    if (!topApps.includes(app.app_name)) return;

    app.focus_sessions.forEach(session => {
      const duration = Math.round(session.duration_minutes);
      const startTime = formatTime(new Date(session.start));
      const endTime = formatTime(new Date(session.end));
      const timeSpan = Math.round((new Date(session.end) - new Date(session.start)) / 60000);
      const shortName = shortenAppName(app.app_name);

      // Green for deep focus (>25 min), blue otherwise
      const className = duration >= 25 ? 'deep-focus' : '';

      // Build tooltip with active time vs time span
      const tooltip = duration === timeSpan
        ? `${shortName}\n${startTime} - ${endTime}\n${duration} min active`
        : `${shortName}\n${startTime} - ${endTime}\n${duration} min active (${timeSpan} min span)`;

      items.push({
        id: itemId++,
        group: app.app_name,
        content: '',
        start: session.start,
        end: session.end,
        title: tooltip,
        className
      });
    });
  });


  if (items.length === 0) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400">No focus sessions for this date</div>';
    return;
  }

  const itemsDataSet = new vis.DataSet(items);

  // Find active time range
  const times = items.map(i => new Date(i.start).getTime());
  const endTimes = items.map(i => new Date(i.end).getTime());
  const minTime = new Date(Math.min(...times));
  const maxTime = new Date(Math.max(...endTimes));

  const options = {
    height: '384px',
    start: minTime,
    end: maxTime,
    zoomable: true,
    moveable: true,
    stack: false,
    tooltip: {
      followMouse: true,
      overflowMethod: 'cap'
    },
    onMove: function(item, callback) {
      callback(null);
    }
  };

  new vis.Timeline(container, itemsDataSet, groups, options);
}

function isWebUrl(name) {
  // Check if it's a URL (contains . and doesn't start with com/org/net/etc)
  return name.includes('.') && !name.startsWith('com.') && !name.startsWith('org.') &&
         !name.startsWith('net.') && !name.startsWith('io.') && !name.match(/^[A-Z]/);
}

function renderSwitchesView(switches, includeWebSwitches = false) {
  const container = document.getElementById('switchesVis');
  if (!container) return;

  // Filter out web switches if checkbox is unchecked
  let filteredSwitches = switches;
  if (!includeWebSwitches) {
    filteredSwitches = switches.filter(sw => {
      return !isWebUrl(sw.from_app) || !isWebUrl(sw.to_app);
    });
  }

  if (filteredSwitches.length === 0) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400">No context switches for this date</div>';
    return;
  }

  // Render as a list
  const html = `
    <div class="overflow-y-auto h-full">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          ${filteredSwitches.slice(0, 100).map(sw => `
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formatTime(new Date(sw.time))}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${shortenAppName(sw.from_app)}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${shortenAppName(sw.to_app)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  container.innerHTML = html;
}

function renderInterruptionsView(interruptions) {
  const container = document.getElementById('interruptionsVis');
  if (!container) return;

  if (interruptions.length === 0) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400">No interruptions for this date</div>';
    return;
  }

  // Render as a list
  const html = `
    <div class="overflow-y-auto h-full">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pattern</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          ${interruptions.slice(0, 100).map(i => {
            const interrupted = shortenAppName(i.interrupted_app);
            const interrupter = shortenAppName(i.interrupting_app);
            return `
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formatTime(new Date(i.time))}</td>
              <td class="px-6 py-4 text-sm text-gray-700">${interrupted} → ${interrupter} → ${interrupted}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${Math.round(i.duration_seconds)}s</td>
            </tr>
          `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
  container.innerHTML = html;
}

function showLoadingState() {
  document.body.classList.add('loading');
}

function hideLoadingState() {
  document.body.classList.remove('loading');
}

function showNoActivityState(date) {
  // Reset metrics
  setText('#active-time', '-');
  setText('#focus-sessions', '0');
  setText('#context-switches', '0');
  setText('#interruptions', '0');

  // Show no activity message
  const container = document.getElementById('insights-list');
  if (container) {
    container.innerHTML = `
      <li class="text-gray-500 italic">
        No activity recorded for ${date}. This could mean:
        <ul class="ml-6 mt-2 space-y-1">
          <li>• Your Mac was not in use</li>
          <li>• The date is in the future</li>
          <li>• macOS Screen Time tracking was disabled</li>
        </ul>
      </li>
    `;
  }

  // Clear charts
  if (focusChart) focusChart.destroy();
  if (interruptersChart) interruptersChart.destroy();
  if (switchPatternsChart) switchPatternsChart.destroy();
  if (switchesChart) switchesChart.destroy();
}

function hideNoActivityState() {
  // Normal rendering will overwrite
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}
