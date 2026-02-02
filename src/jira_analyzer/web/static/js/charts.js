/**
 * Chart.js configuration and initialization for JIRA Allocation Analyzer
 */

let epicChart = null;
let chartData = null;

/**
 * Initialize the epic allocation pie chart
 * @param {string} canvasId - ID of the canvas element
 * @param {Object} data - EpicChartData object with labels, values, colors, etc.
 */
function initEpicChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    chartData = data;

    // Destroy existing chart if present
    if (epicChart) {
        epicChart.destroy();
    }

    const ctx = canvas.getContext('2d');

    epicChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: data.colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false  // We have our own table
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const label = data.labels[index];
                            const value = data.values[index];
                            const percentage = data.percentages[index];
                            return `${label}: ${value}h (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const epicKey = data.epic_keys[index];
                    const epicName = data.labels[index];
                    filterTableByEpic(epicKey, epicName);
                }
            }
        }
    });
}

/**
 * Get the current chart data
 * @returns {Object} The chart data object
 */
function getChartData() {
    return chartData;
}
