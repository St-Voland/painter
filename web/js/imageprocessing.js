// Image Processing Utilities

class ImageProcessor {
    static loadImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = reject;
                img.src = e.target.result;
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    static drawImageToCanvas(canvas, img, offsetX = 0, offsetY = 0) {
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, offsetX, offsetY);
    }

    static resizeImage(img, width, height) {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        const newImg = new Image();
        newImg.src = canvas.toDataURL();
        return newImg;
    }

    static getImageData(canvas) {
        return canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
    }

    static putImageData(canvas, imageData) {
        canvas.getContext('2d').putImageData(imageData, 0, 0);
    }

    static convertToGrayscale(imageData) {
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            data[i] = gray;
            data[i + 1] = gray;
            data[i + 2] = gray;
        }
        return imageData;
    }

    static convertToBinary(imageData, threshold = 127) {
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
            const binary = gray < threshold ? 0 : 255;
            data[i] = binary;
            data[i + 1] = binary;
            data[i + 2] = binary;
        }
        return imageData;
    }

    static findContours(imageData) {
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        const visited = new Set();
        const contours = [];

        // Simple contour detection using flood fill
        for (let i = 0; i < data.length; i += 4) {
            const pixelIndex = i / 4;
            if (data[i] > 127 && !visited.has(pixelIndex)) {
                const contour = this.floodFill(data, width, height, pixelIndex, visited);
                if (contour.length > 10) { // Filter small contours
                    contours.push(contour);
                }
            }
        }
        return contours;
    }

    static floodFill(data, width, height, startIndex, visited) {
        const stack = [startIndex];
        const contour = [];
        const x0 = startIndex % width;
        const y0 = Math.floor(startIndex / width);

        while (stack.length > 0) {
            const index = stack.pop();
            if (visited.has(index)) continue;

            const x = index % width;
            const y = Math.floor(index / width);

            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            if (data[index * 4] <= 127) continue;

            visited.add(index);
            contour.push({x, y});

            // Add neighbors
            if (x + 1 < width) stack.push(index + 1);
            if (x - 1 >= 0) stack.push(index - 1);
            if (y + 1 < height) stack.push(index + width);
            if (y - 1 >= 0) stack.push(index - width);
        }

        return contour;
    }

    static calculateContourArea(contour) {
        if (contour.length < 3) return 0;
        let area = 0;
        for (let i = 0; i < contour.length; i++) {
            const current = contour[i];
            const next = contour[(i + 1) % contour.length];
            area += (current.x * next.y) - (next.x * current.y);
        }
        return Math.abs(area) / 2;
    }

    static drawContoursWithColors(imageData, contours) {
        const data = imageData.data;
        
        // Clear to white
        for (let i = 0; i < data.length; i += 4) {
            data[i] = 255;
            data[i + 1] = 255;
            data[i + 2] = 255;
            data[i + 3] = 255;
        }

        // Draw each contour with random color
        contours.forEach((contour, idx) => {
            const r = Math.floor(Math.random() * 256);
            const g = Math.floor(Math.random() * 256);
            const b = Math.floor(Math.random() * 256);

            contour.forEach((point) => {
                const index = (point.y * imageData.width + point.x) * 4;
                if (index >= 0 && index < data.length) {
                    data[index] = r;
                    data[index + 1] = g;
                    data[index + 2] = b;
                    data[index + 3] = 255;
                }
            });
        });

        return imageData;
    }

    static getImageDimensions(img) {
        return { width: img.width, height: img.height };
    }

    static canvasToImage(canvas) {
        const img = new Image();
        img.src = canvas.toDataURL();
        return img;
    }
}
