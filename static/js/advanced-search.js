/**
 * Advanced Search and Filtering System
 * Handles real-time search, autocomplete, and saved searches
 */

class AdvancedSearch {
    constructor() {
        this.searchTimeout = null;
        this.currentResults = [];
        this.activeFilters = {};
        this.savedSearches = [];
        this.abortController = null; // Track current search request
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedSearches();
        this.initializeFilters();
        this.setupViewSwitching();
        this.loadUserPreferences();
    }

    bindEvents() {
        // Search input with debouncing
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.debouncedSearch(e.target.value);
            });
            
            searchInput.addEventListener('focus', () => {
                this.showSearchSuggestions();
            });
            
            searchInput.addEventListener('blur', () => {
                // Delay hiding to allow clicking on suggestions
                setTimeout(() => this.hideSearchSuggestions(), 200);
            });
        }

        // Clear button functionality
        const clearFiltersBtn = document.getElementById('clearFiltersBtn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearAllFilters();
            });
        }

        // Filter dropdowns - no need to bind events since we use the Apply Filters button

        // Table sorting
        document.addEventListener('click', (e) => {
            if (e.target.closest('.sortable')) {
                this.handleSort(e.target.closest('.sortable'));
            }
        });

        // View switching
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-view]')) {
                this.switchView(e.target.closest('[data-view]').dataset.view);
            }
        });

        // Advanced search modal
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                this.openAdvancedSearch();
            }
        });
    }

    debouncedSearch(query) {
        // Clear existing timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Set new timeout for debounced search
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    async performSearch(query = '') {
        try {
            // Cancel any existing search
            if (this.abortController) {
                this.abortController.abort();
            }
            
            // Show loading WITHOUT disabling input
            this.showLoading();
            
            // Get current filter values
            const filters = this.getCurrentFilters();
            filters.q = query;

            // If no filters are applied, use simple local filtering
            if (!query && Object.keys(filters).length === 1) {
                this.hideLoading();
                this.updateResults(this.getAllRegulations());
                return;
            }

            // Add timeout to search requests
            this.abortController = new AbortController();
            const timeoutId = setTimeout(() => this.abortController.abort(), 10000); // 10 second timeout
            
            try {
                // Perform API search with timeout
                const response = await fetch('/api/search/advanced?' + new URLSearchParams(filters), {
                    signal: this.abortController.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();

                if (data.success) {
                    // Support both 'regulations' and 'results' field names
                    const regulations = data.regulations || data.results || [];
                    this.currentResults = regulations;
                    this.updateResults(regulations);
                    this.updateResultCount(data.count || regulations.length, query);
                    this.highlightSearchTerms(query);
                } else {
                    throw new Error(data.error || 'Search failed');
                }
            } catch (apiError) {
                clearTimeout(timeoutId);
                
                if (apiError.name === 'AbortError') {
                    throw new Error('Search timed out. Please try again.');
                } else if (apiError.message.includes('Failed to fetch')) {
                    console.warn('API search failed, falling back to client-side filtering:', apiError);
                    // Fall back to client-side filtering
                    this.performClientSideSearch({ q: query });
                    return;
                } else {
                    throw apiError;
                }
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message || 'Search failed. Please try again.');
        } finally {
            // Always hide loading and ensure input stays enabled
            this.hideLoading();
        }
    }

    getCurrentFilters() {
        const filters = {};
        
        const location = document.getElementById('locationFilter')?.value;
        const category = document.getElementById('categoryFilter')?.value;
        const jurisdiction = document.getElementById('jurisdictionFilter')?.value;
        const compliance = document.getElementById('complianceFilter')?.value;
        
        if (location) filters.locations = [location];
        if (category) filters.categories = [category];
        if (jurisdiction) filters.jurisdictions = [jurisdiction];
        if (compliance) filters.compliance_levels = [compliance];
        
        return filters;
    }

    async showSearchSuggestions() {
        const searchInput = document.getElementById('searchInput');
        const suggestionsContainer = document.getElementById('searchSuggestions');
        
        if (!searchInput || !suggestionsContainer) return;
        
        const query = searchInput.value.trim();
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.renderSuggestions(data.suggestions);
                suggestionsContainer.style.display = 'block';
            } else {
                this.hideSearchSuggestions();
            }
        } catch (error) {
            console.error('Suggestions error:', error);
        }
    }

    renderSuggestions(suggestions) {
        const container = document.getElementById('searchSuggestions');
        if (!container) return;

        const grouped = suggestions.reduce((acc, suggestion) => {
            if (!acc[suggestion.category]) {
                acc[suggestion.category] = [];
            }
            acc[suggestion.category].push(suggestion);
            return acc;
        }, {});

        let html = '<div class="suggestions-list">';
        
        Object.entries(grouped).forEach(([category, items]) => {
            html += `<div class="suggestion-category">`;
            html += `<div class="suggestion-category-header">${category}</div>`;
            
            items.forEach(item => {
                html += `<div class="suggestion-item" onclick="selectSuggestion('${item.text.replace(/'/g, "\\'")}')">`;
                html += `<i class="fas fa-search me-2"></i>${item.text}`;
                html += `</div>`;
            });
            
            html += `</div>`;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    hideSearchSuggestions() {
        const container = document.getElementById('searchSuggestions');
        if (container) {
            container.style.display = 'none';
        }
    }

    updateResults(regulations) {
        this.updateTableView(regulations);
        this.updateCardsView(regulations);
        
        if (regulations.length === 0) {
            this.showNoResults();
        } else {
            this.hideNoResults();
        }
    }

    updateTableView(regulations) {
        const tbody = document.getElementById('regulationsTableBody');
        if (!tbody) return;

        if (regulations.length === 0) {
            tbody.innerHTML = '';
            return;
        }

        const html = regulations.map(reg => this.renderTableRow(reg)).join('');
        tbody.innerHTML = html;
    }

    updateCardsView(regulations) {
        const container = document.getElementById('regulationsCards');
        if (!container) return;

        if (regulations.length === 0) {
            container.innerHTML = '';
            return;
        }

        const html = regulations.map(reg => this.renderCard(reg)).join('');
        container.innerHTML = html;
    }

    renderTableRow(regulation) {
        const complianceBadge = this.getComplianceBadge(regulation.compliance_level);
        const categoryBadge = this.getCategoryBadge(regulation.category);
        const jurisdictionBadge = this.getJurisdictionBadge(regulation.jurisdiction_level);
        
        return `
            <tr class="regulation-row" data-regulation-id="${regulation.id}">
                <td>${jurisdictionBadge}</td>
                <td class="location-cell">${regulation.location}</td>
                <td class="title-cell">
                    <a href="/regulations/${regulation.id}" class="regulation-title-link text-decoration-none">
                        ${regulation.title}
                    </a>
                </td>
                <td>${categoryBadge}</td>
                <td>${complianceBadge}</td>
                <td class="date-cell">${this.formatDate(regulation.last_updated)}</td>
                <td>
                    <a href="/regulations/${regulation.id}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-eye"></i> View
                    </a>
                </td>
            </tr>
        `;
    }

    renderCard(regulation) {
        const categoryBadge = this.getCategoryBadge(regulation.category);
        const jurisdictionBadge = this.getJurisdictionBadge(regulation.jurisdiction_level);
        
        return `
            <div class="col-lg-6 col-xl-4 mb-4 regulation-card" data-regulation-id="${regulation.id}">
                <div class="card h-100 shadow-sm regulation-card-item">
                    <div class="card-header bg-light d-flex justify-content-between align-items-center">
                        ${jurisdictionBadge}
                        ${categoryBadge}
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">
                            <a href="/regulations/${regulation.id}" class="text-decoration-none">
                                ${regulation.title}
                            </a>
                        </h6>
                        <p class="card-text text-muted small">
                            <i class="fas fa-map-marker-alt"></i> ${regulation.location}
                        </p>
                        <p class="card-text">
                            ${this.truncateText(regulation.key_requirements, 150)}
                        </p>
                    </div>
                    <div class="card-footer bg-transparent">
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">${this.formatDate(regulation.last_updated)}</small>
                            <a href="/regulations/${regulation.id}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-eye"></i> View
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getComplianceBadge(level) {
        const badges = {
            'Mandatory': '<span class="badge bg-danger"><i class="fas fa-exclamation-triangle"></i> Mandatory</span>',
            'Recommended': '<span class="badge bg-warning"><i class="fas fa-info-circle"></i> Recommended</span>',
            'Optional': '<span class="badge bg-secondary"><i class="fas fa-minus-circle"></i> Optional</span>'
        };
        return badges[level] || badges['Optional'];
    }

    getCategoryBadge(category) {
        const className = `category-${category.toLowerCase().replace(' ', '-')}`;
        return `<span class="badge category-badge ${className}">${category}</span>`;
    }

    getJurisdictionBadge(jurisdiction) {
        const className = `jurisdiction-${jurisdiction.toLowerCase()}`;
        return `<span class="jurisdiction-badge ${className}">${jurisdiction}</span>`;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().split('T')[0];
    }

    truncateText(text, length) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    updateResultCount(count, query) {
        const countElement = document.getElementById('resultCount');
        const contextElement = document.getElementById('searchContext');
        
        if (countElement) {
            countElement.textContent = count;
        }
        
        if (contextElement) {
            if (query) {
                contextElement.textContent = `for "${query}"`;
            } else {
                contextElement.textContent = '';
            }
        }
    }

    highlightSearchTerms(query) {
        if (!query) return;
        
        const terms = query.split(' ').filter(term => term.length > 2);
        if (terms.length === 0) return;

        const elements = document.querySelectorAll('.regulation-title-link, .location-cell, .requirements-preview');
        
        elements.forEach(element => {
            let html = element.innerHTML;
            
            terms.forEach(term => {
                const regex = new RegExp(`(${term})`, 'gi');
                html = html.replace(regex, '<mark>$1</mark>');
            });
            
            element.innerHTML = html;
        });
    }

    showLoading() {
        const loading = document.getElementById('searchLoading');
        const container = document.getElementById('regulationsContainer');
        
        if (loading) loading.style.display = 'block';
        if (container) container.style.opacity = '0.5';
    }

    hideLoading() {
        const loading = document.getElementById('searchLoading');
        const container = document.getElementById('regulationsContainer');
        
        if (loading) loading.style.display = 'none';
        if (container) container.style.opacity = '1';
    }

    forceHideAllLoading() {
        // Force hide all possible loading states
        const loadingElements = document.querySelectorAll('.loading-spinner, .spinner-border');
        loadingElements.forEach(el => {
            const loadingParent = el.closest('.loading-spinner');
            if (loadingParent) {
                loadingParent.remove();
            }
        });
        
        // Ensure main container is visible and has proper content
        const container = document.getElementById('regulationsContainer');
        if (container && container.innerHTML.includes('loading-spinner')) {
            // Container was replaced with loading spinner, restore proper structure
            const tableView = container.querySelector('#tableView');
            if (!tableView) {
                container.innerHTML = `
                    <div class="table-view" id="tableView">
                        <div class="table-responsive">
                            <table class="table table-hover regulations-table" id="regulationsTable">
                                <thead class="table-light">
                                    <tr>
                                        <th class="sortable" data-sort="jurisdiction_level">
                                            <i class="fas fa-layer-group"></i> Level
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th class="sortable" data-sort="location">
                                            <i class="fas fa-map-marker-alt"></i> Location
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th class="sortable" data-sort="title">
                                            <i class="fas fa-gavel"></i> Regulation
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th class="sortable" data-sort="category">
                                            <i class="fas fa-tags"></i> Category
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th class="sortable" data-sort="compliance_level">
                                            <i class="fas fa-exclamation-triangle"></i> Priority
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th class="sortable" data-sort="last_updated">
                                            <i class="fas fa-calendar-alt"></i> Updated
                                            <i class="fas fa-sort sort-icon"></i>
                                        </th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="regulationsTableBody">
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
        }
        
        // Reset container styles
        if (container) {
            container.style.opacity = '1';
            container.style.display = 'block';
        }
    }

    showNoResults() {
        const noResults = document.getElementById('noResults');
        const container = document.getElementById('regulationsContainer');
        
        if (noResults) noResults.style.display = 'block';
        if (container) container.style.display = 'none';
    }

    hideNoResults() {
        const noResults = document.getElementById('noResults');
        const container = document.getElementById('regulationsContainer');
        
        if (noResults) noResults.style.display = 'none';
        if (container) container.style.display = 'block';
    }

    showError(message) {
        this.hideLoading();
        
        // Show error in results area
        const resultsContainer = document.querySelector('.regulations-results, .table-responsive, #regulationsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger text-center" role="alert">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Search Error:</strong> ${message}
                    <div class="mt-2">
                        <button class="btn btn-outline-danger btn-sm" onclick="location.reload()">
                            <i class="fas fa-refresh"></i> Refresh Page
                        </button>
                    </div>
                </div>
            `;
        }
        
        // Also log to console for debugging
        console.error('AdvancedSearch Error:', message);
    }

    applyFilters() {
        const query = document.getElementById('searchInput')?.value || '';
        this.performSearch(query);
        this.updateFilterSummary();
    }

    updateFilterSummary() {
        const filters = this.getCurrentFilters();
        const summaryContainer = document.getElementById('filterSummary');
        const activeFiltersContainer = document.getElementById('activeFilters');
        
        if (!summaryContainer || !activeFiltersContainer) return;
        
        let hasFilters = false;
        let html = '';
        
        Object.entries(filters).forEach(([key, values]) => {
            if (Array.isArray(values) && values.length > 0) {
                hasFilters = true;
                values.forEach(value => {
                    html += `<span class="badge bg-primary me-1">${key}: ${value}</span>`;
                });
            }
        });
        
        if (hasFilters) {
            activeFiltersContainer.innerHTML = html;
            summaryContainer.style.display = 'block';
        } else {
            summaryContainer.style.display = 'none';
        }
    }

    clearAllFilters() {
        // Clear search input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Clear filter dropdowns
        ['locationFilter', 'categoryFilter', 'jurisdictionFilter', 'complianceFilter'].forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.value = '';
            }
        });
        
        // Clear date filters
        const dateFrom = document.getElementById('dateFrom');
        const dateTo = document.getElementById('dateTo');
        const dateRange = document.getElementById('dateRange');
        if (dateFrom) dateFrom.value = '';
        if (dateTo) dateTo.value = '';
        if (dateRange) dateRange.value = '';
        
        // Reset all state variables
        this.currentResults = [];
        this.activeFilters = {};
        
        // Cancel any pending search requests
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        
        // Clear any search timeouts
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }
        
        // Hide all loading spinners and restore container
        this.hideLoading();
        this.forceHideAllLoading();
        
        // Hide no results message
        this.hideNoResults();
        
        // Clear search suggestions
        this.hideSearchSuggestions();
        
        // Load all regulations and update display
        this.loadAllRegulations();
        
        // Update filter summary
        this.updateFilterSummary();
        
        // Update URL to remove search parameters
        if (window.history && window.history.pushState) {
            window.history.pushState({}, '', window.location.pathname);
        }
        
        // Close modal if open
        const modal = bootstrap.Modal.getInstance(document.getElementById('advancedSearchModal'));
        if (modal) modal.hide();
    }

    loadAllRegulations() {
        try {
            // Use stored original data if available, otherwise extract from table
            let allRegulations;
            if (window.originalRegulationsData && window.originalRegulationsData.length > 0) {
                allRegulations = window.originalRegulationsData;
            } else {
                // Fallback to extracting from table (for pages without stored data)
                allRegulations = this.getAllRegulations();
            }
            
            // Update results and display
            this.currentResults = allRegulations;
            this.updateResults(allRegulations);
            this.updateResultCount(allRegulations.length, '');
            
            // Remove any highlighting
            this.removeHighlighting();
            
        } catch (error) {
            console.error('Error loading all regulations:', error);
            this.showError('Failed to reload regulations. Please refresh the page.');
        }
    }

    removeHighlighting() {
        // Remove any search term highlighting
        const highlightedElements = document.querySelectorAll('mark');
        highlightedElements.forEach(element => {
            const parent = element.parentNode;
            parent.replaceChild(document.createTextNode(element.textContent), element);
            parent.normalize();
        });
    }

    switchView(viewType) {
        const tableView = document.getElementById('tableView');
        const cardsView = document.getElementById('cardsView');
        const buttons = document.querySelectorAll('[data-view]');
        
        // Update button states
        buttons.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-view="${viewType}"]`)?.classList.add('active');
        
        // Switch views
        if (viewType === 'table') {
            if (tableView) tableView.style.display = 'block';
            if (cardsView) cardsView.style.display = 'none';
        } else if (viewType === 'cards') {
            if (tableView) tableView.style.display = 'none';
            if (cardsView) cardsView.style.display = 'block';
        }
        
        // Save preference
        localStorage.setItem('preferredView', viewType);
    }

    setupViewSwitching() {
        // Restore preferred view
        const preferredView = localStorage.getItem('preferredView');
        if (preferredView) {
            this.switchView(preferredView);
        }
    }

    handleSort(header) {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const sortKey = header.dataset.sort;
        const isAscending = header.classList.contains('sort-asc');
        
        // Remove existing sort classes
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            const icon = th.querySelector('.sort-icon');
            if (icon) {
                icon.className = 'fas fa-sort sort-icon';
            }
        });
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = this.getSortValue(a, sortKey);
            const bValue = this.getSortValue(b, sortKey);
            
            if (!isNaN(Date.parse(aValue)) && !isNaN(Date.parse(bValue))) {
                return isAscending ? new Date(aValue) - new Date(bValue) : new Date(bValue) - new Date(aValue);
            } else {
                return isAscending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
            }
        });
        
        // Update header classes
        header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
        const icon = header.querySelector('.sort-icon');
        if (icon) {
            icon.className = `fas fa-sort-${isAscending ? 'down' : 'up'} sort-icon text-primary`;
        }
        
        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    }

    getSortValue(row, sortKey) {
        const cellIndex = {
            'jurisdiction_level': 0,
            'location': 1,
            'title': 2,
            'category': 3,
            'compliance_level': 4,
            'last_updated': 5
        }[sortKey];
        
        if (cellIndex !== undefined) {
            return row.cells[cellIndex].textContent.trim();
        }
        
        return '';
    }

    getAllRegulations() {
        // Use stored original data if available and table is empty
        const rows = document.querySelectorAll('.regulation-row');
        if (rows.length === 0 && window.originalRegulationsData && window.originalRegulationsData.length > 0) {
            return window.originalRegulationsData;
        }
        
        // Get all regulations from the current table rows
        return Array.from(rows).map(row => {
            // Extract text content from badges and links
            const jurisdictionBadge = row.cells[0].querySelector('.jurisdiction-badge');
            const categoryBadge = row.cells[3].querySelector('.category-badge');
            const complianceBadge = row.cells[4].querySelector('.badge');
            const titleLink = row.cells[2].querySelector('a');
            
            return {
                id: row.dataset.regulationId,
                jurisdiction_level: jurisdictionBadge ? jurisdictionBadge.textContent.trim() : row.cells[0].textContent.trim(),
                location: row.cells[1].textContent.trim(),
                title: titleLink ? titleLink.textContent.trim() : row.cells[2].textContent.trim(),
                category: categoryBadge ? categoryBadge.textContent.trim() : row.cells[3].textContent.trim(),
                compliance_level: complianceBadge ? complianceBadge.textContent.trim().replace(/^\s*\S+\s*/, '') : row.cells[4].textContent.trim(),
                last_updated: row.cells[5].textContent.trim(),
                key_requirements: row.dataset.requirements || ''
            };
        });
    }

    async loadSavedSearches() {
        try {
            const response = await fetch('/api/search/saved');
            const data = await response.json();
            this.savedSearches = data.saved_searches || [];
        } catch (error) {
            console.error('Failed to load saved searches:', error);
        }
    }

    async applySavedSearch(searchId) {
        try {
            const response = await fetch(`/api/search/saved/${searchId}/use`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.applySavedSearchCriteria(data.criteria);
            }
        } catch (error) {
            console.error('Failed to apply saved search:', error);
        }
    }

    applySavedSearchCriteria(criteria) {
        // Clear existing filters
        this.clearAllFilters();
        
        // Apply criteria
        if (criteria.location) {
            const locationFilter = document.getElementById('locationFilter');
            if (locationFilter) locationFilter.value = criteria.location;
        }
        
        if (criteria.category) {
            const categoryFilter = document.getElementById('categoryFilter');
            if (categoryFilter) categoryFilter.value = criteria.category;
        }
        
        if (criteria.compliance_level) {
            // This would be handled in advanced search modal
        }
        
        // Perform search
        this.applyFilters();
    }

    initializeFilters() {
        // Initialize any default filters or preferences
        this.updateFilterSummary();
    }

    loadUserPreferences() {
        // Load any user preferences from localStorage
    }

    // Advanced Search Modal Methods
    openAdvancedSearch() {
        const modal = new bootstrap.Modal(document.getElementById('advancedSearchModal'));
        modal.show();
        
        // Populate current search query
        const currentQuery = document.getElementById('searchInput')?.value || '';
        const advancedQuery = document.getElementById('advancedSearchQuery');
        if (advancedQuery) {
            advancedQuery.value = currentQuery;
        }
    }

    executeAdvancedSearch() {
        const form = document.getElementById('advancedSearchForm');
        if (!form) return;
        
        // Get current search query
        const searchQuery = document.getElementById('searchInput')?.value || '';
        
        // Get filter values from the modal
        const locationFilter = document.getElementById('locationFilter')?.value || '';
        const jurisdictionFilter = document.getElementById('jurisdictionFilter')?.value || '';
        const categoryFilter = document.getElementById('categoryFilter')?.value || '';
        const complianceFilter = document.getElementById('complianceFilter')?.value || '';
        const dateFrom = document.getElementById('dateFrom')?.value || '';
        const dateTo = document.getElementById('dateTo')?.value || '';
        const dateRange = document.getElementById('dateRange')?.value || '';
        
        // Build criteria object
        const criteria = {
            q: searchQuery,
            locations: locationFilter ? [locationFilter] : [],
            jurisdictions: jurisdictionFilter ? [jurisdictionFilter] : [],
            categories: categoryFilter ? [categoryFilter] : [],
            compliance_levels: complianceFilter ? [complianceFilter] : [],
            date_from: dateFrom,
            date_to: dateTo,
            date_range_days: dateRange
        };
        
        this.performAdvancedSearch(criteria);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('advancedSearchModal'));
        if (modal) modal.hide();
    }

    async performAdvancedSearch(criteria) {
        try {
            this.showLoading();
            
            const params = new URLSearchParams();
            
            // Add parameters
            Object.entries(criteria).forEach(([key, value]) => {
                if (Array.isArray(value) && value.length > 0) {
                    value.forEach(v => {
                        if (v) params.append(key + '[]', v);
                    });
                } else if (value && !Array.isArray(value)) {
                    params.append(key, value);
                }
            });
            
            try {
                const response = await fetch('/api/search/advanced?' + params.toString());
                const data = await response.json();
                
                if (data.success) {
                    // Support both 'regulations' and 'results' field names
                    const regulations = data.regulations || data.results || [];
                    this.currentResults = regulations;
                    this.updateResults(regulations);
                    this.updateResultCount(data.count, criteria.q);
                    this.highlightSearchTerms(criteria.q);
                    
                    // Update simple search input
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        searchInput.value = criteria.q;
                    }
                } else {
                    throw new Error(data.error || 'Search failed');
                }
            } catch (apiError) {
                console.warn('API search failed, falling back to client-side filtering:', apiError);
                // Fall back to client-side filtering
                this.performClientSideSearch(criteria);
            }
            
        } catch (error) {
            console.error('Advanced search error:', error);
            this.showError('Advanced search failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    


    performClientSideSearch(criteria) {
        // Get all regulations from the page
        let regulations = this.getAllRegulations();
        
        // Apply filters
        if (criteria.locations && criteria.locations.length > 0) {
            regulations = regulations.filter(reg => 
                criteria.locations.some(loc => reg.location.toLowerCase().includes(loc.toLowerCase()))
            );
        }
        
        if (criteria.jurisdictions && criteria.jurisdictions.length > 0) {
            regulations = regulations.filter(reg => 
                criteria.jurisdictions.some(jur => reg.jurisdiction_level.toLowerCase() === jur.toLowerCase())
            );
        }
        
        if (criteria.categories && criteria.categories.length > 0) {
            regulations = regulations.filter(reg => 
                criteria.categories.some(cat => reg.category.toLowerCase().includes(cat.toLowerCase()))
            );
        }
        
        if (criteria.compliance_levels && criteria.compliance_levels.length > 0) {
            regulations = regulations.filter(reg => 
                criteria.compliance_levels.some(comp => reg.compliance_level.toLowerCase() === comp.toLowerCase())
            );
        }
        
        // Apply search query
        if (criteria.q) {
            const query = criteria.q.toLowerCase();
            regulations = regulations.filter(reg => 
                reg.title.toLowerCase().includes(query) ||
                reg.location.toLowerCase().includes(query) ||
                reg.key_requirements.toLowerCase().includes(query)
            );
        }
        
        // Update results
        this.currentResults = regulations;
        this.updateResults(regulations);
        this.updateResultCount(regulations.length, criteria.q);
        this.highlightSearchTerms(criteria.q);
    }

    async saveAdvancedSearch() {
        const form = document.getElementById('advancedSearchForm');
        const searchName = document.getElementById('searchName')?.value;
        const searchDescription = document.getElementById('searchDescription')?.value;
        
        if (!form || !searchName) {
            alert('Please enter a name for your search.');
            return;
        }
        
        const formData = new FormData(form);
        const criteria = {
            q: formData.get('advancedSearchQuery') || '',
            categories: formData.getAll('categories'),
            compliance_levels: formData.getAll('compliance_levels'),
            property_types: formData.getAll('property_types'),
            jurisdictions: formData.getAll('jurisdictions'),
            date_from: formData.get('date_from'),
            date_to: formData.get('date_to'),
            date_range_days: formData.get('date_range_days')
        };
        
        try {
            const response = await fetch('/api/search/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: searchName,
                    description: searchDescription,
                    criteria: criteria,
                    is_public: true
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show success modal
                const successModal = new bootstrap.Modal(document.getElementById('saveSearchModal'));
                successModal.show();
                
                // Clear the form
                document.getElementById('searchName').value = '';
                document.getElementById('searchDescription').value = '';
                
                // Reload saved searches
                this.loadSavedSearches();
            } else {
                alert(data.error || 'Failed to save search.');
            }
            
        } catch (error) {
            console.error('Save search error:', error);
            alert('Failed to save search. Please try again.');
        }
    }


}

// Global functions for template event handlers
function selectSuggestion(text) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = text;
        if (window.advancedSearch && typeof window.advancedSearch.debouncedSearch === 'function') {
            window.advancedSearch.debouncedSearch(text);
        }
    }
}

