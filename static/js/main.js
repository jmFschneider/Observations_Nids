/**
 * Main JavaScript file for the Observations Nids application
 */

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main JS loaded');
    
    // Initialize any custom functionality here
    initializeTooltips();
    setupEventListeners();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    // Check if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        // Initialize all tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Setup event listeners for interactive elements
 */
function setupEventListeners() {
    // Add your custom event listeners here
}