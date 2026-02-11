/**
 * Main application logic for JIRA Allocation Analyzer web interface
 */

// Configuration
const ROWS_PER_PAGE = 100;

// State
let allIssueRows = [];
let noTimeRows = [];
let filteredRows = [];
let currentPage = 1;
let currentSort = { column: 'normalized_hours', direction: 'desc' };
let currentFilter = null;

// Epic grouping state
let epicGroups = [];
let selectedEpicIndices = new Set();
let jiraBaseUrl = '';
let groupIdCounter = 0;

/**
 * Initialize the issue table with data
 * @param {Array} data - Array of IssueRow objects (with time)
 * @param {Array} noTimeData - Array of IssueRow objects (without time)
 */
function initTable(data, noTimeData) {
    allIssueRows = data;
    noTimeRows = noTimeData || [];
    filteredRows = [...data];
    renderTable();
    setupSortHandlers();
}

/**
 * Toggle the issue table visibility
 */
function toggleIssueTable() {
    const issueView = document.getElementById('issue-view');
    const toggleBtn = document.getElementById('toggle-issues-btn');

    if (!issueView || !toggleBtn) return;

    if (issueView.style.display === 'none') {
        issueView.style.display = 'block';
        toggleBtn.textContent = 'Hide issue list';
    } else {
        issueView.style.display = 'none';
        toggleBtn.textContent = 'Show issue list';
    }
}

/**
 * Filter table by epic key
 * @param {string|null} epicKey - Epic key to filter by (null for "No Epic")
 * @param {string} epicName - Epic name for display
 */
function filterTableByEpic(epicKey, epicName) {
    currentFilter = epicKey;

    // Filter rows
    if (epicKey === null) {
        // "No Epic" case
        filteredRows = allIssueRows.filter(row => !row.epic_key);
    } else {
        filteredRows = allIssueRows.filter(row => row.epic_key === epicKey);
    }

    // Reset to first page
    currentPage = 1;

    // Update UI
    const filterIndicator = document.getElementById('filter-indicator');
    const filterEpicName = document.getElementById('filter-epic-name');
    const clearBtn = document.getElementById('clear-filter-btn');

    if (filterIndicator) filterIndicator.classList.add('active');
    if (filterEpicName) filterEpicName.textContent = epicName;
    if (clearBtn) clearBtn.style.display = 'inline-block';

    // Show issue table if hidden
    const issueView = document.getElementById('issue-view');
    const toggleBtn = document.getElementById('toggle-issues-btn');
    if (issueView) issueView.style.display = 'block';
    if (toggleBtn) toggleBtn.textContent = 'Hide issue list';

    // Re-render table
    renderTable();
}

/**
 * Clear the current filter
 */
function clearFilter() {
    currentFilter = null;
    filteredRows = [...allIssueRows];
    currentPage = 1;

    // Update UI
    const filterIndicator = document.getElementById('filter-indicator');
    const clearBtn = document.getElementById('clear-filter-btn');

    if (filterIndicator) filterIndicator.classList.remove('active');
    if (clearBtn) clearBtn.style.display = 'none';

    // Re-render table
    renderTable();
}

/**
 * Filter by summary category
 * @param {string} category - 'all', 'with_time', 'no_time', or 'unassigned'
 */
function filterByCategory(category) {
    currentPage = 1;

    const filterIndicator = document.getElementById('filter-indicator');
    const filterEpicName = document.getElementById('filter-epic-name');
    const clearBtn = document.getElementById('clear-filter-btn');

    let filterLabel = '';

    switch (category) {
        case 'all':
            // Show issue list (with time + no time)
            filteredRows = [...allIssueRows, ...noTimeRows];
            filterLabel = 'All Issues';
            break;
        case 'with_time':
            // Show issues with time
            filteredRows = [...allIssueRows];
            filterLabel = 'Issues with Time';
            break;
        case 'no_time':
            // Show issues without time
            filteredRows = [...noTimeRows];
            filterLabel = 'Issues without Time';
            break;
        case 'unassigned':
            // Filter to unassigned issues
            filteredRows = allIssueRows.filter(row => row.unassigned);
            filterLabel = 'Unassigned Issues';
            break;
        default:
            filteredRows = [...allIssueRows];
    }

    // Update UI
    if (filterIndicator) filterIndicator.classList.add('active');
    if (filterEpicName) filterEpicName.textContent = filterLabel;
    if (clearBtn) clearBtn.style.display = 'inline-block';

    // Show issue table
    const issueView = document.getElementById('issue-view');
    const toggleBtn = document.getElementById('toggle-issues-btn');
    if (issueView) issueView.style.display = 'block';
    if (toggleBtn) toggleBtn.textContent = 'Hide issue list';

    // Re-render table
    renderTable();
}

