/**
 * STR Compliance Toolkit - Main JavaScript
 * Enhanced with comprehensive error logging and monitoring
 */

// Error tracking and logging system
class ErrorTracker {
    constructor() {
        this.errors = [];
        this.maxErrors = 100; // Store max 100 errors in memory
        this.setupGlobalErrorHandling();
        this.setupPerformanceMonitoring();
    }

    setupGlobalErrorHandling() {
        // Global JavaScript error handler
        window.addEventListener('error', (event) => {
            this.logError({
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error ? event.error.stack : null,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            });
        });

        // Promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.logError({
                type: 'unhandled_promise_rejection',
                message: event.reason ? event.reason.toString() : 'Unknown promise rejection',
                stack: event.reason && event.reason.stack ? event.reason.stack : null,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href
            });
        });

        // Network error detection
        window.addEventListener('online', () => {
            this.logInfo('Network connection restored');
        });

        window.addEventListener('offline', () => {
            this.logError({
                type: 'network_error',
                message: 'Network connection lost',
                timestamp: new Date().toISOString(),
                url: window.location.href
            });
        });
    }

    setupPerformanceMonitoring() {
        // Monitor page load performance
        if ('PerformanceObserver' in window) {
            try {
                // Monitor largest contentful paint
                const lcpObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.startTime > 4000) { // LCP > 4s is poor
                            this.logWarning({
                                type: 'performance_warning',
                                metric: 'largest_contentful_paint',
                                value: entry.startTime,
                                message: `Poor LCP performance: ${entry.startTime}ms`,
                                timestamp: new Date().toISOString()
                            });
                        }
                    }
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

                // Monitor long tasks
                const longTaskObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.logWarning({
                            type: 'performance_warning',
                            metric: 'long_task',
                            duration: entry.duration,
                            message: `Long task detected: ${entry.duration}ms`,
                            timestamp: new Date().toISOString()
                        });
                    }
                });
                longTaskObserver.observe({ entryTypes: ['longtask'] });

            } catch (e) {
                console.warn('Performance monitoring setup failed:', e);
            }
        }

        // Monitor resource loading errors
        document.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.logError({
                    type: 'resource_error',
                    message: `Failed to load resource: ${event.target.src || event.target.href}`,
                    element: event.target.tagName,
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                });
            }
        }, true);
    }

    logError(error) {
        console.error('Client Error:', error);
        this.storeError({ ...error, level: 'error' });
        this.sendToServer(error, 'error');
    }

    logWarning(warning) {
        console.warn('Client Warning:', warning);
        this.storeError({ ...warning, level: 'warning' });
        this.sendToServer(warning, 'warning');
    }

    logInfo(message) {
        console.info('Client Info:', message);
        this.storeError({ 
            type: 'info',
            message: message,
            level: 'info',
            timestamp: new Date().toISOString(),
            url: window.location.href
        });
    }

    storeError(error) {
        this.errors.push(error);
        
        // Keep only the most recent errors
        if (this.errors.length > this.maxErrors) {
            this.errors = this.errors.slice(-this.maxErrors);
        }

        // Store in localStorage for persistence across page loads
        try {
            const storedErrors = JSON.parse(localStorage.getItem('str_client_errors') || '[]');
            storedErrors.push(error);
            
            // Keep only last 50 errors in localStorage
            const recentErrors = storedErrors.slice(-50);
            localStorage.setItem('str_client_errors', JSON.stringify(recentErrors));
        } catch (e) {
            console.warn('Failed to store error in localStorage:', e);
        }
    }

    sendToServer(error, level = 'error') {
        // Only send errors in production or if explicitly enabled
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return; // Don't send errors in development
        }

        // Debounce error sending to avoid spam
        if (this.lastErrorSent && Date.now() - this.lastErrorSent < 1000) {
            return;
        }
        this.lastErrorSent = Date.now();

        try {
            fetch('/api/client-errors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    error: error,
                    level: level,
                    session_id: this.getSessionId(),
                    page_info: {
                        url: window.location.href,
                        referrer: document.referrer,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        screen: {
                            width: window.screen.width,
                            height: window.screen.height
                        }
                    }
                })
            }).catch(e => {
                console.warn('Failed to send error to server:', e);
            });
        } catch (e) {
            console.warn('Error sending error to server:', e);
        }
    }

    getSessionId() {
        // Simple session ID generation/retrieval
        let sessionId = sessionStorage.getItem('str_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('str_session_id', sessionId);
        }
        return sessionId;
    }

    getErrors() {
        return this.errors;
    }

    clearErrors() {
        this.errors = [];
        localStorage.removeItem('str_client_errors');
    }

    // Method to track API errors specifically
    trackApiError(endpoint, error, requestData = null) {
        this.logError({
            type: 'api_error',
            endpoint: endpoint,
            message: error.message || error.toString(),
            status: error.status || null,
            response: error.response || null,
            requestData: requestData ? JSON.stringify(requestData).substring(0, 500) : null,
            timestamp: new Date().toISOString(),
            url: window.location.href
        });
    }

    // Method to track user interactions for debugging
    trackUserAction(action, details = {}) {
        this.logInfo({
            type: 'user_action',
            action: action,
            details: details,
            timestamp: new Date().toISOString(),
            url: window.location.href
        });
    }
}

