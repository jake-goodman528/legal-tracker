// Navigation Fix JavaScript
// This file prevents console errors and provides basic navigation enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Prevent default behavior for empty href links
    const emptyLinks = document.querySelectorAll('a[href="#"], a[href=""]');
    emptyLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
        });
    });
    
    // Add smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]:not([href="#"])');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Basic error handling for missing elements
    const handleMissingElement = (selector, context = 'navigation') => {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`${context}: Element with selector "${selector}" not found`);
        }
        return element;
    };
    
    // Export for use in other scripts
    window.navigationFix = {
        handleMissingElement
    };
}); 