// Main JavaScript for STR Compliance Toolkit - Enhanced Database Interface

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

    // Initialize navigation active states
    initializeNavigation();
    
    // Initialize features (compatible with advanced search)
    initializeFormValidation();
    initializeKeyboardShortcuts();
    initializeAnimations();
    initializeCompatibilityFeatures();
});

// Initialize navigation active states and functionality
function initializeNavigation() {
    // Set active nav link based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.kaystreet-nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        // Check if link href matches current path
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath || 
            (currentPath.includes('/regulations') && linkPath.includes('/regulations')) ||
            (currentPath.includes('/updates') && linkPath.includes('/updates')) ||
            (currentPath.includes('/admin') && linkPath.includes('/admin'))) {
            link.classList.add('active');
        }
    });
    
    // Smooth scroll behavior for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Handle mobile menu close when clicking nav links
    const navLinks_mobile = document.querySelectorAll('.kaystreet-nav-link');
    const mobileMenu = document.getElementById('kaystreetNav');
    
    navLinks_mobile.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && mobileMenu.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(mobileMenu);
                bsCollapse.hide();
            }
        });
    });
}

// Compatibility features for pages without advanced search
function initializeCompatibilityFeatures() {
    // Only initialize if advanced search is not present
    if (!document.getElementById('searchInput') && document.getElementById('search')) {
        initializeLegacySearch();
    }
    
    // Initialize table features if regulations table exists but advanced search doesn't handle it
    if (document.querySelector('.regulations-table') && !window.advancedSearch) {
        initializeLegacyTableFeatures();
    }
}

// Legacy search for pages without advanced search
function initializeLegacySearch() {
    const searchInput = document.getElementById('search');
    const jurisdictionSelect = document.getElementById('jurisdiction');
    const locationSelect = document.getElementById('location');
    const categorySelect = document.getElementById('category');
    
    let debounceTimer;
    
    // Enhanced search with debouncing
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const searchValue = this.value.trim();
            
            // Show loading indicator
            showSearchLoading(true);
            
            debounceTimer = setTimeout(function() {
                if (searchValue.length >= 2 || searchValue.length === 0) {
                    submitLegacyFilter();
                }
                showSearchLoading(false);
            }, 300);
        });
        
        // Clear search functionality
        const clearSearchBtn = createClearSearchButton(searchInput);
        if (searchInput.value) {
            clearSearchBtn.style.display = 'block';
        }
    }
    
    // Auto-filter on dropdown changes
    [jurisdictionSelect, locationSelect, categorySelect].forEach(select => {
        if (select) {
            select.addEventListener('change', function() {
                showSearchLoading(true);
                setTimeout(() => {
                    submitLegacyFilter();
                    showSearchLoading(false);
                }, 100);
            });
        }
    });
}

// Legacy filter submission
function submitLegacyFilter() {
    const form = document.getElementById('filterForm');
    if (form) {
        // Add loading state to form
        form.classList.add('loading');
        form.submit();
    }
}

// Create clear search button
function createClearSearchButton(searchInput) {
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-link position-absolute end-0 top-50 translate-middle-y me-2';
    clearBtn.style.display = 'none';
    clearBtn.style.zIndex = '10';
    clearBtn.innerHTML = '<i class="fas fa-times"></i>';
    
    clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        this.style.display = 'none';
        if (window.advancedSearch) {
            window.advancedSearch.clearAllFilters();
        } else {
            submitLegacyFilter();
        }
    });
    
    searchInput.addEventListener('input', function() {
        clearBtn.style.display = this.value ? 'block' : 'none';
    });
    
    // Position the clear button
    const inputGroup = searchInput.parentNode;
    inputGroup.style.position = 'relative';
    inputGroup.appendChild(clearBtn);
    
    return clearBtn;
}

// Show/hide search loading indicator
function showSearchLoading(show) {
    const searchInput = document.getElementById('search') || document.getElementById('searchInput');
    if (!searchInput) return;
    
    let loadingIndicator = searchInput.parentNode.querySelector('.search-loading');
    
    if (show && !loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'search-loading position-absolute end-0 top-50 translate-middle-y me-4';
        loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin text-muted"></i>';
        loadingIndicator.style.zIndex = '5';
        searchInput.parentNode.appendChild(loadingIndicator);
    } else if (!show && loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Legacy table features for non-advanced search pages
function initializeLegacyTableFeatures() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    let currentSort = { column: null, direction: 'asc' };
    
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            legacySortTable(this);
        });
    });
    
    // Table density toggle
    const densityToggle = document.querySelector('[onclick*="toggleTableDensity"]');
    if (densityToggle) {
        densityToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleTableDensity();
        });
    }
    
    // Enhanced table row hover effects
    const tableRows = document.querySelectorAll('.regulation-row');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
            this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
}

