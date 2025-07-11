/**
 * Comprehensive Filter Management System
 * Handles form state, URL synchronization, debouncing, and API calls
 */

class FilterManager {
    constructor(options = {}) {
        this.options = {
            debounceMs: 300,
            apiEndpoint: '/api/search/advanced',
            containerId: 'dataContainer',
            countId: 'resultCount',
            loadingId: 'loadingSpinner',
            noResultsId: 'noResults',
            ...options
        };
        
        this.state = {
            filters: {},
            isLoading: false,
            hasActiveFilters: false,
            lastResults: [],
            abortController: null
        };
        
        this.searchTimeout = null;
        this.init();
    }
    
    init() {
        this.loadFiltersFromURL();
        this.bindEvents();
        this.updateFilterStates();
    }
    
    /**
     * Load filters from URL query parameters
     */
    loadFiltersFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const filters = {};
        
        for (const [key, value] of urlParams.entries()) {
            if (value && value !== '') {
                if (key.endsWith('[]')) {
                    // Handle array parameters
                    const baseKey = key.slice(0, -2);
                    if (!filters[baseKey]) filters[baseKey] = [];
                    filters[baseKey].push(value);
                } else {
                    filters[key] = value;
                }
            }
        }
        
        this.state.filters = filters;
        this.state.hasActiveFilters = Object.keys(filters).length > 0;
    }
    
    /**
     * Bind event listeners to form elements
     */
    bindEvents() {
        // Search input with debouncing
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.debouncedSearch(e.target.value);
            });
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.applyFilters();
                }
            });
        }
        
        // Filter dropdowns
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                this.updateFilterFromElement(select);
            });
        });
        
        // Date inputs
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateFilterFromElement(input);
            });
        });
        
        // Clear button
        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearAllFilters();
            });
        }
        
        // Apply filters button (if exists)
        const applyBtn = document.getElementById('applyFiltersBtn');
        if (applyBtn) {
            applyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.applyFilters();
            });
        }
    }
    
    /**
     * Update filter state from form element
     */
    updateFilterFromElement(element) {
        const key = element.name || element.id;
        const value = element.value;
        
        if (value && value !== '') {
            this.state.filters[key] = value;
        } else {
            delete this.state.filters[key];
        }
        
        this.state.hasActiveFilters = Object.keys(this.state.filters).length > 0;
    }
    
    /**
     * Debounced search function
     */
    debouncedSearch(query) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            if (query && query.trim() !== '') {
                this.state.filters.search = query.trim();
            } else {
                delete this.state.filters.search;
            }
            this.state.hasActiveFilters = Object.keys(this.state.filters).length > 0;
            this.applyFilters();
        }, this.options.debounceMs);
    }
    
    /**
     * Apply current filters
     */
    async applyFilters() {
        try {
            this.showLoading();
            
            // Cancel any existing request
            if (this.state.abortController) {
                this.state.abortController.abort();
            }
            
            // Create new abort controller
            this.state.abortController = new AbortController();
            
            // Build query parameters
            const params = this.serializeFilters();
            
            // Update URL without page reload
            this.updateURL(params);
            
            // Make API request
            const response = await fetch(`${this.options.apiEndpoint}?${params}`, {
                signal: this.state.abortController.signal
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.state.lastResults = data.results || data.regulations || data.updates || [];
                this.updateResults(this.state.lastResults);
                this.updateResultCount(data.count || this.state.lastResults.length);
            } else {
                throw new Error(data.error || 'Search failed');
            }
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Filter error:', error);
                this.showError(error.message || 'Failed to apply filters');
            }
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Serialize filters to URL parameters
     */
    serializeFilters() {
        const params = new URLSearchParams();
        
        Object.entries(this.state.filters).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach(v => {
                    if (v && v !== '') {
                        params.append(`${key}[]`, v);
                    }
                });
            } else if (value && value !== '') {
                params.append(key, value);
            }
        });
        
        return params.toString();
    }
    
    /**
     * Update URL with current filters
     */
    updateURL(params) {
        const newURL = params ? `${window.location.pathname}?${params}` : window.location.pathname;
        window.history.replaceState({}, '', newURL);
    }
    
    /**
     * Clear all filters
     */
    clearAllFilters() {
        // Reset form elements
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';
        
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.value = '';
        });
        
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.value = '';
        });
        
        // Reset state
        this.state.filters = {};
        this.state.hasActiveFilters = false;
        
        // Update URL
        this.updateURL('');
        
        // Refetch data
        this.applyFilters();
        
        // Update UI states
        this.updateFilterStates();
    }
    
    /**
     * Update filter UI states (show/hide active indicators)
     */
    updateFilterStates() {
        // Update filter status indicator
        const filterStatus = document.getElementById('filterStatus');
        if (filterStatus) {
            filterStatus.style.display = this.state.hasActiveFilters ? 'inline' : 'none';
        }
        
        // Update form elements to show current values
        Object.entries(this.state.filters).forEach(([key, value]) => {
            const element = document.getElementById(key) || document.querySelector(`[name="${key}"]`);
            if (element) {
                element.value = Array.isArray(value) ? value[0] : value;
            }
        });
    }
    
    /**
     * Update results display
     */
    updateResults(results) {
        const container = document.getElementById(this.options.containerId);
        if (!container) return;
        
        // This method should be overridden by specific implementations
        // to handle their specific result rendering
        if (window.STR_DEBUG) {
            console.log('Results updated:', results);
        }
    }
    
    /**
     * Update result count display
     */
    updateResultCount(count) {
        const countElement = document.getElementById(this.options.countId);
        if (countElement) {
            countElement.textContent = count;
        }
        
        // Show/hide no results message
        const noResults = document.getElementById(this.options.noResultsId);
        const container = document.getElementById(this.options.containerId);
        
        if (count === 0) {
            if (noResults) noResults.style.display = 'block';
            if (container) container.style.display = 'none';
        } else {
            if (noResults) noResults.style.display = 'none';
            if (container) container.style.display = 'block';
        }
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        this.state.isLoading = true;
        const loadingElement = document.getElementById(this.options.loadingId);
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
        
        // Disable form elements during loading
        const formElements = document.querySelectorAll('input, select, button');
        formElements.forEach(element => {
            element.disabled = true;
        });
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        this.state.isLoading = false;
        const loadingElement = document.getElementById(this.options.loadingId);
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Re-enable form elements
        const formElements = document.querySelectorAll('input, select, button');
        formElements.forEach(element => {
            element.disabled = false;
        });
    }
    
    /**
     * Show error message
     */
    showError(message) {
        // Create or update error display
        let errorElement = document.getElementById('filterError');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'filterError';
            errorElement.className = 'alert alert-danger mt-3';
            errorElement.style.display = 'none';
            
            const container = document.querySelector('.filter-card') || document.body;
            container.appendChild(errorElement);
        }
        
        errorElement.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.style.display='none'"></button>
        `;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Get current filter state
     */
    getFilters() {
        return { ...this.state.filters };
    }
    
    /**
     * Set filters programmatically
     */
    setFilters(filters) {
        this.state.filters = { ...filters };
        this.state.hasActiveFilters = Object.keys(filters).length > 0;
        this.updateFilterStates();
    }
}

// Export for use in other files
window.FilterManager = FilterManager; 