function applySavedSearch(searchId) {
    if (window.advancedSearch && typeof window.advancedSearch.applySavedSearch === 'function') {
        window.advancedSearch.applySavedSearch(searchId);
    }
}

function clearAllFilters() {
    // Clear the search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Clear filter dropdowns
    ['locationFilter', 'categoryFilter', 'jurisdictionFilter', 'complianceFilter'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.value = '';
        }
    });
    
    // Clear date filters
    ['dateFrom', 'dateTo', 'dateRange'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.value = '';
        }
    });
    
    // Try to use advanced search if available
    if (window.advancedSearch && typeof window.advancedSearch.clearAllFilters === 'function') {
        window.advancedSearch.clearAllFilters();
    } else {
        // Fallback: Try to restore original data without reloading
        try {
            // Hide any loading indicators
            const loadingElement = document.getElementById('searchLoading');
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            
            // Force remove any LoadingManager loading spinners
            const loadingSpinners = document.querySelectorAll('.loading-spinner, .spinner-border');
            loadingSpinners.forEach(spinner => {
                const parent = spinner.closest('.loading-spinner');
                if (parent) parent.remove();
            });
            
            // Hide no results message
            const noResults = document.getElementById('noResults');
            if (noResults) {
                noResults.style.display = 'none';
            }
            
            // Show the main content
            const mainContainer = document.getElementById('regulationsContainer') || 
                                 document.getElementById('tableView');
            if (mainContainer) {
                mainContainer.style.display = 'block';
            }
            
            // Try to restore original data if available
            if (window.originalRegulationsData && window.originalRegulationsData.length > 0) {
                const tbody = document.getElementById('regulationsTableBody');
                if (tbody) {
                    // Recreate table rows from stored data
                    const html = window.originalRegulationsData.map(reg => {
                        const complianceBadge = reg.compliance_level === 'Mandatory' 
                            ? `<span class="badge bg-danger"><i class="fas fa-exclamation-triangle"></i> Mandatory</span>`
                            : reg.compliance_level === 'Recommended'
                            ? `<span class="badge bg-warning"><i class="fas fa-info-circle"></i> Recommended</span>`
                            : `<span class="badge bg-secondary"><i class="fas fa-minus-circle"></i> Optional</span>`;
                        
                        return `
                            <tr class="regulation-row" data-regulation-id="${reg.id}">
                                <td>
                                    <span class="jurisdiction-badge jurisdiction-${reg.jurisdiction_level.toLowerCase()}">
                                        ${reg.jurisdiction_level}
                                    </span>
                                </td>
                                <td class="location-cell">${reg.location}</td>
                                <td class="title-cell">
                                    <a href="/regulations/${reg.id}" class="regulation-title-link text-decoration-none">
                                        ${reg.title}
                                    </a>
                                </td>
                                <td>
                                    <span class="badge category-badge category-${reg.category.toLowerCase().replace(' ', '-')}">
                                        ${reg.category}
                                    </span>
                                </td>
                                <td>${complianceBadge}</td>
                                <td class="date-cell">${reg.last_updated}</td>
                                <td>
                                    <a href="/regulations/${reg.id}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-eye"></i> View
                                    </a>
                                </td>
                            </tr>
                        `;
                    }).join('');
                    
                    tbody.innerHTML = html;
                    
                    // Update result count
                    const resultCount = document.getElementById('resultCount');
                    if (resultCount) {
                        resultCount.textContent = window.originalRegulationsData.length;
                    }
                }
            } else {
                // If no stored data, reload page as last resort
                window.location.href = window.location.pathname;
            }
            
            // Update URL to remove search parameters
            if (window.history && window.history.pushState) {
                window.history.pushState({}, '', window.location.pathname);
            }
            
        } catch (error) {
            console.error('Error in fallback clear function:', error);
            // Ultimate fallback - just reload the page
            window.location.reload();
        }
    }
}

