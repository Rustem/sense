// Chart rendering using Chart.js

let focusChart = null;
let interruptersChart = null;
let switchPatternsChart = null;
let switchesChart = null;

function renderFocusChart(data) {
  const canvas = document.getElementById('focus-chart');
  if (!canvas) return;

  // Destroy existing chart
  if (focusChart) {
    focusChart.destroy();
  }

  const ctx = canvas.getContext('2d');
  focusChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.app),
      datasets: [{
        label: 'Focus Time (minutes)',
        data: data.map(d => d.minutes),
        backgroundColor: '#3b82f6',
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: {
            display: false
          }
        },
        y: {
          grid: {
            display: false
          }
        }
      }
    }
  });
}

function renderInterruptionPatternsChart(data) {
  const canvas = document.getElementById('interrupters-chart');
  if (!canvas) return;

  // Destroy existing chart
  if (interruptersChart) {
    interruptersChart.destroy();
  }

  const ctx = canvas.getContext('2d');
  interruptersChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.pattern),
      datasets: [{
        label: 'Pattern Occurrences',
        data: data.map(d => d.count),
        backgroundColor: '#ef4444',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          },
          grid: {
            display: false
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  });
}

function renderSwitchPatternsChart(data) {
  const canvas = document.getElementById('switch-patterns-chart');
  if (!canvas) return;

  // Destroy existing chart
  if (switchPatternsChart) {
    switchPatternsChart.destroy();
  }

  const ctx = canvas.getContext('2d');
  switchPatternsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.pattern),
      datasets: [{
        label: 'Pattern Occurrences',
        data: data.map(d => d.count),
        backgroundColor: '#f97316',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          },
          grid: {
            display: false
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  });
}

function renderSwitchesChart(data) {
  const canvas = document.getElementById('switches-chart');
  if (!canvas) return;

  // Destroy existing chart
  if (switchesChart) {
    switchesChart.destroy();
  }

  const ctx = canvas.getContext('2d');
  switchesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.hour),
      datasets: [{
        label: 'Context Switches',
        data: data.map(d => d.count),
        borderColor: '#f97316',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 2
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  });
}