/**
 * Render the table with current filtered/sorted data
 */
function renderTable() {
    const tbody = document.getElementById('issue-table-body');
    if (!tbody) return;

    // Calculate total hours for percentage
    const totalHours = filteredRows.reduce((sum, row) => sum + (parseFloat(row.normalized_hours) || 0), 0);

    // Add percentage to each row
    const dataWithPercentage = filteredRows.map(row => ({
        ...row,
        percentage: totalHours > 0 ? ((parseFloat(row.normalized_hours) || 0) / totalHours * 100) : 0
    }));

    // Sort data
    const sortedData = sortData(dataWithPercentage, currentSort.column, currentSort.direction);

    // Paginate
    const start = (currentPage - 1) * ROWS_PER_PAGE;
    const end = start + ROWS_PER_PAGE;
    const pageData = sortedData.slice(start, end);

    // Render rows
    tbody.innerHTML = pageData.map(row => `
        <tr data-epic-key="${row.epic_key || ''}">
            <td><a href="${row.issue_url}" target="_blank">${row.issue_key}</a></td>
            <td class="truncate" title="${row.issue_title}">${row.issue_title}</td>
            <td>${row.issue_type}</td>
            <td>${row.epic_key || '—'}</td>
            <td class="text-right">${row.normalized_hours}</td>
            <td class="text-right">${row.percentage.toFixed(1)}%</td>
        </tr>
    `).join('');

    // Render pagination
    renderPagination(sortedData.length);
}

/**
 * Sort data by column
 * @param {Array} data - Data to sort
 * @param {string} column - Column name
 * @param {string} direction - 'asc' or 'desc'
 * @returns {Array} Sorted data
 */
function sortData(data, column, direction) {
    return [...data].sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle null/undefined
        if (aVal == null) aVal = '';
        if (bVal == null) bVal = '';

        // Numeric comparison for hours and percentage
        if (column === 'normalized_hours' || column === 'raw_hours' || column === 'percentage') {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
        } else {
            // String comparison
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();
        }

        if (aVal < bVal) return direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return direction === 'asc' ? 1 : -1;
        return 0;
    });
}

/**
 * Setup click handlers for sortable columns
 */
function setupSortHandlers() {
    document.querySelectorAll('.data-table th.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.dataset.column;

            // Toggle direction if same column
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'desc';  // Default to descending for new column
            }

            // Update UI
            document.querySelectorAll('.data-table th.sortable').forEach(header => {
                header.classList.remove('sorted-asc', 'sorted-desc');
            });
            this.classList.add(currentSort.direction === 'asc' ? 'sorted-asc' : 'sorted-desc');

            // Re-render
            renderTable();
        });
    });
}

/**
 * Render pagination controls
 * @param {number} totalItems - Total number of items
 */
function renderPagination(totalItems) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const totalPages = Math.ceil(totalItems / ROWS_PER_PAGE);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">Prev</button>`;

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += `<span>...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span>...</span>`;
        html += `<button onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">Next</button>`;

    pagination.innerHTML = html;
}

/**
 * Navigate to a specific page
 * @param {number} page - Page number
 */
function goToPage(page) {
    currentPage = page;
    renderTable();
}

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
function truncate(str, maxLength) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

/**
 * Save form state to sessionStorage
 */
function saveFormState() {
    const jql = document.getElementById('jql');
    const fromDate = document.getElementById('from_date');
    const toDate = document.getElementById('to_date');

    if (jql && fromDate && toDate) {
        sessionStorage.setItem('jira_analyzer_form', JSON.stringify({
            jql: jql.value,
            from_date: fromDate.value,
            to_date: toDate.value
        }));
    }
}

/**
 * Restore form state from sessionStorage
 */
function restoreFormState() {
    const saved = sessionStorage.getItem('jira_analyzer_form');
    if (!saved) return;

    try {
        const state = JSON.parse(saved);
        const jql = document.getElementById('jql');
        const fromDate = document.getElementById('from_date');
        const toDate = document.getElementById('to_date');

        // Only restore if fields are empty (don't override server values)
        if (jql && !jql.value && state.jql) {
            jql.value = state.jql;
        }
        if (fromDate && !fromDate.value && state.from_date) {
            fromDate.value = state.from_date;
        }
        if (toDate && !toDate.value && state.to_date) {
            toDate.value = state.to_date;
        }
    } catch (e) {
        console.error('Error restoring form state:', e);
    }
}

