// Bulk Operations for Admin Interface
class BulkOperations {
    constructor() {
        this.selectedItems = new Set();
        this.init();
    }
    
    init() {
        this.addSelectAllCheckbox();
        this.addItemCheckboxes();
        this.addBulkActionButtons();
        this.updateBulkActionVisibility();
    }
    
    addSelectAllCheckbox() {
        const table = document.querySelector('.admin-regulations-table, .admin-updates-table');
        if (!table) return;
        
        const headerRow = table.querySelector('thead tr');
        if (headerRow) {
            const selectAllCell = document.createElement('th');
            selectAllCell.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="selectAll">
                    <label class="form-check-label" for="selectAll">
                        <span class="visually-hidden">Select All</span>
                    </label>
                </div>
            `;
            headerRow.insertBefore(selectAllCell, headerRow.firstChild);
            
            const selectAllCheckbox = selectAllCell.querySelector('#selectAll');
            selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
    }
    
    addItemCheckboxes() {
        const table = document.querySelector('.admin-regulations-table tbody, .admin-updates-table tbody');
        if (!table) return;
        
        const rows = table.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const itemId = row.dataset.itemId || index;
            const selectCell = document.createElement('td');
            selectCell.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input item-checkbox" type="checkbox" 
                           id="item-${itemId}" data-item-id="${itemId}">
                    <label class="form-check-label" for="item-${itemId}">
                        <span class="visually-hidden">Select Item</span>
                    </label>
                </div>
            `;
            row.insertBefore(selectCell, row.firstChild);
            
            const checkbox = selectCell.querySelector('.item-checkbox');
            checkbox.addEventListener('change', (e) => {
                this.toggleItemSelection(itemId, e.target.checked);
            });
        });
    }
    
    addBulkActionButtons() {
        const container = document.querySelector('.admin-content');
        if (!container) return;
        
        const bulkActionsDiv = document.createElement('div');
        bulkActionsDiv.className = 'bulk-actions mb-3';
        bulkActionsDiv.style.display = 'none';
        bulkActionsDiv.innerHTML = `
            <div class="card">
                <div class="card-body py-2">
                    <div class="d-flex align-items-center justify-content-between">
                        <span class="selected-count">0 items selected</span>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-outline-danger btn-sm" 
                                    onclick="bulkOperations.confirmBulkDelete()">
                                <i class="fas fa-trash"></i> Delete Selected
                            </button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" 
                                    onclick="bulkOperations.exportSelected()">
                                <i class="fas fa-download"></i> Export Selected
                            </button>
                            <button type="button" class="btn btn-outline-primary btn-sm" 
                                    onclick="bulkOperations.clearSelection()">
                                <i class="fas fa-times"></i> Clear Selection
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const table = document.querySelector('.admin-regulations-table, .admin-updates-table');
        if (table) {
            table.parentNode.insertBefore(bulkActionsDiv, table);
        }
    }
    
    toggleSelectAll(checked) {
        const itemCheckboxes = document.querySelectorAll('.item-checkbox');
        itemCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
            this.toggleItemSelection(checkbox.dataset.itemId, checked);
        });
    }
    
    toggleItemSelection(itemId, selected) {
        if (selected) {
            this.selectedItems.add(itemId);
        } else {
            this.selectedItems.delete(itemId);
        }
        
        this.updateBulkActionVisibility();
        this.updateSelectAllState();
    }
    
    updateBulkActionVisibility() {
        const bulkActions = document.querySelector('.bulk-actions');
        const selectedCount = document.querySelector('.selected-count');
        
        if (bulkActions && selectedCount) {
            if (this.selectedItems.size > 0) {
                bulkActions.style.display = 'block';
                selectedCount.textContent = `${this.selectedItems.size} item${this.selectedItems.size !== 1 ? 's' : ''} selected`;
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }
    
    updateSelectAllState() {
        const selectAllCheckbox = document.querySelector('#selectAll');
        const itemCheckboxes = document.querySelectorAll('.item-checkbox');
        
        if (selectAllCheckbox && itemCheckboxes.length > 0) {
            const checkedCount = document.querySelectorAll('.item-checkbox:checked').length;
            
            if (checkedCount === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (checkedCount === itemCheckboxes.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }
    }
    
    confirmBulkDelete() {
        if (this.selectedItems.size === 0) return;
        
        const modal = this.createConfirmationModal(
            'Confirm Bulk Delete',
            `Are you sure you want to delete ${this.selectedItems.size} selected item${this.selectedItems.size !== 1 ? 's' : ''}? This action cannot be undone.`,
            'Delete',
            'btn-danger',
            () => this.performBulkDelete()
        );
        
        modal.show();
    }
    
    performBulkDelete() {
        // Implement actual bulk delete logic here
        if (window.STR_DEBUG) console.log('Deleting items:', Array.from(this.selectedItems));
        
        // Example: Send AJAX request to bulk delete endpoint
        // fetch('/admin/bulk-delete', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ ids: Array.from(this.selectedItems) })
        // });
        
        // For now, just remove from UI
        this.selectedItems.forEach(itemId => {
            const row = document.querySelector(`tr[data-item-id="${itemId}"]`);
            if (row) row.remove();
        });
        
        this.clearSelection();
    }
    
    exportSelected() {
        if (this.selectedItems.size === 0) return;
        
        if (window.STR_DEBUG) console.log('Exporting items:', Array.from(this.selectedItems));
        // Implement export logic here
    }
    
    clearSelection() {
        this.selectedItems.clear();
        document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = false);
        document.querySelector('#selectAll').checked = false;
        this.updateBulkActionVisibility();
    }
    
    createConfirmationModal(title, message, actionText, actionClass, onConfirm) {
        const modalId = 'confirmationModal';
        let modal = document.getElementById(modalId);
        
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = modalId;
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn ${actionClass}" id="confirmAction">${actionText}</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        const confirmButton = modal.querySelector('#confirmAction');
        confirmButton.onclick = () => {
            onConfirm();
            bootstrap.Modal.getInstance(modal).hide();
        };
        
        return new bootstrap.Modal(modal);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.admin-regulations-table, .admin-updates-table')) {
        window.bulkOperations = new BulkOperations();
    }
}); 