import { chromium } from 'playwright';
import fs from 'fs';
const b=await chromium.launch();
const ctx=await b.newContext({viewport:{width:1440,height:1000}});
await ctx.addInitScript(()=>{ localStorage.setItem('d2r_chronicleInbox', JSON.stringify([
  {name:'Annihilus', triageWhy:'only 0 independent witnesses (none) — needs 2'},
  {name:'Gorefoot', triageWhy:'the second eye disagreed with this read'}]));
});
const p=await ctx.newPage();
await p.route(u=>/fonts\.(googleapis|gstatic)\.com/.test(u.host), r=>r.fulfill({status:200,body:''}));
await p.goto('file:///Users/konyo/d2r_bible_tests/bible.html');
await p.waitForTimeout(3000);
await p.evaluate(()=>{ window.switchTab('tools');
  const bar=document.getElementById('routine-status-bar'); if(bar) bar.style.setProperty('display','none','important'); });
await p.waitForTimeout(800);
await p.evaluate(()=>document.getElementById('inbox-card').scrollIntoView({block:'center'}));
await p.waitForTimeout(1000);
const r=await p.evaluate(()=>{ const c=document.getElementById('inbox-card').getBoundingClientRect();
  return {y:Math.round(c.y),h:Math.round(c.height)}; });
console.log(JSON.stringify(r));
const cdp=await ctx.newCDPSession(p);
const {data}=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
fs.writeFileSync(process.env.CLAUDE_JOB_DIR+'/tmp/badge3.png', Buffer.from(data,'base64'));
const y=r.y;
await b.close();
console.log('crop y', Math.max(0,y-12), 'to', y+r.h+12);