// API Helper with error tracking
class ApiClient {
    constructor(errorTracker) {
        this.errorTracker = errorTracker;
        this.baseUrl = '/api';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const startTime = performance.now();

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const duration = performance.now() - startTime;

            // Log slow API calls
            if (duration > 2000) {
                this.errorTracker.logWarning({
                    type: 'slow_api_call',
                    endpoint: endpoint,
                    duration: duration,
                    message: `Slow API call: ${endpoint} took ${duration.toFixed(2)}ms`,
                    timestamp: new Date().toISOString()
                });
            }

            if (!response.ok) {
                const errorData = await response.text();
                const error = new Error(`API Error: ${response.status} ${response.statusText}`);
                error.status = response.status;
                error.response = errorData;
                
                this.errorTracker.trackApiError(endpoint, error, options.body);
                throw error;
            }

            const data = await response.json();
            
            // Log successful API calls in debug mode
            if (window.STR_DEBUG) {
                console.log(`API Success: ${endpoint} (${duration.toFixed(2)}ms)`, data);
            }

            return data;

        } catch (error) {
            const duration = performance.now() - startTime;
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                // Network error
                this.errorTracker.trackApiError(endpoint, {
                    message: 'Network error - check internet connection',
                    type: 'network_error'
                }, options.body);
            } else {
                this.errorTracker.trackApiError(endpoint, error, options.body);
            }

            throw error;
        }
    }

    // Convenience methods
    get(endpoint, params = {}) {
        const url = new URL(endpoint, window.location.origin + this.baseUrl);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search);
    }

    post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Initialize error tracking and API client
const errorTracker = new ErrorTracker();
const apiClient = new ApiClient(errorTracker);

// Enhanced alert management with error tracking
class AlertManager {
    constructor() {
        this.alerts = [];
        this.setupAlertManagement();
    }

    setupAlertManagement() {
        // Auto-dismiss alerts after timeout
        document.addEventListener('DOMContentLoaded', () => {
            this.managePersistentAlerts();
        });

        // Track alert interactions
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('btn-close') && event.target.closest('.alert')) {
                const alert = event.target.closest('.alert');
                const alertType = this.getAlertType(alert);
                errorTracker.trackUserAction('alert_dismissed', { type: alertType });
            }
        });
    }

    managePersistentAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach((alert, index) => {
            const alertType = this.getAlertType(alert);
            let timeout = 5000; // Default 5 seconds

            // Different timeouts for different alert types
            switch (alertType) {
                case 'success':
                    timeout = 4000;
                    break;
                case 'info':
                    timeout = 6000;
                    break;
                case 'warning':
                    timeout = 8000;
                    break;
                case 'error':
                case 'danger':
                    timeout = 10000;
                    break;
            }

            // Auto-dismiss after timeout
            setTimeout(() => {
                if (alert && alert.parentNode) {
                    const bootstrap = window.bootstrap;
                    if (bootstrap && bootstrap.Alert) {
                        const bsAlert = new bootstrap.Alert(alert);
                        bsAlert.close();
                    } else {
                        alert.remove();
                    }
                }
            }, timeout + (index * 1000)); // Stagger multiple alerts
        });
    }

    getAlertType(alertElement) {
        const classes = alertElement.className;
        if (classes.includes('alert-success')) return 'success';
        if (classes.includes('alert-danger')) return 'error';
        if (classes.includes('alert-warning')) return 'warning';
        if (classes.includes('alert-info')) return 'info';
        return 'unknown';
    }

    show(message, type = 'info', duration = 5000) {
        const alertId = 'alert_' + Date.now();
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
                <div class="d-flex align-items-center">
                    <div class="alert-icon me-3">
                        <i class="fas fa-${this.getIcon(type)}"></i>
                    </div>
                    <div class="alert-content flex-grow-1">
                        ${message}
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Add to container
        const container = document.querySelector('.container') || document.body;
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = alertHtml;
        const alertElement = tempDiv.firstElementChild;
        
        container.insertBefore(alertElement, container.firstChild);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                if (alertElement && alertElement.parentNode) {
                    alertElement.remove();
                }
            }, duration);
        }

        errorTracker.trackUserAction('alert_shown', { type, message: message.substring(0, 100) });
        return alertId;
    }

    getIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error':
            case 'danger': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            case 'info': return 'info-circle';
            default: return 'info-circle';
        }
    }
}

