#!/usr/bin/env node
// Print the committed, offline HTML manual. No live application or credential is used.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {chromium}=require(path.resolve(__dirname,'../../units/consumers/dashboard-core/browser-tests/node_modules/playwright'));
const directory=path.resolve(__dirname,'../../docs/manual');
const source=path.join(directory,'PROJECT_MANUAL.html');
const output=path.join(directory,'PROJECT_MANUAL.pdf');
const binary=process.env.CHROME_BIN || ['chromium','google-chrome','google-chrome-stable'].map(name=>{
 try{return execFileSync('which',[name],{encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim();}catch{return null;}
}).find(Boolean);
(async()=>{
 if(!binary)throw new Error('Local Chrome/Chromium is required');
 const browser=await chromium.launch({executablePath:binary,headless:true});
 try{
  const page=await browser.newPage();
  // The manual has no remote CSS/fonts/scripts. Links remain clickable but are not fetched.
  await page.route('http://**/*',route=>route.abort());
  await page.route('https://**/*',route=>route.abort());
  await page.setContent(fs.readFileSync(source,'utf8'),{waitUntil:'load'});
  await page.pdf({path:output,format:'A4',printBackground:true,preferCSSPageSize:true,
   tagged:true,outline:true,displayHeaderFooter:true,
   headerTemplate:'<div></div>',
   footerTemplate:'<div style="font-size:9px;width:100%;text-align:center;color:#596579"><span class="pageNumber"></span> / <span class="totalPages"></span> — 30nA Project Manual</div>'});
  const digest=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  fs.writeFileSync(path.join(directory,'pdf-manifest.json'),JSON.stringify({
   html_sha256:digest(source),pdf_sha256:digest(output),bytes:fs.statSync(output).size,
   renderer:'Playwright 1.62.1 with host Chromium; offline HTML printing'
  },null,2)+'\n');
  console.log('PDF written; source and output checksums recorded');
 }finally{await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