// ===== Epic Grouping =====

/**
 * Initialize the epic table with JS rendering
 * @param {string} jiraUrl - Base JIRA URL
 */
function initEpicTable(jiraUrl) {
    jiraBaseUrl = jiraUrl.replace(/\/+$/, '');
    renderEpicTable();
}

/**
 * Convert hex color to HSL
 */
function hexToHSL(hex) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;

    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
        h = s = 0;
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
            case g: h = ((b - r) / d + 2) / 6; break;
            case b: h = ((r - g) / d + 4) / 6; break;
        }
    }
    return { h: h * 360, s: s * 100, l: l * 100 };
}

/**
 * Convert HSL to hex color
 */
function hslToHex(h, s, l) {
    h /= 360; s /= 100; l /= 100;
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    const toHex = x => {
        const hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    return '#' + toHex(r) + toHex(g) + toHex(b);
}

/**
 * Generate color shades for grouped epics
 * @param {string} hexColor - Base hex color
 * @param {number} count - Number of shades needed
 * @returns {string[]} Array of hex color strings
 */
function generateColorShades(hexColor, count) {
    if (count === 1) return [hexColor];
    const hsl = hexToHSL(hexColor);
    const spread = 15;
    const minL = Math.max(20, hsl.l - spread);
    const maxL = Math.min(85, hsl.l + spread);
    const step = (maxL - minL) / (count - 1);
    const shades = [];
    for (let i = 0; i < count; i++) {
        shades.push(hslToHex(hsl.h, hsl.s, minL + step * i));
    }
    return shades;
}

/**
 * Get display color for an epic index (shade if grouped, original otherwise)
 */
function getDisplayColor(epicIndex) {
    for (const group of epicGroups) {
        const pos = group.members.indexOf(epicIndex);
        if (pos !== -1) {
            return group.shades[pos];
        }
    }
    return chartData.colors[epicIndex];
}

/**
 * Find which group an epic index belongs to
 */
function findGroupForEpic(epicIndex) {
    return epicGroups.find(g => g.members.includes(epicIndex)) || null;
}

/**
 * Build the rendering order for epic rows
 * Returns array of items: { type: 'epic', index } or { type: 'subtotal', group }
 */
function buildRenderOrder() {
    const rendered = new Set();
    const order = [];

    for (let i = 0; i < chartData.labels.length; i++) {
        if (rendered.has(i)) continue;

        const group = findGroupForEpic(i);
        if (group) {
            // Render all group members adjacent
            for (const memberIdx of group.members) {
                if (!rendered.has(memberIdx)) {
                    order.push({ type: 'epic', index: memberIdx });
                    rendered.add(memberIdx);
                }
            }
            // Subtotal row after group members
            order.push({ type: 'subtotal', group: group });
        } else {
            order.push({ type: 'epic', index: i });
            rendered.add(i);
        }
    }
    return order;
}

/**
 * Render the epic table from chartData (JS-rendered)
 */
function renderEpicTable() {
    const tbody = document.getElementById('epic-table-body');
    if (!tbody || !chartData) return;

    const order = buildRenderOrder();
    let html = '';

    for (const item of order) {
        if (item.type === 'epic') {
            const i = item.index;
            const color = getDisplayColor(i);
            const epicKey = chartData.epic_keys[i];
            const label = chartData.labels[i];
            const value = chartData.values[i];
            const pct = chartData.percentages[i];
            const checked = selectedEpicIndices.has(i) ? 'checked' : '';
            const inGroup = findGroupForEpic(i) !== null;

            const epicLink = epicKey
                ? `<a href="${jiraBaseUrl}/browse/${epicKey}" target="_blank">${epicKey}</a>`
                : '—';

            html += `<tr>
                <td style="width: 4px; padding: 0; background: ${color};"></td>
                <td>${epicLink}</td>
                <td class="clickable-cell truncate" onclick='filterTableByEpic(${JSON.stringify(epicKey)}, ${JSON.stringify(label)})' title="${label}">${label}</td>
                <td class="text-right">${value}</td>
                <td class="text-right">${pct}%</td>
                <td style="padding: 4px 8px; text-align: center;"><input type="checkbox" class="epic-checkbox" data-index="${i}" ${checked} ${inGroup ? 'disabled' : ''}></td>
            </tr>`;
        } else {
            // Subtotal row
            const group = item.group;
            const totalHours = group.members.reduce((sum, idx) => sum + parseFloat(chartData.values[idx] || 0), 0);
            const totalPct = group.members.reduce((sum, idx) => sum + parseFloat(chartData.percentages[idx] || 0), 0);
            const epicKeys = group.members.map(idx => chartData.epic_keys[idx]).filter(Boolean);

            html += `<tr class="group-subtotal-row">
                <td style="width: 4px; padding: 0;"></td>
                <td></td>
                <td class="clickable-cell" onclick='filterTableByGroup(${JSON.stringify(epicKeys)}, ${JSON.stringify(group.name)})'>${group.name}</td>
                <td class="text-right">${totalHours.toFixed(1)}</td>
                <td class="text-right">${totalPct.toFixed(1)}%</td>
                <td style="padding: 4px 8px; text-align: center;"><button class="btn-ungroup" onclick="ungroupById(${group.id})" title="Ungroup">✕</button></td>
            </tr>`;
        }
    }

    tbody.innerHTML = html;

    // Wire checkbox handlers
    tbody.querySelectorAll('.epic-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            const idx = parseInt(this.dataset.index);
            if (this.checked) {
                selectedEpicIndices.add(idx);
            } else {
                selectedEpicIndices.delete(idx);
            }
            updateToolbar();
        });
    });

    updateToolbar();
}

