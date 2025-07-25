# MHT to HTML Converter

A Node.js utility to convert MHT (MHTML) files to standard HTML format with extracted assets.

## Features

- Convert single MHT files to HTML
- Batch convert all MHT files in a directory
- Extract and save embedded assets (images, CSS, fonts, etc.)
- Preserve file structure and references
- Support for base64 encoded assets
- Command-line interface

## Installation

No external dependencies required. This tool uses only Node.js built-in modules.

```bash
# Clone or download the files to your project directory
# Ensure you have Node.js installed (version 12 or higher)
```

## Usage

### Command Line

#### Convert a single MHT file:
```bash
node mht-to-html.js <mht-file-path> [output-directory]
```

Examples:
```bash
# Convert to same directory
node mht-to-html.js example.mht

# Convert to specific output directory
node mht-to-html.js example.mht ./output

# Convert MHT file with Chinese filename
node mht-to-html.js "乾癬.mht"
```

#### Convert all MHT files in a directory:
```bash
node mht-to-html.js --dir <input-directory> [output-directory]
```

Examples:
```bash
# Convert all MHT files in current directory
node mht-to-html.js --dir .

# Convert all MHT files to specific output directory
node mht-to-html.js --dir ./mht-files ./html-output
```

### Programmatic Usage

```javascript
const { mhtToHtml, convertAllMhtFiles } = require('./mht-to-html');

// Convert single file
async function convertSingle() {
    try {
        const htmlPath = await mhtToHtml('example.mht', './output');
        console.log('Converted to:', htmlPath);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Convert all MHT files in directory
async function convertAll() {
    try {
        await convertAllMhtFiles('./mht-files', './html-output');
        console.log('All files converted!');
    } catch (error) {
        console.error('Error:', error.message);
    }
}
```

### NPM Scripts

```bash
# Run test conversion
npm test

# Convert all MHT files in current directory
npm run convert-all
```

## How it Works

1. **Parsing**: The tool reads the MHT file and parses the MIME multipart structure
2. **Content Extraction**: Separates HTML content from embedded assets (images, CSS, etc.)
3. **Asset Handling**: Saves embedded assets as separate files
4. **Reference Updates**: Updates HTML references to point to extracted asset files
5. **Output**: Creates a clean HTML file with properly linked assets

## Supported Asset Types

- Images: JPEG, PNG, GIF, SVG
- Stylesheets: CSS files
- Scripts: JavaScript files
- Fonts: WOFF, WOFF2, TTF, OTF
- Documents: PDF and other binary files

## File Structure After Conversion

```
input-directory/
├── example.mht          # Original MHT file
├── example.html         # Converted HTML file
├── image1.jpg           # Extracted image
├── style.css            # Extracted stylesheet
└── font.woff           # Extracted font
```

## Error Handling

The tool includes comprehensive error handling for:
- Invalid MHT file format
- Missing or corrupted assets
- File system permission issues
- Encoding problems

## Limitations

- Some complex MHT files with non-standard formatting may not parse correctly
- Very large MHT files may require significant memory
- Some proprietary Microsoft-specific features may not be preserved

## Troubleshooting

### Common Issues

1. **"File not found" error**: Ensure the MHT file path is correct
2. **Permission denied**: Check file/directory permissions
3. **Partial conversion**: Some MHT files use non-standard formats

### Debug Mode

For debugging, you can modify the code to add more verbose logging:
```javascript
// Add this line at the top of mht-to-html.js for debugging
console.log('Debug mode enabled');
```

## License

MIT License - feel free to use and modify as needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Requirements

- Node.js 12.0.0 or higher
- No external dependencies
