# Image Painter - Web Version

A web-based image composition and editing tool that works on GitHub Pages.

## Features

- Load background and foreground images
- Drag layers to reposition (foreground, background, or result)
- Resize individual components
- Multiple view modes:
  - BGR: Full color display
  - Grayscale: Convert to grayscale
  - Binary: Black/white with threshold at 127
  - Contours: Detect and color contours with random colors
- Real-time preview
- Save result as PNG
- Responsive design

## Usage

### Local Development

Simply open `index.html` in a web browser. All processing is done client-side.

### GitHub Pages Deployment

1. Copy the `web` folder contents to your GitHub Pages repository
2. Access via your GitHub Pages URL

### How to Use

1. **Load Images**: Click "Load Background" and "Load Foreground" to select images
2. **Reposition**: Select a drag mode and click-drag on the canvas to move elements
3. **Resize**: Enter width/height values and click "Resize BG", "Resize FG", or "Resize Result"
4. **Change View**: Use the "View Mode" dropdown to switch between different representations
5. **Save**: Click "Save Result" to download the composite image as PNG

## File Structure

```
web/
├── index.html              # Main HTML
├── css/
│   └── style.css          # Styling
└── js/
    ├── main.js            # Main application logic
    └── imageprocessing.js # Image processing utilities
```

## Technical Details

- Pure client-side JavaScript (no server required)
- Uses HTML5 Canvas API for image manipulation
- No external image processing library dependencies
- Works in all modern browsers

## Limitations

- Contour detection is simplified compared to OpenCV
- Processing large images may be slower due to JavaScript performance
- All image processing happens in the browser
