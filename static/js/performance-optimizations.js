// Performance Optimizations
class PerformanceOptimizer {
    constructor() {
        this.init();
    }
    
    init() {
        this.addLazyLoading();
        this.addImageOptimization();
        this.addCacheManagement();
        this.addDebouncing();
        this.addVirtualScrolling();
    }
    
    addLazyLoading() {
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
        
        // Lazy load content sections
        const sections = document.querySelectorAll('.lazy-section');
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('loaded');
                }
            });
        }, { threshold: 0.1 });
        
        sections.forEach(section => sectionObserver.observe(section));
    }
    
    addImageOptimization() {
        // Add loading="lazy" to images
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
        });
        
        // Add responsive image support
        const responsiveImages = document.querySelectorAll('.responsive-img');
        responsiveImages.forEach(img => {
            if (!img.srcset) {
                const src = img.src;
                const baseName = src.substring(0, src.lastIndexOf('.'));
                const extension = src.substring(src.lastIndexOf('.'));
                
                img.srcset = `
                    ${baseName}-small${extension} 480w,
                    ${baseName}-medium${extension} 768w,
                    ${baseName}-large${extension} 1200w
                `;
                img.sizes = '(max-width: 480px) 480px, (max-width: 768px) 768px, 1200px';
            }
        });
    }
    
    addCacheManagement() {
        // Cache API responses
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        
        // Override fetch for caching
        const originalFetch = window.fetch;
        window.fetch = (url, options = {}) => {
            if (options.method && options.method !== 'GET') {
                return originalFetch(url, options);
            }
            
            const cacheKey = url;
            const cached = this.cache.get(cacheKey);
            
            if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
                return Promise.resolve(new Response(JSON.stringify(cached.data), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                }));
            }
            
            return originalFetch(url, options).then(response => {
                if (response.ok && response.headers.get('content-type')?.includes('application/json')) {
                    return response.clone().json().then(data => {
                        this.cache.set(cacheKey, {
                            data: data,
                            timestamp: Date.now()
                        });
                        return response;
                    });
                }
                return response;
            });
        };
    }
    
    addDebouncing() {
            // Debounce inputs
    const textInputs = document.querySelectorAll('input[type="text"]');
    
    textInputs.forEach(input => {
            let timeout;
            const originalHandler = input.oninput;
            
            input.oninput = function(e) {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (originalHandler) {
                        originalHandler.call(this, e);
                    }
                }, 300);
            };
        });
        
        // Debounce resize events
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                window.dispatchEvent(new Event('debouncedResize'));
            }, 250);
        });
    }
    
    addVirtualScrolling() {
        // Virtual scrolling for large lists
        const largeContainers = document.querySelectorAll('.virtual-scroll-container');
        
        largeContainers.forEach(container => {
            const items = Array.from(container.children);
            if (items.length < 50) return; // Only virtualize large lists
            
            const itemHeight = 100; // Adjust based on your item height
            const containerHeight = container.clientHeight;
            const visibleItems = Math.ceil(containerHeight / itemHeight) + 2;
            
            let scrollTop = 0;
            let startIndex = 0;
            
            const updateVisibleItems = () => {
                const newStartIndex = Math.floor(scrollTop / itemHeight);
                const endIndex = Math.min(newStartIndex + visibleItems, items.length);
                
                if (newStartIndex !== startIndex) {
                    startIndex = newStartIndex;
                    
                    // Hide all items
                    items.forEach(item => item.style.display = 'none');
                    
                    // Show visible items
                    for (let i = startIndex; i < endIndex; i++) {
                        if (items[i]) {
                            items[i].style.display = 'block';
                            items[i].style.transform = `translateY(${i * itemHeight}px)`;
                        }
                    }
                }
            };
            
            container.addEventListener('scroll', () => {
                scrollTop = container.scrollTop;
                requestAnimationFrame(updateVisibleItems);
            });
            
            // Initial render
            updateVisibleItems();
        });
    }
    
    // Preload critical resources
    preloadCriticalResources() {
        const criticalResources = [
            '/static/css/style.css',
            '/static/js/main.js'
        ];
        
        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
        });
    }
    
    // Monitor performance
    monitorPerformance() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    console.log('Page Load Performance:', {
                        'DOM Content Loaded': perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        'Load Complete': perfData.loadEventEnd - perfData.loadEventStart,
                        'Total Load Time': perfData.loadEventEnd - perfData.navigationStart
                    });
                }, 0);
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const optimizer = new PerformanceOptimizer();
    optimizer.preloadCriticalResources();
    optimizer.monitorPerformance();
}); 