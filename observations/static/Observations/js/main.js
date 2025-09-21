/**
 * Main JavaScript file for the observations Nids application
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

/**
 * Opens a resizable window to display an image
 * @param {string} imageUrl - The URL of the image to display
 */
function openResizableImageWindow(imageUrl) {
    // Open a new window
    var imgWindow = window.open('', '_blank', 'width=800,height=600,resizable=yes,scrollbars=yes,status=yes');

    // Write HTML content to the new window
    imgWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Image Viewer</title>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    overflow: auto;
                    background-color: #f5f5f5;
                    font-family: Arial, sans-serif;
                }
                .image-container {
                    position: relative;
                    margin: 0 auto;
                    text-align: center;
                }
                img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    cursor: move;
                    resize: both;
                    overflow: auto;
                }
                .controls {
                    margin-top: 15px;
                    text-align: center;
                }
                button {
                    padding: 8px 15px;
                    margin: 0 5px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="image-container">
                <img src="${imageUrl}" id="resizable-image" alt="Image">
            </div>
            <div class="controls">
                <button onclick="zoomIn()">Zoom In</button>
                <button onclick="zoomOut()">Zoom Out</button>
                <button onclick="resetZoom()">Reset</button>
            </div>

            <script>
                // Make the image draggable
                const img = document.getElementById('resizable-image');
                let isDragging = false;
                let currentX;
                let currentY;
                let initialX;
                let initialY;
                let xOffset = 0;
                let yOffset = 0;

                img.addEventListener("mousedown", dragStart);
                document.addEventListener("mouseup", dragEnd);
                document.addEventListener("mousemove", drag);

                function dragStart(e) {
                    initialX = e.clientX - xOffset;
                    initialY = e.clientY - yOffset;

                    if (e.target === img) {
                        isDragging = true;
                    }
                }

                function dragEnd(e) {
                    initialX = currentX;
                    initialY = currentY;

                    isDragging = false;
                }

                function drag(e) {
                    if (isDragging) {
                        e.preventDefault();
                        currentX = e.clientX - initialX;
                        currentY = e.clientY - initialY;

                        xOffset = currentX;
                        yOffset = currentY;

                        setTranslate(currentX, currentY, img);
                    }
                }

                function setTranslate(xPos, yPos, el) {
                    el.style.transform = "translate3d(" + xPos + "px, " + yPos + "px, 0)";
                }

                // Zoom functionality
                let scale = 1;
                const ZOOM_SPEED = 0.1;

                function zoomIn() {
                    scale += ZOOM_SPEED;
                    applyTransform();
                }

                function zoomOut() {
                    scale -= ZOOM_SPEED;
                    if (scale < 0.1) scale = 0.1;
                    applyTransform();
                }

                function resetZoom() {
                    scale = 1;
                    xOffset = 0;
                    yOffset = 0;
                    applyTransform();
                }

                function applyTransform() {
                    img.style.transform = \`translate3d(\${xOffset}px, \${yOffset}px, 0) scale(\${scale})\`;
                }
            </script>
        </body>
        </html>
    `);

    imgWindow.document.close();
}
