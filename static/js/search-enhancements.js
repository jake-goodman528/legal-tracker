// Search Enhancements and Autocomplete
class SearchEnhancer {
    constructor() {
        this.searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        this.maxHistoryItems = 10;
        this.init();
    }
    
    init() {
        this.addSearchEnhancements();
        this.addKeyboardShortcuts();
        this.addSearchHistory();
    }
    
    addSearchEnhancements() {
        const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Search"]');
        
        searchInputs.forEach(input => {
            // Add search icon
            this.addSearchIcon(input);
            
            // Add clear button
            this.addClearButton(input);
            
            // Add search suggestions
            this.addSearchSuggestions(input);
            
            // Add search on enter
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch(input.value);
                }
            });
        });
    }
    
    addSearchIcon(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'search-input-wrapper position-relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-search search-icon position-absolute';
        icon.style.cssText = 'left: 12px; top: 50%; transform: translateY(-50%); color: #6c757d; pointer-events: none;';
        wrapper.appendChild(icon);
        
        input.style.paddingLeft = '40px';
    }
    
    addClearButton(input) {
        const wrapper = input.parentNode;
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-link search-clear position-absolute';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.style.cssText = 'right: 8px; top: 50%; transform: translateY(-50%); padding: 0; border: none; background: none; color: #6c757d; display: none;';
        
        clearBtn.addEventListener('click', () => {
            input.value = '';
            input.focus();
            clearBtn.style.display = 'none';
            this.performSearch('');
        });
        
        input.addEventListener('input', () => {
            clearBtn.style.display = input.value ? 'block' : 'none';
        });
        
        wrapper.appendChild(clearBtn);
    }
    
    addSearchSuggestions(input) {
        const suggestions = [
            'registration', 'licensing', 'tax', 'zoning', 'permits',
            'Tampa', 'Florida', 'Clearwater', 'St. Petersburg',
            'short-term rental', 'Airbnb', 'VRBO', 'compliance'
        ];
        
        const dropdown = document.createElement('div');
        dropdown.className = 'search-suggestions dropdown-menu';
        dropdown.style.cssText = 'position: absolute; top: 100%; left: 0; right: 0; z-index: 1000; display: none;';
        
        input.parentNode.appendChild(dropdown);
        
        input.addEventListener('input', () => {
            const value = input.value.toLowerCase();
            if (value.length < 2) {
                dropdown.style.display = 'none';
                return;
            }
            
            const matches = suggestions.filter(s => s.toLowerCase().includes(value));
            if (matches.length > 0) {
                dropdown.innerHTML = matches.map(match => 
                    `<a class="dropdown-item" href="#" data-suggestion="${match}">${match}</a>`
                ).join('');
                dropdown.style.display = 'block';
            } else {
                dropdown.style.display = 'none';
            }
        });
        
        dropdown.addEventListener('click', (e) => {
            if (e.target.classList.contains('dropdown-item')) {
                e.preventDefault();
                input.value = e.target.dataset.suggestion;
                dropdown.style.display = 'none';
                this.performSearch(input.value);
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    }
    
    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Focus search on '/' key
            if (e.key === '/' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"], input[placeholder*="Search"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Clear search on Escape
            if (e.key === 'Escape' && e.target.matches('input[type="search"], input[placeholder*="Search"]')) {
                e.target.value = '';
                e.target.blur();
                this.performSearch('');
            }
        });
    }
    
    addSearchHistory() {
        // Add search history dropdown
        const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Search"]');
        
        searchInputs.forEach(input => {
            input.addEventListener('focus', () => {
                if (this.searchHistory.length > 0 && !input.value) {
                    this.showSearchHistory(input);
                }
            });
        });
    }
    
    showSearchHistory(input) {
        const dropdown = input.parentNode.querySelector('.search-suggestions');
        if (dropdown && this.searchHistory.length > 0) {
            dropdown.innerHTML = [
                '<h6 class="dropdown-header">Recent Searches</h6>',
                ...this.searchHistory.map(term => 
                    `<a class="dropdown-item" href="#" data-suggestion="${term}">
                        <i class="fas fa-history me-2"></i>${term}
                    </a>`
                )
            ].join('');
            dropdown.style.display = 'block';
        }
    }
    
    performSearch(query) {
        if (query && query.length > 1) {
            // Add to search history
            this.addToHistory(query);
        }
        
        // Trigger your existing search logic here
        if (window.STR_DEBUG) console.log('Performing search for:', query);
        
        // Example: trigger form submission or AJAX call
        const form = document.querySelector('form[role="search"]');
        if (form) {
            form.submit();
        }
    }
    
    addToHistory(query) {
        // Remove if already exists
        this.searchHistory = this.searchHistory.filter(item => item !== query);
        
        // Add to beginning
        this.searchHistory.unshift(query);
        
        // Limit history size
        this.searchHistory = this.searchHistory.slice(0, this.maxHistoryItems);
        
        // Save to localStorage
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SearchEnhancer();
}); 