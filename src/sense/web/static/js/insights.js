/**
 * Insights generation from dashboard metrics
 */

/**
 * Generate insights from dashboard data
 * @param {Object} data - Dashboard data object
 * @returns {Array<Object>} Array of insight objects with details
 */
function generateInsights(data) {
  const insights = [];
  const { metrics, hourlyData, interruptions, focusApps } = data;

  // Top 3 deep focus sessions (>25 min only)
  const deepSessions = findTopFocusSessions(focusApps, interruptions, 3, 25);
  if (deepSessions.length > 0) {
    const appNames = [...new Set(deepSessions.map(s => shortenAppName(s.app)))].join(', ');
    insights.push({
      type: 'deep-focus',
      title: `Top ${deepSessions.length} deep focus sessions: ${appNames}`,
      sessions: deepSessions
    });
  }

  // Top 3 worst interruption patterns (A → B → A)
  const interruptionPatterns = findTopInterruptionPatterns(interruptions, 3);
  if (interruptionPatterns.length > 0) {
    insights.push({
      type: 'interruption-patterns',
      title: `Top ${interruptionPatterns.length} worst interruption patterns`,
      patterns: interruptionPatterns
    });
  }

  // Top 2 peak context switching hours
  const peakHours = findTopSwitchingHours(hourlyData, 2);
  if (peakHours.length > 0) {
    insights.push({
      type: 'peak-switching',
      title: `Peak context switching hours`,
      hours: peakHours
    });
  }

  return insights;
}

/**
 * Find top N longest focus sessions with interruption counts
 * @param {Array<Object>} focusApps - Focus apps data from API
 * @param {Array<Object>} interruptions - All interruptions
 * @param {number} topN - Number of top sessions to return
 * @param {number} minDuration - Minimum duration in minutes (optional)
 * @returns {Array<Object>} Top focus sessions with details
 */
function findTopFocusSessions(focusApps, interruptions, topN = 3, minDuration = 0) {
  if (!focusApps || focusApps.length === 0) {
    return [];
  }

  // Collect all sessions across all apps
  const allSessions = [];
  focusApps.forEach(app => {
    app.focus_sessions.forEach(session => {
      if (session.duration_minutes >= minDuration) {
        allSessions.push({
          app: app.app_name,
          start: new Date(session.start),
          end: new Date(session.end),
          duration: session.duration_minutes
        });
      }
    });
  });

  // Sort by duration descending
  allSessions.sort((a, b) => b.duration - a.duration);

  // Take top N and count interruptions during each
  return allSessions.slice(0, topN).map(session => {
    const interruptionCount = countInterruptionsDuring(
      session.start,
      session.end,
      interruptions
    );

    return {
      app: session.app,
      start: session.start,
      end: session.end,
      duration: session.duration,
      interruptions: interruptionCount
    };
  });
}

/**
 * Count interruptions that occurred during a time period
 * @param {Date} start - Period start
 * @param {Date} end - Period end
 * @param {Array<Object>} interruptions - All interruptions
 * @returns {number} Count of interruptions in period
 */
function countInterruptionsDuring(start, end, interruptions) {
  if (!interruptions || interruptions.length === 0) {
    return 0;
  }

  return interruptions.filter(i => {
    const time = new Date(i.time);
    return time >= start && time <= end;
  }).length;
}

/**
 * Find top N worst interruption patterns (A → B → A)
 * @param {Array<Object>} interruptions - All interruptions
 * @param {number} topN - Number of patterns to return
 * @returns {Array<Object>} Top interruption patterns
 */
function findTopInterruptionPatterns(interruptions, topN = 3) {
  if (!interruptions || interruptions.length === 0) {
    return [];
  }

  // Count patterns: interrupted_app → interrupting_app
  const patterns = {};
  interruptions.forEach(i => {
    const key = `${i.interrupted_app} → ${i.interrupting_app}`;
    if (!patterns[key]) {
      patterns[key] = {
        interrupted: i.interrupted_app,
        interrupter: i.interrupting_app,
        count: 0
      };
    }
    patterns[key].count++;
  });

  // Sort by count and take top N
  return Object.values(patterns)
    .sort((a, b) => b.count - a.count)
    .slice(0, topN);
}

/**
 * Find top N hours with most context switches
 * @param {Array<Object>} hourlyData - Hourly aggregated data
 * @param {number} topN - Number of hours to return
 * @returns {Array<Object>} Top switching hours
 */
function findTopSwitchingHours(hourlyData, topN = 2) {
  if (!hourlyData || hourlyData.length === 0) {
    return [];
  }

  // Filter only hours with switches
  const activeHours = hourlyData.filter(h => (h.switches || 0) > 0);
  if (activeHours.length === 0) {
    return [];
  }

  // Sort by switches descending and take top N
  return activeHours
    .sort((a, b) => (b.switches || 0) - (a.switches || 0))
    .slice(0, topN)
    .map(h => ({
      hour: h.hour,
      switches: h.switches || 0
    }));
}
