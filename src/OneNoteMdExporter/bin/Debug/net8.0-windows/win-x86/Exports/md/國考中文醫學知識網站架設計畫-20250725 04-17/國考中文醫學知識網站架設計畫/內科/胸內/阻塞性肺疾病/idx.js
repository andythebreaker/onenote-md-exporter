const fs = require('fs');
const mhtml2html = require('mhtml2html');

const input = fs.readFileSync('COPD.mht', 'utf8');

mhtml2html(input).then(result => {
  fs.writeFileSync('COPD.html', result.html, 'utf8');
  console.log('已轉換成 HTML');

  // 若有附加資源
  if (result.attachments && result.attachments.length > 0) {
    for (const attachment of result.attachments) {
      fs.writeFileSync(attachment.filename, attachment.content);
    }
    console.log('附件已儲存');
  }
});
