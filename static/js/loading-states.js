// Loading States for Search and Filter Operations
class LoadingManager {
    static showLoading(elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="loading-spinner enhanced text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${message}</span>
                    </div>
                    <p class="mt-2 text-muted">${message}</p>
                </div>
            `;
        }
    }
    
    static hideLoading(elementId, originalContent) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = originalContent;
        }
    }
    
    static addSearchLoadingState() {
        const searchInput = document.querySelector('input[placeholder*="Search"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                // Try to find the appropriate results container
                const resultsContainer = document.getElementById('regulationsContainer') || 
                                       document.getElementById('updatesContainer') ||
                                       document.getElementById('results-container');
                
                searchTimeout = setTimeout(() => {
                    if (this.value.length > 2 && resultsContainer) {
                        const containerId = resultsContainer.id;
                        LoadingManager.showLoading(containerId, 'Searching...');
                        // Simulate search delay (remove in production)
                        setTimeout(() => {
                            // Your existing search logic here
                            if (window.STR_DEBUG) console.log('Search completed for:', this.value);
                        }, 500);
                    }
                }, 300);
            });
        }
    }
    
    static addFilterLoadingState() {
        // Exclude clear button since it has its own loading management
        const filterButtons = document.querySelectorAll('[data-filter], .btn-filter, button[onclick*="Filter"]:not(#clearFiltersBtn)');
        const resultsContainer = document.getElementById('regulationsContainer') || 
                               document.getElementById('updatesContainer') ||
                               document.getElementById('results-container');
        
        if (resultsContainer) {
            filterButtons.forEach(button => {
                // Skip clear button to avoid conflicts with AdvancedSearch clear handling
                if (button.id === 'clearFiltersBtn') return;
                
                button.addEventListener('click', function() {
                    LoadingManager.showLoading(resultsContainer.id, 'Applying filters...');
                    // Your existing filter logic here
                    setTimeout(() => {
                        if (window.STR_DEBUG) console.log('Filter applied');
                    }, 300);
                });
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    LoadingManager.addSearchLoadingState();
    LoadingManager.addFilterLoadingState();
}); 