// Main Application Logic

class ImagePainter {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.background = null;
        this.foreground = null;
        this.bgWidth = null;
        this.bgHeight = null;
        this.fgWidth = null;
        this.fgHeight = null;
        
        this.bgOffsetX = 0;
        this.bgOffsetY = 0;
        this.fgOffsetX = 0;
        this.fgOffsetY = 0;
        this.resultX = 0;
        this.resultY = 0;
        this.resultWidth = null;
        this.resultHeight = null;
        
        this.dragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // File inputs
        document.getElementById('loadBgBtn').addEventListener('click', () => {
            document.getElementById('bgFile').click();
        });
        document.getElementById('loadFgBtn').addEventListener('click', () => {
            document.getElementById('fgFile').click();
        });

        document.getElementById('bgFile').addEventListener('change', (e) => this.loadBackground(e));
        document.getElementById('fgFile').addEventListener('change', (e) => this.loadForeground(e));

        // Resize buttons
        document.getElementById('resizeBgBtn').addEventListener('click', () => this.resizeBackground());
        document.getElementById('resizeFgBtn').addEventListener('click', () => this.resizeForeground());
        document.getElementById('resizeResultBtn').addEventListener('click', () => this.resizeResult());

        // Save button
        document.getElementById('saveResultBtn').addEventListener('click', () => this.saveResult());

        // View mode
        document.getElementById('viewMode').addEventListener('change', () => this.updateDisplay());