// Legacy table sorting function
function legacySortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        const icon = th.querySelector('.sort-icon');
        if (icon) {
            icon.className = 'fas fa-sort sort-icon';
        }
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();
        
        // Check if values are dates
        if (!isNaN(Date.parse(aText)) && !isNaN(Date.parse(bText))) {
            return isAscending ? new Date(aText) - new Date(bText) : new Date(bText) - new Date(aText);
        } else {
            return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
        }
    });
    
    // Update header classes
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    const icon = header.querySelector('.sort-icon');
    if (icon) {
        icon.className = `fas fa-sort-${isAscending ? 'down' : 'up'} sort-icon text-primary`;
    }
    
    // Re-append sorted rows with animation
    rows.forEach((row, index) => {
        setTimeout(() => {
            tbody.appendChild(row);
            row.style.opacity = '0';
            row.style.animation = 'fadeInUp 0.3s ease-out forwards';
            row.style.animationDelay = `${index * 0.02}s`;
        }, index * 10);
    });
}

// Table density toggle
function toggleTableDensity() {
    const table = document.querySelector('.regulations-table') || document.querySelector('.notion-table');
    if (table) {
        table.classList.toggle('table-compact');
        
        // Save preference
        const isCompact = table.classList.contains('table-compact');
        localStorage.setItem('tableCompact', isCompact);
    }
}

// Form validation functionality
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Highlight first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
    
    // Character count for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        updateCharacterCount(textarea);
        textarea.addEventListener('input', () => updateCharacterCount(textarea));
    });
}

// Update character count for textareas
function updateCharacterCount(textarea) {
    const maxLength = textarea.getAttribute('maxlength');
    const currentLength = textarea.value.length;
    
    let counter = textarea.parentNode.querySelector('.character-count');
    if (!counter) {
        counter = document.createElement('div');
        counter.className = 'character-count text-muted small mt-1';
        textarea.parentNode.appendChild(counter);
    }
    
    counter.textContent = `${currentLength}/${maxLength} characters`;
    
    if (currentLength > maxLength * 0.9) {
        counter.classList.add('text-warning');
        counter.classList.remove('text-muted');
    } else {
        counter.classList.add('text-muted');
        counter.classList.remove('text-warning');
    }
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + K for search focus
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('searchInput') || document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Ctrl/Cmd + Shift + F for advanced search
        if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'F') {
            event.preventDefault();
            if (window.openAdvancedSearch) {
                window.openAdvancedSearch();
            }
        }
        
        // Escape to clear search
        if (event.key === 'Escape') {
            const searchInput = document.getElementById('searchInput') || document.getElementById('search');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                if (window.advancedSearch) {
                    window.advancedSearch.clearAllFilters();
                }
                searchInput.blur();
            }
        }
        
        // Arrow keys for table navigation (when table row is focused)
        if (['ArrowUp', 'ArrowDown'].includes(event.key)) {
            const focusedRow = document.activeElement.closest('.regulation-row');
            if (focusedRow) {
                event.preventDefault();
                const rows = Array.from(document.querySelectorAll('.regulation-row'));
                const currentIndex = rows.indexOf(focusedRow);
                let newIndex;
                
                if (event.key === 'ArrowUp') {
                    newIndex = currentIndex > 0 ? currentIndex - 1 : rows.length - 1;
                } else {
                    newIndex = currentIndex < rows.length - 1 ? currentIndex + 1 : 0;
                }
                
                if (rows[newIndex]) {
                    rows[newIndex].focus();
                    rows[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        }
    });
    
    // Add tabindex to regulation rows for keyboard navigation
    const regulationRows = document.querySelectorAll('.regulation-row');
    regulationRows.forEach((row, index) => {
        row.tabIndex = index === 0 ? 0 : -1;
        row.addEventListener('focus', function() {
            regulationRows.forEach(r => r.tabIndex = -1);
            this.tabIndex = 0;
        });
        
        // Enter key to view details
        row.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                const link = this.querySelector('a[href*="/regulations/"]');
                if (link) {
                    link.click();
                }
            }
        });
    });
}

// Animation initialization
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatableElements = document.querySelectorAll('.card, .regulation-row, .regulation-card');
    animatableElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
    
    // Add CSS for fade-in animation if not exists
    if (!document.querySelector('#fade-in-styles')) {
        const style = document.createElement('style');
        style.id = 'fade-in-styles';
        style.textContent = `
            .fade-in {
                opacity: 1 !important;
                transform: translateY(0) !important;
                transition: opacity 0.6s ease-out, transform 0.6s ease-out;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Utility functions for loading states
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

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = createToastContainer();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Create toast container
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Global utility functions for backward compatibility
window.submitFilter = function() {
    if (window.advancedSearch) {
        window.advancedSearch.applyFilters();
    } else {
        submitLegacyFilter();
    }
};

window.toggleTableDensity = toggleTableDensity;
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
