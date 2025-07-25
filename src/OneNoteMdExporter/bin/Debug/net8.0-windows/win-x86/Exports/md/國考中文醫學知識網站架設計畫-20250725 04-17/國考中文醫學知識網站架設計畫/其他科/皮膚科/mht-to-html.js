const fs = require('fs');
const path = require('path');

/**
 * Convert MHT (MHTML) file to HTML
 * @param {string} mhtFilePath - Path to the MHT file
 * @param {string} outputDir - Directory to save the HTML file and assets
 * @returns {Promise<string>} - Path to the created HTML file
 */
async function mhtToHtml(mhtFilePath, outputDir = null) {
    try {
        // Read the MHT file
        const mhtContent = fs.readFileSync(mhtFilePath, 'utf8');
        
        // Parse the MHT content
        const parsed = parseMHT(mhtContent);
        
        // Set output directory
        if (!outputDir) {
            outputDir = path.dirname(mhtFilePath);
        }
        
        // Ensure output directory exists
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        // Create HTML file name
        const baseName = path.basename(mhtFilePath, path.extname(mhtFilePath));
        const htmlFilePath = path.join(outputDir, `${baseName}.html`);
        
        // Process and save assets
        let htmlContent = parsed.html;
        
        for (const asset of parsed.assets) {
            // Save asset file
            const assetFileName = asset.filename || `asset_${asset.id}${getExtensionFromContentType(asset.contentType)}`;
            const assetFilePath = path.join(outputDir, assetFileName);
            
            // Write asset file (decode base64 if needed)
            if (asset.encoding === 'base64') {
                fs.writeFileSync(assetFilePath, Buffer.from(asset.content, 'base64'));
            } else {
                fs.writeFileSync(assetFilePath, asset.content);
            }
            
            // Replace references in HTML
            if (asset.cid) {
                htmlContent = htmlContent.replace(new RegExp(`cid:${asset.cid}`, 'g'), assetFileName);
            }
            if (asset.location) {
                htmlContent = htmlContent.replace(new RegExp(escapeRegExp(asset.location), 'g'), assetFileName);
            }
        }
        
        // Write HTML file
        fs.writeFileSync(htmlFilePath, htmlContent);
        
        console.log(`Converted ${mhtFilePath} to ${htmlFilePath}`);
        return htmlFilePath;
        
    } catch (error) {
        console.error(`Error converting MHT to HTML: ${error.message}`);
        throw error;
    }
}

/**
 * Decode Quoted-Printable content
 * @param {string} content - Quoted-Printable encoded content
 * @returns {string} - Decoded content
 */
function decodeQuotedPrintable(content) {
    // First, handle soft line breaks (=\r\n or =\n)
    // Remove soft line breaks which are represented by = at end of line
    content = content.replace(/=\r?\n/g, '');
    
    // Then decode =XX hex sequences
    content = content.replace(/=([0-9A-F]{2})/gi, (match, hex) => {
        return String.fromCharCode(parseInt(hex, 16));
    });
    
    return content;
}

/**
 * Decode Quoted-Printable content with proper binary handling for UTF-8
 * @param {string} content - Quoted-Printable encoded content
 * @returns {Buffer} - Decoded content as Buffer
 */
function decodeQuotedPrintableBinary(content) {
    // Remove soft line breaks (= followed by CRLF or LF)
    // This is crucial for preserving UTF-8 multi-byte sequences
    content = content.replace(/=(?:\r\n|\r|\n)/g, '');
    
    // Convert to binary data
    const bytes = [];
    let i = 0;
    
    while (i < content.length) {
        if (content[i] === '=' && i + 2 < content.length) {
            // Decode =XX hex sequence
            const hex = content.substring(i + 1, i + 3);
            if (/^[0-9A-F]{2}$/i.test(hex)) {
                bytes.push(parseInt(hex, 16));
                i += 3;
            } else {
                // Invalid hex sequence, keep as is
                bytes.push(content.charCodeAt(i));
                i++;
            }
        } else {
            // Regular character
            bytes.push(content.charCodeAt(i));
            i++;
        }
    }
    
    return Buffer.from(bytes);
}

/**
 * Parse MHT content into HTML and assets
 * @param {string} mhtContent - Raw MHT file content
 * @returns {Object} - Parsed content with html and assets
 */
