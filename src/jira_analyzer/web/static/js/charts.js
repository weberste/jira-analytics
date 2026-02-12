/**
 * Chart.js configuration and initialization for JIRA Allocation Analyzer
 */

let epicChart = null;
let chartData = null;

/**
 * Initialize the epic allocation stacked bar chart
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

    const totalValue = data.values.reduce((sum, v) => sum + parseFloat(v || 0), 0);

    // Create one dataset per epic for stacked bar
    const datasets = data.labels.map((label, index) => ({
        label: label,
        data: [data.values[index]],
        backgroundColor: data.colors[index],
        borderWidth: 0,
        borderSkipped: false,
        categoryPercentage: 1.0,
        barPercentage: 1.0,
        _epicIndex: index,
    }));

    epicChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [''],  // Single bar
            datasets: datasets
        },
        options: {
            indexAxis: 'y',  // Horizontal bar
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: 0, autoPadding: false },
            scales: {
                x: {
                    stacked: true,
                    display: false,
                    min: 0,
                    max: totalValue,
                    afterFit: function(axis) { axis.height = 0; axis.paddingTop = 0; axis.paddingBottom = 0; }
                },
                y: {
                    stacked: true,
                    display: false,
                    afterFit: function(axis) { axis.width = 0; axis.paddingLeft = 0; axis.paddingRight = 0; }
                }
            },
            plugins: {
                legend: {
                    display: false  // We have our own table
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataset._epicIndex;
                            const label = data.labels[index];
                            const value = data.values[index];
                            const percentage = data.percentages[index];
                            return `${label}: ${value}h (${percentage}%)`;
                        }
                    }
                }
            },
            onHover: function(event, elements) {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            },
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const dataset = epicChart.data.datasets[elements[0].datasetIndex];
                    const index = dataset._epicIndex;
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

/**
 * Update chart datasets to reflect current epic grouping order and colors
 */
function updateChartForGroups() {
    if (!epicChart || !chartData) return;

    // Build datasets in the same order as the epic table
    const order = buildRenderOrder();
    const datasets = [];

    for (const item of order) {
        if (item.type === 'epic') {
            const i = item.index;
            datasets.push({
                label: chartData.labels[i],
                data: [chartData.values[i]],
                backgroundColor: getDisplayColor(i),
                borderWidth: 0,
                borderSkipped: false,
                categoryPercentage: 1.0,
                barPercentage: 1.0,
                _epicIndex: i,
            });
        }
        // subtotal rows don't appear in the chart
    }

    epicChart.data.datasets = datasets;
    epicChart.update();
}