        // Canvas events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleScroll(e));
    }

    async loadBackground(e) {
        const file = e.target.files[0];
        if (file) {
            this.background = await ImageProcessor.loadImage(file);
            this.bgWidth = this.background.width;
            this.bgHeight = this.background.height;
            this.bgOffsetX = 0;
            this.bgOffsetY = 0;
            this.resultWidth = null;
            this.resultHeight = null;
            this.updateDisplay();
            this.updateInfo();
        }
    }

    async loadForeground(e) {
        const file = e.target.files[0];
        if (file) {
            this.foreground = await ImageProcessor.loadImage(file);
            this.fgWidth = this.foreground.width;
            this.fgHeight = this.foreground.height;
            this.fgOffsetX = 0;
            this.fgOffsetY = 0;
            this.resultWidth = null;
            this.resultHeight = null;
            this.updateDisplay();
            this.updateInfo();
        }
    }

    resizeBackground() {
        if (!this.background) return;
        const width = parseInt(document.getElementById('widthInput').value);
        const height = parseInt(document.getElementById('heightInput').value);
        if (width > 0 && height > 0) {
            this.background = ImageProcessor.resizeImage(this.background, width, height);
            this.bgWidth = width;
            this.bgHeight = height;
            this.updateDisplay();
            this.updateInfo();
        }
    }

    resizeForeground() {
        if (!this.foreground) return;
        const width = parseInt(document.getElementById('widthInput').value);
        const height = parseInt(document.getElementById('heightInput').value);
        if (width > 0 && height > 0) {
            this.foreground = ImageProcessor.resizeImage(this.foreground, width, height);
            this.fgWidth = width;
            this.fgHeight = height;
            this.updateDisplay();
            this.updateInfo();
        }
    }

    resizeResult() {
        if (!this.background || !this.foreground) return;
        const width = parseInt(document.getElementById('widthInput').value);
        const height = parseInt(document.getElementById('heightInput').value);
        if (width > 0 && height > 0) {
            this.resultWidth = width;
            this.resultHeight = height;
            this.resultX = 0;
            this.resultY = 0;
            this.updateDisplay();
            this.updateInfo();
        }
    }

    updateDisplay() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (!this.background || !this.foreground) return;

        // Create composite
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = Math.max(
            this.bgWidth + this.bgOffsetX,
            this.fgWidth + this.fgOffsetX,
            this.resultWidth || 0
        );
        tempCanvas.height = Math.max(
            this.bgHeight + this.bgOffsetY,
            this.fgHeight + this.fgOffsetY,
            this.resultHeight || 0
        );

        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.fillStyle = 'white';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

        // Draw background
        tempCtx.drawImage(this.background, this.bgOffsetX, this.bgOffsetY);

        // Draw foreground
        tempCtx.drawImage(this.foreground, this.fgOffsetX, this.fgOffsetY);

        // Get image data for processing
        let imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const viewMode = document.getElementById('viewMode').value;

        if (viewMode === 'Grayscale') {
            imageData = ImageProcessor.convertToGrayscale(imageData);
        } else if (viewMode === 'Binary') {
            imageData = ImageProcessor.convertToBinary(imageData);
        } else if (viewMode === 'Contours') {
            const binaryData = ImageProcessor.convertToBinary(imageData);
            const contours = ImageProcessor.findContours(binaryData);
            imageData = ImageProcessor.drawContoursWithColors(binaryData, contours);
            
            // Update contour info
            const totalArea = contours.reduce((sum, c) => sum + ImageProcessor.calculateContourArea(c), 0);
            document.getElementById('contourInfo').textContent = 
                `Contours: ${contours.length}, Total area: ${totalArea.toFixed(0)}px²`;
        } else {
            document.getElementById('contourInfo').textContent = '';
        }

        tempCtx.putImageData(imageData, 0, 0);

        this.canvas.width = tempCanvas.width;
        this.canvas.height = tempCanvas.height;
        this.ctx.drawImage(tempCanvas, 0, 0);

        // Draw result rectangle if set
        if (this.resultWidth && this.resultHeight) {
            this.ctx.strokeStyle = 'red';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(this.resultX, this.resultY, this.resultWidth, this.resultHeight);
        }
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const dragMode = document.getElementById('dragMode').value;

        this.dragging = false;
        this.dragStartX = x;
        this.dragStartY = y;

        if (dragMode === 'Result' && this.resultWidth && this.resultHeight) {
            const inRect = x >= this.resultX && x <= this.resultX + this.resultWidth &&
                          y >= this.resultY && y <= this.resultY + this.resultHeight;
            if (inRect) {
                this.dragging = true;
            }
        } else if (dragMode === 'Foreground' && this.foreground) {
            this.dragging = true;
        } else if (dragMode === 'Background' && this.background) {
            this.dragging = true;
        }
    }

    handleMouseMove(e) {
        if (!this.dragging) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const dragMode = document.getElementById('dragMode').value;

        const deltaX = x - this.dragStartX;
        const deltaY = y - this.dragStartY;

        if (dragMode === 'Result') {
            this.resultX += deltaX;
            this.resultY += deltaY;
        } else if (dragMode === 'Foreground') {
            this.fgOffsetX += deltaX;
            this.fgOffsetY += deltaY;
        } else if (dragMode === 'Background') {
            this.bgOffsetX += deltaX;
            this.bgOffsetY += deltaY;
        }

        this.dragStartX = x;
        this.dragStartY = y;
        this.updateDisplay();
        this.updateInfo();
    }

    handleMouseUp(e) {
        this.dragging = false;
    }

    handleScroll(e) {
        // Prevent default scroll behavior
        e.preventDefault();
    }

    updateInfo() {
        let info = '';
        if (this.background) {
            info += `Background: ${this.bgWidth}x${this.bgHeight}px`;
            if (this.bgOffsetX !== 0 || this.bgOffsetY !== 0) {
                info += ` (offset: ${Math.round(this.bgOffsetX)}, ${Math.round(this.bgOffsetY)})`;
            }
            info += '\n';
        }
        if (this.foreground) {
            info += `Foreground: ${this.fgWidth}x${this.fgHeight}px`;
            if (this.fgOffsetX !== 0 || this.fgOffsetY !== 0) {
                info += ` (offset: ${Math.round(this.fgOffsetX)}, ${Math.round(this.fgOffsetY)})`;
            }
            info += '\n';
        }
        if (this.background && this.foreground) {
            const resultW = this.resultWidth || this.bgWidth;
            const resultH = this.resultHeight || this.bgHeight;
            info += `Result: ${resultW}x${resultH}px`;
            if (this.resultX !== 0 || this.resultY !== 0) {
                info += ` (offset: ${Math.round(this.resultX)}, ${Math.round(this.resultY)})`;
            }
        }
        document.getElementById('info').textContent = info || 'No images loaded';
    }

    saveResult() {
        if (!this.background || !this.foreground) return;

        const tempCanvas = document.createElement('canvas');
        const resultW = this.resultWidth || this.bgWidth;
        const resultH = this.resultHeight || this.bgHeight;
        tempCanvas.width = resultW;
        tempCanvas.height = resultH;

        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.fillStyle = 'white';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

        tempCtx.drawImage(this.background, this.bgOffsetX, this.bgOffsetY);
        tempCtx.drawImage(this.foreground, this.fgOffsetX, this.fgOffsetY);

        if (this.resultWidth && this.resultHeight) {
            const imageData = tempCtx.getImageData(this.resultX, this.resultY, resultW, resultH);
            tempCanvas.width = resultW;
            tempCanvas.height = resultH;
            tempCtx.putImageData(imageData, 0, 0);
        }

        // Download
        const link = document.createElement('a');
        link.href = tempCanvas.toDataURL('image/png');
        link.download = 'result.png';
        link.click();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ImagePainter();
});
