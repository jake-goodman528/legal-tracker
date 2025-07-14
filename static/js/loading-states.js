// Loading States for UI Operations
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
    

    

}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {

}); 