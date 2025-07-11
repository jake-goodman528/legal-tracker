/**
 * Regulations-specific Filter Manager
 * Extends FilterManager with regulations-specific functionality
 */

class RegulationsFilterManager extends FilterManager {
    constructor() {
        super({
            apiEndpoint: '/api/search/advanced',
            containerId: 'regulationsContainer',
            countId: 'resultCount',
            loadingId: 'loadingSpinner',
            noResultsId: 'noResults'
        });
    }
    
    /**
     * Override to handle regulations-specific event binding
     */
    bindEvents() {
        super.bindEvents();
        
        // Jurisdiction filter with location update
        const jurisdictionFilter = document.getElementById('jurisdictionFilter');
        if (jurisdictionFilter) {
            jurisdictionFilter.addEventListener('change', () => {
                this.updateFilterFromElement(jurisdictionFilter);
                this.updateLocationOptions();
            });
        }
        
        // Jurisdiction specific filter
        const jurisdictionSpecificFilter = document.getElementById('jurisdictionSpecificFilter');
        if (jurisdictionSpecificFilter) {
            jurisdictionSpecificFilter.addEventListener('change', () => {
                this.updateFilterFromElement(jurisdictionSpecificFilter);
            });
        }
        
        // Location filter
        const locationFilter = document.getElementById('locationFilter');
        if (locationFilter) {
            locationFilter.addEventListener('change', () => {
                this.updateFilterFromElement(locationFilter);
            });
        }
        
        // View switching
        const cardsBtn = document.getElementById('cardsViewBtn');
        const tableBtn = document.getElementById('tableViewBtn');
        if (cardsBtn) {
            cardsBtn.addEventListener('click', () => this.switchView('cards'));
        }
        if (tableBtn) {
            tableBtn.addEventListener('click', () => this.switchView('table'));
        }
    }
    
    /**
     * Update location options based on jurisdiction level
     */
    async updateLocationOptions() {
        const jurisdictionFilter = document.getElementById('jurisdictionFilter');
        const locationFilter = document.getElementById('locationFilter');
        
        if (!jurisdictionFilter || !locationFilter) return;
        
        const jurisdictionLevel = jurisdictionFilter.value;
        
        // Clear current options
        locationFilter.innerHTML = '<option value="">All Locations</option>';
        
        if (jurisdictionLevel) {
            try {
                const response = await fetch(`/api/locations/${jurisdictionLevel}`);
                const data = await response.json();
                
                if (data.success && data.locations) {
                    data.locations.forEach(location => {
                        const option = document.createElement('option');
                        option.value = location;
                        option.textContent = location;
                        locationFilter.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error fetching locations:', error);
            }
        }
    }
    
    /**
     * Override to handle regulations-specific result rendering
     */
    updateResults(regulations) {
        const cardsView = document.getElementById('cardsView');
        const tableView = document.getElementById('tableView');
        
        if (cardsView) {
            this.renderCardsView(regulations);
        }
        
        if (tableView) {
            this.renderTableView(regulations);
        }
    }
    
    /**
     * Render regulations in cards view
     */
    renderCardsView(regulations) {
        const cardsContainer = document.getElementById('cardsView');
        if (!cardsContainer) return;
        
        cardsContainer.innerHTML = '';
        
        regulations.forEach(regulation => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4 mb-4';
            card.dataset.regulationId = regulation.id;
            
            card.innerHTML = `
                <div class="card regulation-card h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <a href="/regulations/${regulation.id}" class="text-decoration-none">
                                ${this.escapeHtml(regulation.title)}
                            </a>
                        </h5>
                        <p class="card-text text-muted small">
                            <i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(regulation.location)}
                        </p>
                        <p class="card-text text-muted small">
                            <i class="fas fa-building"></i> ${this.escapeHtml(regulation.jurisdiction_level)}
                        </p>
                        <p class="card-text">${this.escapeHtml(regulation.overview || '').substring(0, 150)}...</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                Updated: ${regulation.last_updated ? new Date(regulation.last_updated).toLocaleDateString() : 'N/A'}
                            </small>
                            <a href="/regulations/${regulation.id}" class="btn btn-sm btn-outline-primary">
                                View Details
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            cardsContainer.appendChild(card);
        });
    }
    
    /**
     * Render regulations in table view
     */
    renderTableView(regulations) {
        const tableBody = document.querySelector('#regulationsTable tbody');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        regulations.forEach(regulation => {
            const row = document.createElement('tr');
            row.className = 'regulation-row';
            row.dataset.regulationId = regulation.id;
            
            row.innerHTML = `
                <td>
                    <a href="/regulations/${regulation.id}" class="fw-bold text-decoration-none">
                        ${this.escapeHtml(regulation.title)}
                    </a>
                </td>
                <td>${this.escapeHtml(regulation.jurisdiction_level)}</td>
                <td>${this.escapeHtml(regulation.location)}</td>
                <td>${regulation.last_updated ? new Date(regulation.last_updated).toLocaleDateString() : 'N/A'}</td>
                <td>
                    <a href="/regulations/${regulation.id}" class="btn btn-sm btn-outline-primary">
                        View
                    </a>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Switch between cards and table view
     */
    switchView(viewType) {
        const cardsView = document.getElementById('cardsView');
        const tableView = document.getElementById('tableView');
        const cardsBtn = document.getElementById('cardsViewBtn');
        const tableBtn = document.getElementById('tableViewBtn');
        
        if (viewType === 'cards') {
            if (cardsView) cardsView.style.display = 'block';
            if (tableView) tableView.style.display = 'none';
            if (cardsBtn) cardsBtn.classList.add('active');
            if (tableBtn) tableBtn.classList.remove('active');
        } else {
            if (cardsView) cardsView.style.display = 'none';
            if (tableView) tableView.style.display = 'block';
            if (tableBtn) tableBtn.classList.add('active');
            if (cardsBtn) cardsBtn.classList.remove('active');
        }
        
        // Save preference
        localStorage.setItem('regulationsViewType', viewType);
    }
    
    /**
     * Load saved view preference
     */
    loadSavedView() {
        const savedView = localStorage.getItem('regulationsViewType') || 'table';
        this.switchView(savedView);
    }
    
    /**
     * Override init to include view loading
     */
    init() {
        super.init();
        this.loadSavedView();
        
        // If we have filters from URL, apply them immediately
        if (this.state.hasActiveFilters) {
            this.applyFilters();
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.regulationsFilter = new RegulationsFilterManager();
}); 