function parseMHT(mhtContent) {
    const parts = [];
    let currentPart = null;
    let inHeaders = true;
    let boundary = null;
    
    // Find the boundary
    const boundaryMatch = mhtContent.match(/boundary="([^"]+)"/i);
    if (boundaryMatch) {
        boundary = boundaryMatch[1];
    }
    
    const lines = mhtContent.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check for boundary
        if (boundary && line.includes(`--${boundary}`)) {
            if (currentPart) {
                // Process the content based on encoding before adding to parts
                if (currentPart.encoding && currentPart.encoding.toLowerCase() === 'quoted-printable') {
                    if (currentPart.contentType.startsWith('text/')) {
                        // For text content, decode to string with proper UTF-8 handling
                        const buffer = decodeQuotedPrintableBinary(currentPart.content);
                        currentPart.content = buffer.toString('utf8');
                    } else {
                        // For binary content, keep as decoded buffer
                        const buffer = decodeQuotedPrintableBinary(currentPart.content);
                        currentPart.content = buffer.toString('base64');
                        currentPart.encoding = 'base64'; // Mark as base64 for later processing
                    }
                }
                parts.push(currentPart);
            }
            currentPart = {
                headers: {},
                content: '',
                contentType: '',
                encoding: '',
                location: '',
                cid: '',
                filename: ''
            };
            inHeaders = true;
            continue;
        }
        
        if (!currentPart) continue;
        
        if (inHeaders) {
            if (line.trim() === '') {
                inHeaders = false;
                continue;
            }
            
            // Parse headers
            const headerMatch = line.match(/^([^:]+):\s*(.+)$/);
            if (headerMatch) {
                const headerName = headerMatch[1].toLowerCase();
                const headerValue = headerMatch[2].trim();
                
                currentPart.headers[headerName] = headerValue;
                
                if (headerName === 'content-type') {
                    currentPart.contentType = headerValue.split(';')[0].trim();
                }
                if (headerName === 'content-transfer-encoding') {
                    currentPart.encoding = headerValue;
                }
                if (headerName === 'content-location') {
                    currentPart.location = headerValue;
                }
                if (headerName === 'content-id') {
                    currentPart.cid = headerValue.replace(/[<>]/g, '');
                }
                
                // Extract filename from content-type or content-disposition
                const filenameMatch = headerValue.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/i);
                if (filenameMatch) {
                    currentPart.filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
        } else {
            currentPart.content += line + '\n';
        }
    }
    
    // Add the last part
    if (currentPart) {
        // Process the content based on encoding before adding to parts
        if (currentPart.encoding && currentPart.encoding.toLowerCase() === 'quoted-printable') {
            if (currentPart.contentType.startsWith('text/')) {
                // For text content, decode to string with proper UTF-8 handling
                const buffer = decodeQuotedPrintableBinary(currentPart.content);
                currentPart.content = buffer.toString('utf8');
            } else {
                // For binary content, keep as decoded buffer
                const buffer = decodeQuotedPrintableBinary(currentPart.content);
                currentPart.content = buffer.toString('base64');
                currentPart.encoding = 'base64'; // Mark as base64 for later processing
            }
        }
        parts.push(currentPart);
    }
    
    // Find HTML part and assets
    let htmlPart = null;
    const assets = [];
    
    for (const part of parts) {
        if (part.contentType.includes('text/html')) {
            htmlPart = part;
        } else if (part.contentType.startsWith('image/') || 
                   part.contentType.startsWith('text/css') ||
                   part.contentType.startsWith('application/') ||
                   part.contentType.startsWith('font/')) {
            assets.push({
                id: assets.length,
                content: part.content.trim(),
                contentType: part.contentType,
                encoding: part.encoding,
                location: part.location,
                cid: part.cid,
                filename: part.filename
            });
        }
    }
    
    return {
        html: htmlPart ? htmlPart.content.trim() : '',
        assets: assets
    };
}

/**
 * Get file extension from content type
 * @param {string} contentType - MIME content type
 * @returns {string} - File extension
 */
function getExtensionFromContentType(contentType) {
    const extensions = {
        'text/html': '.html',
        'text/css': '.css',
        'text/javascript': '.js',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/svg+xml': '.svg',
        'application/pdf': '.pdf',
        'font/woff': '.woff',
        'font/woff2': '.woff2',
        'font/ttf': '.ttf',
        'font/otf': '.otf'
    };
    
    return extensions[contentType.toLowerCase()] || '.bin';
}

/**
 * Escape string for use in regular expression
 * @param {string} string - String to escape
 * @returns {string} - Escaped string
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Convert all MHT files in a directory to HTML
 * @param {string} inputDir - Directory containing MHT files
 * @param {string} outputDir - Directory to save HTML files (optional)
 */
async function convertAllMhtFiles(inputDir, outputDir = null) {
    try {
        const files = fs.readdirSync(inputDir);
        const mhtFiles = files.filter(file => path.extname(file).toLowerCase() === '.mht');
        
        console.log(`Found ${mhtFiles.length} MHT files to convert...`);
        
        for (const mhtFile of mhtFiles) {
            const mhtFilePath = path.join(inputDir, mhtFile);
            const targetOutputDir = outputDir || inputDir;
            
            try {
                await mhtToHtml(mhtFilePath, targetOutputDir);
            } catch (error) {
                console.error(`Failed to convert ${mhtFile}: ${error.message}`);
            }
        }
        
        console.log('Conversion completed!');
    } catch (error) {
        console.error(`Error reading directory: ${error.message}`);
    }
}

// Export functions
module.exports = {
    mhtToHtml,
    convertAllMhtFiles
};

// Command line usage
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Usage:');
        console.log('  node mht-to-html.js <mht-file-path> [output-directory]');
        console.log('  node mht-to-html.js --dir <input-directory> [output-directory]');
        console.log('');
        console.log('Examples:');
        console.log('  node mht-to-html.js example.mht');
        console.log('  node mht-to-html.js example.mht ./output');
        console.log('  node mht-to-html.js --dir ./mht-files ./html-files');
        process.exit(1);
    }
    
    if (args[0] === '--dir') {
        // Convert all MHT files in directory
        const inputDir = args[1];
        const outputDir = args[2] || null;
        
        if (!inputDir || !fs.existsSync(inputDir)) {
            console.error('Input directory does not exist!');
            process.exit(1);
        }
        
        convertAllMhtFiles(inputDir, outputDir);
    } else {
        // Convert single file
        const mhtFilePath = args[0];
        const outputDir = args[1] || null;
        
        if (!fs.existsSync(mhtFilePath)) {
            console.error('MHT file does not exist!');
            process.exit(1);
        }
        
        mhtToHtml(mhtFilePath, outputDir)
            .then(htmlPath => {
                console.log(`Successfully converted to: ${htmlPath}`);
            })
            .catch(error => {
                console.error(`Conversion failed: ${error.message}`);
                process.exit(1);
            });
    }
}
