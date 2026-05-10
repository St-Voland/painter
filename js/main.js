class ImagePainter {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');

        this.originalImage = null;
        this.image = null;
        this.processedCanvas = null;
        this.components = null;
        this.contourInfo = '';

        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;

        this.selectedColor = {r: 255, g: 0, b: 0, a: 255};

        this.undoStack = [];
        this.redoStack = [];
        this.maxUndo = 50;

        this.dragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.dragPanX = 0;
        this.dragPanY = 0;

        this.setupEventListeners();
        this.updateColorPreview();
    }

    setupEventListeners() {
        const $ = id => document.getElementById(id);

        $('loadBtn').addEventListener('click', () => $('fileInput').click());
        $('fileInput').addEventListener('change', (e) => this.loadImage(e));

        $('resizeBtn').addEventListener('click', () => this.resizeImage());
        $('saveBtn').addEventListener('click', () => this.saveImage());
        $('saveViewBtn').addEventListener('click', () => this.saveView());
        $('undoBtn').addEventListener('click', () => this.undo());
        $('redoBtn').addEventListener('click', () => this.redo());
        $('zoomInBtn').addEventListener('click', () => this.zoomIn());
        $('zoomOutBtn').addEventListener('click', () => this.zoomOut());
        $('zoomResetBtn').addEventListener('click', () => this.zoomReset());

        $('pickColorBtn').addEventListener('click', () => this.pickColorDialog());

        $('viewMode').addEventListener('change', () => this.computeView());
        ['rInput', 'gInput', 'bInput', 'aInput'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => this.updateColorFromInputs());
        });

        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.onMouseUp());
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e));
    }

    loadImage(e) {
        const file = e.target.files[0];
        if (!file) return;
        ImageProcessor.loadImage(file).then(img => {
            this.originalImage = img;
            this.image = img;
            this.zoomLevel = 1.0;
            this.panX = 0;
            this.panY = 0;
            this.undoStack = [];
            this.redoStack = [];
            this.computeView();
            this.updateInfo();
        });
    }

    computeView() {
        if (!this.image) return;
        this.saveSnapshot();

        const w = this.image.width;
        const h = this.image.height;

        this.processedCanvas = document.createElement('canvas');
        this.processedCanvas.width = w;
        this.processedCanvas.height = h;
        const ctx = this.processedCanvas.getContext('2d');
        ctx.drawImage(this.image, 0, 0);
        let imageData = ctx.getImageData(0, 0, w, h);

        const view = document.getElementById('viewMode').value;

        const binaryData = new ImageData(new Uint8ClampedArray(imageData.data), w, h);
        ImageProcessor.convertToBinary(binaryData);
        this.components = ImageProcessor.findComponents(binaryData);

        if (view === 'Grayscale') {
            imageData = ImageProcessor.convertToGrayscale(imageData);
            this.contourInfo = '';
        } else if (view === 'Binary') {
            imageData = ImageProcessor.convertToBinary(imageData);
            this.contourInfo = '';
        } else if (view === 'Contours') {
            const bw = new ImageData(new Uint8ClampedArray(binaryData.data), w, h);
            imageData = ImageProcessor.drawComponents(bw, this.components, () => ({
                r: Math.floor(Math.random() * 256),
                g: Math.floor(Math.random() * 256),
                b: Math.floor(Math.random() * 256),
                a: 255
            }));
            imageData = ImageProcessor.drawBoundaries(imageData, this.components);
            const totalArea = this.components.reduce((sum, c) => sum + c.length, 0);
            this.contourInfo = `Contours: ${this.components.length}, Total area: ${totalArea}px²`;
        } else if (view === 'Flood Fill') {
            const bw = new ImageData(new Uint8ClampedArray(binaryData.data), w, h);
            imageData = ImageProcessor.drawComponents(bw, this.components, () => ({
                r: Math.floor(Math.random() * 256),
                g: Math.floor(Math.random() * 256),
                b: Math.floor(Math.random() * 256),
                a: 255
            }));
            const totalArea = this.components.reduce((sum, c) => sum + c.length, 0);
            this.contourInfo = `Flood fill: ${this.components.length}, Total area: ${totalArea}px²`;
        } else {
            this.contourInfo = '';
        }

        ctx.putImageData(imageData, 0, 0);
        this.updateDisplay();
        document.getElementById('contourInfo').textContent = this.contourInfo;
    }

    updateDisplay() {
        const ctx = this.ctx;
        const canvas = this.canvas;
        const src = this.processedCanvas || this.image;

        if (!src) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            return;
        }

        const w = src.width * this.zoomLevel;
        const h = src.height * this.zoomLevel;

        canvas.width = Math.max(800, w);
        canvas.height = Math.max(600, h);

        ctx.fillStyle = '#888';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.save();
        ctx.translate(this.panX, this.panY);
        ctx.drawImage(src, 0, 0, w, h);
        ctx.restore();
    }

    saveSnapshot() {
        if (!this.processedCanvas) return;
        this.undoStack.push(this.processedCanvas.toDataURL());
        if (this.undoStack.length > this.maxUndo) this.undoStack.shift();
        this.redoStack = [];
    }

    restoreFromDataURL(src) {
        const img = new Image();
        img.onload = () => {
            this.processedCanvas.width = img.width;
            this.processedCanvas.height = img.height;
            this.processedCanvas.getContext('2d').drawImage(img, 0, 0);
            this.updateDisplay();
        };
        img.src = src;
    }

    undo() {
        if (this.undoStack.length === 0) return;
        this.redoStack.push(this.processedCanvas.toDataURL());
        this.restoreFromDataURL(this.undoStack.pop());
    }

    redo() {
        if (this.redoStack.length === 0) return;
        this.undoStack.push(this.processedCanvas.toDataURL());
        this.restoreFromDataURL(this.redoStack.pop());
    }

    zoomIn() {
        this.zoomLevel *= 1.25;
        this.updateDisplay();
    }

    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.25, 0.1);
        this.updateDisplay();
    }

    zoomReset() {
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.updateDisplay();
    }

    getImageCoords(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = clientX - rect.left;
        const canvasY = clientY - rect.top;
        return {
            x: Math.floor((canvasX - this.panX) / this.zoomLevel),
            y: Math.floor((canvasY - this.panY) / this.zoomLevel)
        };
    }

    onMouseDown(e) {
        const mode = document.getElementById('mouseMode').value;

        if (mode === 'Drag') {
            if (!this.image) return;
            this.dragging = true;
            this.dragStartX = e.clientX;
            this.dragStartY = e.clientY;
            this.dragPanX = this.panX;
            this.dragPanY = this.panY;
        } else if (mode === 'Random Color') {
            this.clickContour(e, true);
        } else if (mode === 'Paint Color') {
            this.clickContour(e, false);
        } else if (mode === 'Pick Color') {
            this.clickPickColor(e);
        }
    }

    onMouseMove(e) {
        if (!this.dragging) return;
        const dx = e.clientX - this.dragStartX;
        const dy = e.clientY - this.dragStartY;
        this.panX = this.dragPanX + dx;
        this.panY = this.dragPanY + dy;
        this.updateDisplay();
    }

    onMouseUp() {
        this.dragging = false;
    }

    onWheel(e) {
        e.preventDefault();
        if (e.deltaY < 0) this.zoomIn();
        else this.zoomOut();
    }

    clickContour(e, randomColor) {
        if (!this.processedCanvas || !this.components) return;
        this.saveSnapshot();

        const coords = this.getImageCoords(e.clientX, e.clientY);
        const imgX = coords.x, imgY = coords.y;

        const ctx = this.processedCanvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, this.processedCanvas.width, this.processedCanvas.height);
        const data = imageData.data;

        for (const component of this.components) {
            let hit = false;
            for (const p of component) {
                if (p.x === imgX && p.y === imgY) { hit = true; break; }
            }
            if (hit) {
                const color = randomColor
                    ? {r: Math.floor(Math.random() * 256), g: Math.floor(Math.random() * 256), b: Math.floor(Math.random() * 256), a: 255}
                    : this.selectedColor;
                for (const p of component) {
                    const idx = (p.y * imageData.width + p.x) * 4;
                    data[idx] = color.r;
                    data[idx + 1] = color.g;
                    data[idx + 2] = color.b;
                    data[idx + 3] = color.a;
                }
                if (document.getElementById('viewMode').value === 'Contours') {
                    const boundaries = ImageProcessor.findBoundaries(component, imageData.width, imageData.height);
                    for (const p of boundaries) {
                        const idx = (p.y * imageData.width + p.x) * 4;
                        data[idx] = 0;
                        data[idx + 1] = 0;
                        data[idx + 2] = 0;
                        data[idx + 3] = 255;
                    }
                }
                ctx.putImageData(imageData, 0, 0);
                this.updateDisplay();
                return;
            }
        }
    }

    clickPickColor(e) {
        if (!this.processedCanvas) return;
        const coords = this.getImageCoords(e.clientX, e.clientY);
        const imgX = coords.x, imgY = coords.y;
        if (imgX < 0 || imgX >= this.processedCanvas.width || imgY < 0 || imgY >= this.processedCanvas.height) return;

        const pixel = this.processedCanvas.getContext('2d').getImageData(imgX, imgY, 1, 1).data;

        this.selectedColor = {r: pixel[0], g: pixel[1], b: pixel[2], a: pixel[3]};
        document.getElementById('rInput').value = pixel[0];
        document.getElementById('gInput').value = pixel[1];
        document.getElementById('bInput').value = pixel[2];
        document.getElementById('aInput').value = pixel[3];
        this.updateColorPreview();
    }

    pickColorDialog() {
        const input = document.createElement('input');
        input.type = 'color';
        input.value = '#' + [this.selectedColor.r, this.selectedColor.g, this.selectedColor.b]
            .map(v => v.toString(16).padStart(2, '0')).join('');
        input.addEventListener('input', () => {
            const hex = input.value;
            this.selectedColor.r = parseInt(hex.slice(1, 3), 16);
            this.selectedColor.g = parseInt(hex.slice(3, 5), 16);
            this.selectedColor.b = parseInt(hex.slice(5, 7), 16);
            document.getElementById('rInput').value = this.selectedColor.r;
            document.getElementById('gInput').value = this.selectedColor.g;
            document.getElementById('bInput').value = this.selectedColor.b;
            this.updateColorPreview();
        });
        input.click();
    }

    updateColorFromInputs() {
        const get = id => Math.min(255, Math.max(0, parseInt(document.getElementById(id).value) || 0));
        this.selectedColor = {
            r: get('rInput'), g: get('gInput'), b: get('bInput'), a: get('aInput')
        };
        this.updateColorPreview();
    }

    updateColorPreview() {
        const el = document.getElementById('colorPreview');
        el.style.backgroundColor = `rgba(${this.selectedColor.r},${this.selectedColor.g},${this.selectedColor.b},${this.selectedColor.a / 255})`;
    }

    resizeImage() {
        if (!this.originalImage) return;
        const w = parseInt(document.getElementById('widthInput').value);
        const h = parseInt(document.getElementById('heightInput').value);
        if (w > 0 && h > 0) {
            this.image = ImageProcessor.resizeImage(this.originalImage, w, h);
            this.computeView();
            this.updateDisplay();
            this.updateInfo();
        }
    }

    saveImage() {
        if (!this.image) return;
        const canvas = document.createElement('canvas');
        canvas.width = this.image.width;
        canvas.height = this.image.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.image, 0, 0);
        const link = document.createElement('a');
        link.href = canvas.toDataURL('image/png');
        link.download = 'image.png';
        link.click();
    }

    saveView() {
        if (!this.processedCanvas) return;
        const link = document.createElement('a');
        link.href = this.processedCanvas.toDataURL('image/png');
        link.download = 'view.png';
        link.click();
    }

    updateInfo() {
        if (this.image) {
            document.getElementById('info').textContent =
                `Image: ${this.image.width}x${this.image.height}px`;
        } else {
            document.getElementById('info').textContent = 'No image loaded';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ImagePainter();
});