function openAdvancedSearch() {
    if (window.advancedSearch) {
        window.advancedSearch.openAdvancedSearch();
    } else {
        // Fallback if advanced search is not initialized
        const modal = document.getElementById('advancedSearchModal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }
}

function executeAdvancedSearch() {
    if (window.advancedSearch) {
        window.advancedSearch.executeAdvancedSearch();
    }
}

function saveAdvancedSearch() {
    if (window.advancedSearch) {
        window.advancedSearch.saveAdvancedSearch();
    }
}



// Quick filter functions for template buttons
function filterByJurisdiction(level) {
    if (window.advancedSearch) {
        const filter = document.getElementById('jurisdictionFilter');
        if (filter) {
            filter.value = level;
            window.advancedSearch.performSearch(document.getElementById('searchInput')?.value || '');
        }
    }
}

function filterByCompliance(level) {
    if (window.advancedSearch) {
        const filter = document.getElementById('complianceFilter');
        if (filter) {
            filter.value = level;
            window.advancedSearch.performSearch(document.getElementById('searchInput')?.value || '');
        }
    }
}

function filterByCategory(category) {
    if (window.advancedSearch) {
        const filter = document.getElementById('categoryFilter');
        if (filter) {
            filter.value = category;
            window.advancedSearch.performSearch(document.getElementById('searchInput')?.value || '');
        }
    }
}

function clearAdvancedFilters() {
    if (window.advancedSearch) {
        window.advancedSearch.clearAllFilters();
    }
    // Also clear the advanced search form
    const form = document.getElementById('advancedSearchForm');
    if (form) {
        form.reset();
    }
}

// Prevent automatic initialization - will be initialized by specific pages that need it
// This prevents conflicts when multiple pages include this script 