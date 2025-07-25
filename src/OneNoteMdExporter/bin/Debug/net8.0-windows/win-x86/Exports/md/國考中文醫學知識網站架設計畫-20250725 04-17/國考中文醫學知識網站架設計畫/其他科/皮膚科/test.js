const { mhtToHtml, convertAllMhtFiles } = require('./mht-to-html');
const fs = require('fs');
const path = require('path');

// Test the MHT to HTML converter
async function runTests() {
    console.log('=== MHT to HTML Converter Test ===\n');
    
    // Get current directory
    const currentDir = __dirname;
    
    // Find MHT files in current directory
    const files = fs.readdirSync(currentDir);
    const mhtFiles = files.filter(file => path.extname(file).toLowerCase() === '.mht');
    
    if (mhtFiles.length === 0) {
        console.log('No MHT files found in current directory.');
        return;
    }
    
    console.log(`Found ${mhtFiles.length} MHT file(s):`);
    mhtFiles.forEach((file, index) => {
        console.log(`  ${index + 1}. ${file}`);
    });
    console.log('');
    
    // Test converting the first MHT file
    const testFile = path.join(currentDir, mhtFiles[0]);
    
    try {
        console.log(`Converting: ${mhtFiles[0]}`);
        const htmlFile = await mhtToHtml(testFile);
        console.log(`✓ Successfully converted to: ${path.basename(htmlFile)}`);
        
        // Check if HTML file was created
        if (fs.existsSync(htmlFile)) {
            const stats = fs.statSync(htmlFile);
            console.log(`  File size: ${(stats.size / 1024).toFixed(2)} KB`);
        }
        
    } catch (error) {
        console.error(`✗ Conversion failed: ${error.message}`);
    }
    
    console.log('\n=== Batch Conversion Test ===');
    
    // Test batch conversion
    try {
        console.log('Converting all MHT files in current directory...');
        await convertAllMhtFiles(currentDir);
        console.log('✓ Batch conversion completed!');
    } catch (error) {
        console.error(`✗ Batch conversion failed: ${error.message}`);
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    runTests().catch(console.error);
}

module.exports = { runTests };