// Initialize alert manager
const alertManager = new AlertManager();

// Enhanced utility functions
const STRUtils = {
    // Debounce function with error tracking
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) {
                    try {
                        func(...args);
                    } catch (error) {
                        errorTracker.logError({
                            type: 'debounced_function_error',
                            message: error.message,
                            stack: error.stack,
                            timestamp: new Date().toISOString()
                        });
                    }
                }
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) {
                try {
                    func(...args);
                } catch (error) {
                    errorTracker.logError({
                        type: 'immediate_function_error',
                        message: error.message,
                        stack: error.stack,
                        timestamp: new Date().toISOString()
                    });
                }
            }
        };
    },

    // Format date with error handling
    formatDate(date, format = 'YYYY-MM-DD') {
        try {
            if (!date) return '';
            
            const d = new Date(date);
            if (isNaN(d.getTime())) {
                throw new Error(`Invalid date: ${date}`);
            }

            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');

            switch (format) {
                case 'YYYY-MM-DD':
                    return `${year}-${month}-${day}`;
                case 'MM/DD/YYYY':
                    return `${month}/${day}/${year}`;
                case 'DD/MM/YYYY':
                    return `${day}/${month}/${year}`;
                default:
                    return d.toLocaleDateString();
            }
        } catch (error) {
            errorTracker.logError({
                type: 'date_formatting_error',
                message: error.message,
                input: date,
                format: format,
                timestamp: new Date().toISOString()
            });
            return 'Invalid Date';
        }
    },

    // Safe localStorage operations
    setStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            errorTracker.logError({
                type: 'storage_error',
                operation: 'set',
                message: error.message,
                key: key,
                timestamp: new Date().toISOString()
            });
            return false;
        }
    },

    getStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            errorTracker.logError({
                type: 'storage_error',
                operation: 'get',
                message: error.message,
                key: key,
                timestamp: new Date().toISOString()
            });
            return defaultValue;
        }
    },

    // Form validation with error tracking
    validateForm(formElement) {
        try {
            if (!formElement) {
                throw new Error('Form element is required');
            }

            const errors = [];
            const requiredFields = formElement.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    errors.push(`${field.name || field.id || 'Unknown field'} is required`);
                }
            });

            // Email validation
            const emailFields = formElement.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !this.isValidEmail(field.value)) {
                    errors.push(`${field.name || field.id || 'Email field'} must be a valid email address`);
                }
            });

            if (errors.length > 0) {
                errorTracker.trackUserAction('form_validation_failed', {
                    form: formElement.id || formElement.name || 'unknown',
                    errors: errors
                });
            }

            return {
                isValid: errors.length === 0,
                errors: errors
            };

        } catch (error) {
            errorTracker.logError({
                type: 'form_validation_error',
                message: error.message,
                timestamp: new Date().toISOString()
            });
            return {
                isValid: false,
                errors: ['Form validation failed']
            };
        }
    },

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
};

// Page load performance tracking
document.addEventListener('DOMContentLoaded', () => {
    // Track page load performance
    if ('performance' in window && 'timing' in performance) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const timing = performance.timing;
                const loadTime = timing.loadEventEnd - timing.navigationStart;
                const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;

                if (loadTime > 5000) {
                    errorTracker.logWarning({
                        type: 'slow_page_load',
                        loadTime: loadTime,
                        domReady: domReady,
                        message: `Slow page load: ${loadTime}ms`,
                        timestamp: new Date().toISOString()
                    });
                }

                // Log performance metrics
                if (window.STR_DEBUG) {
                    console.log('Page Performance:', {
                        loadTime: loadTime,
                        domReady: domReady,
                        firstPaint: timing.responseEnd - timing.navigationStart
                    });
                }
            }, 100);
        });
    }

    // Track user interactions
    errorTracker.trackUserAction('page_loaded', {
        page: window.location.pathname,
        referrer: document.referrer
    });
});

// Export for global access
window.STR = {
    errorTracker,
    apiClient,
    alertManager,
    utils: STRUtils
};

// Development mode helpers
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.STR_DEBUG = true;
    
    // Add debug helpers to console
    window.STRDebug = {
        getErrors: () => errorTracker.getErrors(),
        clearErrors: () => errorTracker.clearErrors(),
        testError: () => { throw new Error('Test error for debugging'); },
        testApiError: () => apiClient.get('/test-error-endpoint'),
        showAlert: (message, type) => alertManager.show(message, type)
    };
    
    console.log('STR Debug mode enabled. Use STRDebug object for debugging helpers.');
}