/**
 * Update the grouping toolbar visibility and content
 */
function updateToolbar() {
    const toolbar = document.getElementById('epic-group-toolbar');
    if (!toolbar) return;

    let html = '';
    if (selectedEpicIndices.size >= 2) {
        html += `<button class="btn-sm" onclick="groupSelectedEpics()">Group Selected (${selectedEpicIndices.size})</button>`;
    }
    if (epicGroups.length > 0) {
        html += `<button class="btn-sm" onclick="ungroupAll()">Ungroup All</button>`;
    }
    toolbar.innerHTML = html;
}

/**
 * Group the currently selected epics
 */
function groupSelectedEpics() {
    if (selectedEpicIndices.size < 2) return;

    const indices = Array.from(selectedEpicIndices).sort((a, b) => a - b);

    // Remove from any existing groups (dissolve empty groups)
    for (const idx of indices) {
        const existingGroup = findGroupForEpic(idx);
        if (existingGroup) {
            existingGroup.members = existingGroup.members.filter(m => m !== idx);
        }
    }
    epicGroups = epicGroups.filter(g => g.members.length > 0);

    // Prompt for group name
    const defaultName = 'Group ' + (++groupIdCounter);
    const name = prompt('Group name:', defaultName);
    if (name === null) return; // cancelled

    // Pick base color from first selected epic
    const baseColor = chartData.colors[indices[0]];
    const shades = generateColorShades(baseColor, indices.length);

    epicGroups.push({
        id: groupIdCounter,
        name: name || defaultName,
        members: indices,
        baseColor: baseColor,
        shades: shades
    });

    selectedEpicIndices.clear();
    renderEpicTable();
    if (typeof updateChartForGroups === 'function') {
        updateChartForGroups();
    }
}

/**
 * Ungroup a specific group by ID
 */
function ungroupById(id) {
    epicGroups = epicGroups.filter(g => g.id !== id);
    renderEpicTable();
    if (typeof updateChartForGroups === 'function') {
        updateChartForGroups();
    }
}

/**
 * Ungroup all groups
 */
function ungroupAll() {
    epicGroups = [];
    selectedEpicIndices.clear();
    renderEpicTable();
    if (typeof updateChartForGroups === 'function') {
        updateChartForGroups();
    }
}

/**
 * Filter issue table by multiple epic keys (for group subtotal click)
 * @param {string[]} epicKeys - Array of epic keys to filter by
 * @param {string} groupName - Group name for display
 */
function filterTableByGroup(epicKeys, groupName) {
    const keySet = new Set(epicKeys);
    filteredRows = allIssueRows.filter(row => keySet.has(row.epic_key));
    currentPage = 1;

    const filterIndicator = document.getElementById('filter-indicator');
    const filterEpicName = document.getElementById('filter-epic-name');
    const clearBtn = document.getElementById('clear-filter-btn');

    if (filterIndicator) filterIndicator.classList.add('active');
    if (filterEpicName) filterEpicName.textContent = groupName;
    if (clearBtn) clearBtn.style.display = 'inline-block';

    const issueView = document.getElementById('issue-view');
    const toggleBtn = document.getElementById('toggle-issues-btn');
    if (issueView) issueView.style.display = 'block';
    if (toggleBtn) toggleBtn.textContent = 'Hide issue list';

    renderTable();
}
