/**
 * Main application logic for JIRA Allocation Analyzer web interface
 */

// Configuration
const ROWS_PER_PAGE = 100;

// State
let allIssueRows = [];
let filteredRows = [];
let currentPage = 1;
let currentSort = { column: 'normalized_hours', direction: 'desc' };
let currentFilter = null;

/**
 * Initialize the issue table with data
 * @param {Array} data - Array of IssueRow objects
 */
function initTable(data) {
    allIssueRows = data;
    filteredRows = [...data];
    renderTable();
    setupSortHandlers();
}

/**
 * Switch between Epic View and Issue View
 * @param {string} view - 'epic' or 'issue'
 */
function switchView(view) {
    // Update tab buttons
    document.querySelectorAll('.view-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update view content
    document.querySelectorAll('.view-content').forEach(content => {
        content.classList.remove('active');
    });

    const viewElement = document.getElementById(view + '-view');
    if (viewElement) {
        viewElement.classList.add('active');
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

    // Switch to issue view to show filtered results
    switchViewTo('issue');

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
 * Switch to a specific view programmatically
 * @param {string} view - 'epic' or 'issue'
 */
function switchViewTo(view) {
    // Update tab buttons
    document.querySelectorAll('.view-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.textContent.toLowerCase().includes(view)) {
            tab.classList.add('active');
        }
    });

    // Update view content
    document.querySelectorAll('.view-content').forEach(content => {
        content.classList.remove('active');
    });

    const viewElement = document.getElementById(view + '-view');
    if (viewElement) {
        viewElement.classList.add('active');
    }
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
            <td>${truncate(row.issue_title, 50)}</td>
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
