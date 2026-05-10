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
            const val = gray < threshold ? 0 : 255;
            data[i] = val;
            data[i + 1] = val;
            data[i + 2] = val;
        }
        return imageData;
    }

    static findComponents(imageData) {
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        const visited = new Uint8Array(width * height);
        const components = [];

        for (let i = 0; i < data.length; i += 4) {
            const idx = i / 4;
            if (data[i] > 127 && !visited[idx]) {
                const pixels = this.floodFill(data, width, height, idx, visited);
                if (pixels.length > 10) {
                    components.push(pixels);
                }
            }
        }
        return components;
    }

    static floodFill(data, width, height, startIndex, visited) {
        const stack = [startIndex];
        const pixels = [];

        while (stack.length > 0) {
            const idx = stack.pop();
            if (visited[idx]) continue;
            const x = idx % width;
            const y = Math.floor(idx / width);
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            if (data[idx * 4] <= 127) continue;
            visited[idx] = 1;
            pixels.push({x, y});
            if (x + 1 < width) stack.push(idx + 1);
            if (x - 1 >= 0) stack.push(idx - 1);
            if (y + 1 < height) stack.push(idx + width);
            if (y - 1 >= 0) stack.push(idx - width);
        }
        return pixels;
    }

    static findBoundaries(component, width, height) {
        const pixelSet = new Set(component.map(p => `${p.x},${p.y}`));
        const boundaries = [];
        for (const p of component) {
            const x = p.x, y = p.y;
            if (!pixelSet.has(`${x + 1},${y}`) || !pixelSet.has(`${x - 1},${y}`) ||
                !pixelSet.has(`${x},${y + 1}`) || !pixelSet.has(`${x},${y - 1}`)) {
                boundaries.push(p);
            }
        }
        return boundaries;
    }

    static drawComponents(imageData, components, colorFn) {
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            data[i] = 0;
            data[i + 1] = 0;
            data[i + 2] = 0;
            data[i + 3] = 255;
        }
        for (const component of components) {
            const {r, g, b, a} = colorFn();
            for (const p of component) {
                const idx = (p.y * imageData.width + p.x) * 4;
                data[idx] = r;
                data[idx + 1] = g;
                data[idx + 2] = b;
                data[idx + 3] = a;
            }
        }
        return imageData;
    }

    static drawBoundaries(imageData, components) {
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        for (const component of components) {
            const boundaries = this.findBoundaries(component, width, height);
            for (const p of boundaries) {
                const idx = (p.y * width + p.x) * 4;
                data[idx] = 0;
                data[idx + 1] = 0;
                data[idx + 2] = 0;
                data[idx + 3] = 255;
            }
        }
        return imageData;
    }
}
