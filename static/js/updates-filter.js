/**
 * Updates-specific Filter Manager
 * Extends FilterManager with updates-specific functionality
 */

class UpdatesFilterManager extends FilterManager {
    constructor() {
        super({
            apiEndpoint: '/api/updates/search',
            containerId: 'updatesContainer',
            countId: 'resultCount',
            loadingId: 'loadingSpinner',
            noResultsId: 'noResults'
        });
    }
    
    /**
     * Override to handle updates-specific event binding
     */
    bindEvents() {
        super.bindEvents();
        
        // Status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.updateFilterFromElement(statusFilter);
            });
        }
        
        // Category filter
        const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => {
                this.updateFilterFromElement(categoryFilter);
            });
        }
        
        // Impact filter
        const impactFilter = document.getElementById('impactFilter');
        if (impactFilter) {
            impactFilter.addEventListener('change', () => {
                this.updateFilterFromElement(impactFilter);
            });
        }
        
        // Jurisdiction filter
        const jurisdictionFilter = document.getElementById('jurisdictionFilter');
        if (jurisdictionFilter) {
            jurisdictionFilter.addEventListener('change', () => {
                this.updateFilterFromElement(jurisdictionFilter);
            });
        }
        
        // Priority filter
        const priorityFilter = document.getElementById('priorityFilter');
        if (priorityFilter) {
            priorityFilter.addEventListener('change', () => {
                this.updateFilterFromElement(priorityFilter);
            });
        }
        
        // Decision status filter
        const decisionStatusFilter = document.getElementById('decisionStatusFilter');
        if (decisionStatusFilter) {
            decisionStatusFilter.addEventListener('change', () => {
                this.updateFilterFromElement(decisionStatusFilter);
            });
        }
        
        // Action required filter
        const actionRequiredFilter = document.getElementById('actionRequiredFilter');
        if (actionRequiredFilter) {
            actionRequiredFilter.addEventListener('change', () => {
                this.updateFilterFromElement(actionRequiredFilter);
            });
        }
        
        // Date filters
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        if (dateFromFilter) {
            dateFromFilter.addEventListener('change', () => {
                this.updateFilterFromElement(dateFromFilter);
            });
        }
        if (dateToFilter) {
            dateToFilter.addEventListener('change', () => {
                this.updateFilterFromElement(dateToFilter);
            });
        }
    }
    
    /**
     * Override to handle updates-specific result rendering
     */
    updateResults(updates) {
        const updatesTable = document.getElementById('updatesTable');
        if (updatesTable) {
            this.renderTableView(updates);
        }
    }
    
    /**
     * Render updates in table view
     */
    renderTableView(updates) {
        const tableBody = document.querySelector('#updatesTable tbody');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        updates.forEach(update => {
            const row = document.createElement('tr');
            row.className = 'update-row';
            row.dataset.updateId = update.id;
            
            const priorityClass = this.getPriorityClass(update.priority);
            const statusClass = this.getStatusClass(update.status);
            const impactClass = this.getImpactClass(update.impact_level);
            
            row.innerHTML = `
                <td>
                    <a href="/updates/${update.id}" class="update-title-link">
                        ${this.escapeHtml(update.title)}
                    </a>
                    ${update.action_required ? '<i class="fas fa-exclamation-triangle text-warning ms-2" title="Action Required"></i>' : ''}
                </td>
                <td>
                    <span class="badge ${statusClass}">${this.escapeHtml(update.status)}</span>
                </td>
                <td>
                    <span class="badge category-${this.getCategoryClass(update.category)}">${this.escapeHtml(update.category)}</span>
                </td>
                <td>
                    <span class="badge ${impactClass}">${this.escapeHtml(update.impact_level)}</span>
                </td>
                <td>${this.escapeHtml(update.jurisdiction_affected)}</td>
                <td>
                    <span class="badge ${priorityClass}">${this.getPriorityText(update.priority)}</span>
                </td>
                <td>${update.update_date ? new Date(update.update_date).toLocaleDateString() : 'N/A'}</td>
                <td>
                    ${update.deadline_date ? new Date(update.deadline_date).toLocaleDateString() : 'N/A'}
                </td>
                <td>
                    <a href="/updates/${update.id}" class="btn btn-sm btn-outline-primary">
                        View
                    </a>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    /**
     * Get priority CSS class
     */
    getPriorityClass(priority) {
        switch (priority) {
            case 1: return 'bg-danger';
            case 2: return 'bg-warning';
            case 3: return 'bg-info';
            default: return 'bg-secondary';
        }
    }
    
    /**
     * Get priority text
     */
    getPriorityText(priority) {
        switch (priority) {
            case 1: return 'High';
            case 2: return 'Medium';
            case 3: return 'Low';
            default: return 'Unknown';
        }
    }
    
    /**
     * Get status CSS class
     */
    getStatusClass(status) {
        switch (status) {
            case 'Recent': return 'bg-success';
            case 'Upcoming': return 'bg-primary';
            case 'Proposed': return 'bg-warning';
            default: return 'bg-secondary';
        }
    }
    
    /**
     * Get impact CSS class
     */
    getImpactClass(impact) {
        switch (impact) {
            case 'High': return 'bg-danger';
            case 'Medium': return 'bg-warning';
            case 'Low': return 'bg-info';
            default: return 'bg-secondary';
        }
    }
    
    /**
     * Get category CSS class
     */
    getCategoryClass(category) {
        if (!category) return 'general';
        return category.toLowerCase().replace(/\s+/g, '-');
    }
    
    /**
     * Override clear to handle updates-specific form elements
     */
    clearAllFilters() {
        // Reset all update-specific filters
        const filterIds = [
            'searchInput', 'statusFilter', 'categoryFilter', 'impactFilter',
            'jurisdictionFilter', 'priorityFilter', 'decisionStatusFilter',
            'actionRequiredFilter', 'dateFromFilter', 'dateToFilter'
        ];
        
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.value = '';
            }
        });
        
        // Call parent clear method
        super.clearAllFilters();
    }
    
    /**
     * Override init to apply filters immediately if present
     */
    init() {
        super.init();
        
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
    window.updatesFilter = new UpdatesFilterManager();
}); 