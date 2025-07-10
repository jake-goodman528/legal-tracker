/**
 * Navigation Fix Script
 * Ensures admin navigation links work consistently by preventing JavaScript interference
 */

(function() {
    'use strict';
    
    // Only run on admin pages
    if (!window.location.pathname.startsWith('/admin/')) {
        return;
    }
    
    console.log('Navigation Fix: Initializing admin navigation protection');
    
    // Store original navigation behavior
    const originalNavigationLinks = new Map();
    
    function protectNavigationLinks() {
        // Find all admin navigation links
        const adminNavLinks = document.querySelectorAll('.admin-nav-link, a[href*="/admin/"]');
        
        adminNavLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // Skip placeholder links
            if (!href || href === '#' || href === 'javascript:void(0)') {
                return;
            }
            
            // Store original href
            originalNavigationLinks.set(link, href);
            
            // Add protected click handler
            link.addEventListener('click', function(e) {
                // Only protect actual navigation links, not buttons or other elements
                if (this.tagName === 'A' && this.href && !this.href.includes('#')) {
                    console.log('Navigation Fix: Protecting navigation to', this.href);
                    
                    // Stop any event propagation that might interfere
                    e.stopImmediatePropagation();
                    
                    // Ensure we navigate to the correct URL
                    const targetUrl = this.href;
                    
                    // Use setTimeout to ensure navigation happens after any other handlers
                    setTimeout(() => {
                        if (targetUrl.startsWith('http') || targetUrl.startsWith('/')) {
                            window.location.href = targetUrl;
                        }
                    }, 0);
                    
                    // Prevent default to avoid double navigation
                    e.preventDefault();
                    return false;
                }
            }, true); // Use capture phase to run before other handlers
        });
        
        console.log(`Navigation Fix: Protected ${adminNavLinks.length} navigation links`);
    }
    
    function monitorNavigationErrors() {
        // Monitor for navigation-related errors
        const originalConsoleError = console.error;
        console.error = function(...args) {
            const message = args.join(' ');
            if (message.includes('navigation') || message.includes('href') || message.includes('click')) {
                console.warn('Navigation Fix: Detected potential navigation error:', message);
            }
            originalConsoleError.apply(console, args);
        };
    }
    
    function fixDynamicContent() {
        // Watch for dynamically added content that might need protection
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const newNavLinks = node.querySelectorAll('.admin-nav-link, a[href*="/admin/"]');
                            if (newNavLinks.length > 0) {
                                console.log('Navigation Fix: Protecting newly added navigation links');
                                protectNavigationLinks();
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    function preventJavaScriptInterference() {
        // Prevent common JavaScript patterns that might interfere with navigation
        
        // Override problematic global click handlers
        const originalAddEventListener = Document.prototype.addEventListener;
        Document.prototype.addEventListener = function(type, listener, options) {
            if (type === 'click') {
                // Wrap click handlers to avoid interfering with navigation
                const wrappedListener = function(e) {
                    // Check if this is a navigation link
                    const target = e.target.closest('a[href*="/admin/"]');
                    if (target && target.classList.contains('admin-nav-link')) {
                        // Don't run other click handlers for navigation links
                        return;
                    }
                    
                    // Run the original listener
                    return listener.call(this, e);
                };
                
                return originalAddEventListener.call(this, type, wrappedListener, options);
            }
            
            return originalAddEventListener.call(this, type, listener, options);
        };
    }
    
    function addNavigationDebugInfo() {
        // Add debug information for navigation issues
        window.navigationDebug = {
            getProtectedLinks: () => Array.from(originalNavigationLinks.entries()),
            testNavigation: (url) => {
                console.log('Navigation Fix: Testing navigation to', url);
                window.location.href = url;
            },
            checkLinkStatus: () => {
                const links = document.querySelectorAll('.admin-nav-link');
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    const isProtected = originalNavigationLinks.has(link);
                    console.log(`Link: ${href}, Protected: ${isProtected}, Visible: ${link.offsetParent !== null}`);
                });
            }
        };
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Navigation Fix: DOM loaded, initializing...');
            protectNavigationLinks();
            monitorNavigationErrors();
            fixDynamicContent();
            preventJavaScriptInterference();
            addNavigationDebugInfo();
        });
    } else {
        // DOM is already loaded
        console.log('Navigation Fix: DOM already loaded, initializing immediately...');
        protectNavigationLinks();
        monitorNavigationErrors();
        fixDynamicContent();
        preventJavaScriptInterference();
        addNavigationDebugInfo();
    }
    
    // Also run after a short delay to catch any late-loading content
    setTimeout(() => {
        console.log('Navigation Fix: Running delayed initialization...');
        protectNavigationLinks();
    }, 1000);
    
    console.log('Navigation Fix: Script loaded successfully');
})(); 