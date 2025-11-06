// API client - handles HTTP requests to backend

const API_BASE = '/api';

async function fetchTimeline(date) {
  const url = `${API_BASE}/timeline?start_date=${date}&end_date=${date}&limit=1000&include_system=false`;
  return fetchJson(url);
}

async function fetchFocusSessions(date) {
  const url = `${API_BASE}/focus?start_date=${date}&end_date=${date}&limit=1000`;
  return fetchJson(url);
}

async function fetchContextSwitches(date) {
  const url = `${API_BASE}/switches?start_date=${date}&end_date=${date}&limit=1000`;
  return fetchJson(url);
}

async function fetchInterruptions(date) {
  const url = `${API_BASE}/interruptions?start_date=${date}&end_date=${date}&max_interruption_seconds=60&limit=1000`;
  return fetchJson(url);
}

async function fetchTimelineRange(startDate, endDate) {
  const url = `${API_BASE}/timeline?start_date=${startDate}&end_date=${endDate}&limit=10000&include_system=false`;
  return fetchJson(url);
}

/**
 * Generic JSON fetch with error handling
 * @param {string} url - URL to fetch
 * @returns {Promise<Object>} Parsed JSON response
 * @throws {Error} If request fails
 */
async function fetchJson(url) {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}
