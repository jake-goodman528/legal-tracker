// Main JavaScript for STR Compliance Toolkit

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });

    // Enhanced search functionality
    initializeSearch();
    
    // Form validation enhancements
    initializeFormValidation();
    
    // Table enhancements
    initializeTableFeatures();
    
    // Keyboard shortcuts
    initializeKeyboardShortcuts();
});

// Show/hide regulation details
function showRegulationDetails(regulationId) {
    const detailsRow = document.getElementById(`details-${regulationId}`);
    const isVisible = !detailsRow.classList.contains('d-none');
    
    // Hide all other details
    document.querySelectorAll('.regulation-details').forEach(function(row) {
        row.classList.add('d-none');
    });
    
    // Toggle current details
    if (!isVisible) {
        detailsRow.classList.remove('d-none');
        detailsRow.classList.add('fade-in');
    }
}

// Enhanced search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let debounceTimer;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                // Auto-submit search after 500ms of no typing
                if (searchInput.value.length >= 3 || searchInput.value.length === 0) {
                    // Ensure form values are properly captured before submit
                    const form = searchInput.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }, 500);
        });
    }
    
    // Add change listeners to dropdown filters for immediate filtering
    const jurisdictionSelect = document.getElementById('jurisdiction');
    const locationSelect = document.getElementById('location');
    
    // Make submitFilter function globally available
    window.submitFilter = function() {
        const jurisdiction = document.getElementById('jurisdiction').value;
        const location = document.getElementById('location').value;
        const search = document.getElementById('search').value;
        
        // Build the URL with parameters
        let url = '/regulations?';
        const params = [];
        
        if (jurisdiction) {
            params.push('jurisdiction=' + encodeURIComponent(jurisdiction));
        }
        if (location) {
            params.push('location=' + encodeURIComponent(location));
        }
        if (search) {
            params.push('search=' + encodeURIComponent(search));
        }
        
        url += params.join('&');
        window.location.href = url;
    };
    
    if (jurisdictionSelect) {
        jurisdictionSelect.addEventListener('change', function() {
            // Auto-filter when jurisdiction changes
            submitFilter();
        });
    }
    
    if (locationSelect) {
        locationSelect.addEventListener('change', function() {
            // Auto-filter when location changes
            submitFilter();
        });
    }
}

// Form validation enhancements
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation for text areas
        const textareas = form.querySelectorAll('textarea');
        textareas.forEach(function(textarea) {
            textarea.addEventListener('input', function() {
                updateCharacterCount(textarea);
            });
            updateCharacterCount(textarea);
        });
    });
}

// Update character count for textareas
function updateCharacterCount(textarea) {
    const maxLength = textarea.getAttribute('maxlength');
    if (maxLength) {
        const currentLength = textarea.value.length;
        const countElement = textarea.parentNode.querySelector('.character-count');
        
        if (!countElement) {
            const counter = document.createElement('small');
            counter.className = 'character-count text-muted';
            textarea.parentNode.appendChild(counter);
        }
        
        const counter = textarea.parentNode.querySelector('.character-count');
        counter.textContent = `${currentLength}/${maxLength} characters`;
        
        if (currentLength > maxLength * 0.9) {
            counter.classList.add('text-warning');
        } else {
            counter.classList.remove('text-warning');
        }
    }
}

// Table enhancements
function initializeTableFeatures() {
    // Add loading states to form submissions
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = button.closest('form');
            if (form && form.checkValidity()) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(function() {
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
                }, 5000);
            }
        });
        
        // Store original text
        button.setAttribute('data-original-text', button.innerHTML);
    });
    
    // Sort table columns
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(header);
        });
    });
}

// Sort table functionality
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentNode.querySelectorAll('th').forEach(function(th) {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Sort rows
    rows.sort(function(a, b) {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        const result = aValue.localeCompare(bValue, undefined, {numeric: true, sensitivity: 'base'});
        return isAscending ? -result : result;
    });
    
    // Update header class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Reorder rows
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + K for search focus
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(function(modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// Utility functions
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '11';
    document.body.appendChild(container);
    return container;
}

// Export functions for global use
window.showRegulationDetails = showRegulationDetails;
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
