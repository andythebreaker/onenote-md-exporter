const fs = require('fs');

/**
 * Test Quoted-Printable decoding with Chinese characters
 */
function testQuotedPrintableDecoding() {
    console.log('=== Quoted-Printable 解碼測試 ===\n');
    
    // Test case 1: Simple Chinese text with soft line breaks
    const testCase1 = '這是一個測試=\r\n中文字符的=\r\n編碼範例';
    console.log('測試案例 1 - 簡單軟換行:');
    console.log('輸入:', JSON.stringify(testCase1));
    console.log('輸出:', decodeQuotedPrintableBinary(testCase1).toString('utf8'));
    console.log('');
    
    // Test case 2: UTF-8 encoded Chinese with hex sequences and soft breaks
    const testCase2 = 'Hello =E4=B8=AD=\r\n=E6=96=87 World';
    console.log('測試案例 2 - UTF-8 十六進制編碼 + 軟換行:');
    console.log('輸入:', JSON.stringify(testCase2));
    console.log('輸出:', decodeQuotedPrintableBinary(testCase2).toString('utf8'));
    console.log('');
    
    // Test case 3: Complex case with Chinese characters broken by soft line breaks
    const testCase3 = '皮膚科=\r\n醫學知識=\r\n網站架設';
    console.log('測試案例 3 - 中文字符被軟換行分割:');
    console.log('輸入:', JSON.stringify(testCase3));
    console.log('輸出:', decodeQuotedPrintableBinary(testCase3).toString('utf8'));
    console.log('');
    
    // Test case 4: UTF-8 bytes split across soft line breaks
    const testCase4 = '=E7=9A=AE=\r\n=E8=86=9A=\r\n=E7=A7=91'; // 皮膚科 in UTF-8
    console.log('測試案例 4 - UTF-8 字節被軟換行分割:');
    console.log('輸入:', JSON.stringify(testCase4));
    console.log('輸出:', decodeQuotedPrintableBinary(testCase4).toString('utf8'));
    console.log('');
    
    // Test case 5: Mixed content
    const testCase5 = 'Subject: =E5=9C=8B=E8=80=83=\r\n=E4=B8=AD=E6=96=87=E9=86=AB=E5=AD=B8'; // 國考中文醫學
    console.log('測試案例 5 - 混合內容:');
    console.log('輸入:', JSON.stringify(testCase5));
    console.log('輸出:', decodeQuotedPrintableBinary(testCase5).toString('utf8'));
    console.log('');
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
 * Test with actual MHT file if available
 */
function testWithMhtFile() {
    console.log('=== 實際 MHT 文件測試 ===\n');
    
    const currentDir = __dirname;
    const files = fs.readdirSync(currentDir);
    const mhtFiles = files.filter(file => file.endsWith('.mht'));
    
    if (mhtFiles.length === 0) {
        console.log('當前目錄中未找到 MHT 文件。');
        return;
    }
    
    const testFile = mhtFiles[0];
    console.log(`測試文件: ${testFile}`);
    
    try {
        const content = fs.readFileSync(testFile, 'utf8');
        
        // Look for quoted-printable content
        const qpMatches = content.match(/Content-Transfer-Encoding:\s*quoted-printable/gi);
        if (qpMatches) {
            console.log(`找到 ${qpMatches.length} 個 quoted-printable 編碼的部分`);
            
            // Find soft line breaks
            const softBreaks = content.match(/=[^\r\n]*[\r\n]/g);
            if (softBreaks) {
                console.log(`找到 ${softBreaks.length} 個軟換行`);
                console.log('軟換行示例:', softBreaks.slice(0, 5));
            }
        } else {
            console.log('未找到 quoted-printable 編碼的內容');
        }
        
    } catch (error) {
        console.error(`讀取文件錯誤: ${error.message}`);
    }
}

// Run tests
if (require.main === module) {
    testQuotedPrintableDecoding();
    testWithMhtFile();
}

module.exports = {
    testQuotedPrintableDecoding,
    testWithMhtFile,
    decodeQuotedPrintableBinary
};
