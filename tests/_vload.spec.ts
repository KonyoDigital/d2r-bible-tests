import { test } from '@playwright/test';
test('shot', async ({ page }) => {
  await page.setViewportSize({ width:1400, height:900 });
  await page.goto('file://'+process.cwd()+'/bible.html');
  await page.waitForFunction(()=>(window as any).switchTab);
  await page.evaluate(()=>(window as any).switchTab('tools'));
  await page.waitForTimeout(400);
  await page.evaluate(()=>{
    const r=document.getElementById('vault-intake-report'); if(!r)return;
    r.hidden=false;
    const verbs=['Reading','Scanning','Analyzing','Matching']; const done=37,total=62,nw=11,pct=Math.round(done/total*100),verb=verbs[done%4];
    r.innerHTML='<div class="ai-load vintake-ai"><div class="ai-load-orb">📸</div><div class="ai-load-body">'
      +'<div class="ai-load-title">'+verb+' your loot<span class="ai-load-dots"><i>.</i><i>.</i><i>.</i></span>'
      +'<span class="vintake-ai-meta"><b>'+done+'</b> / <b>'+total+'</b> screenshots · <span class="vintake-ai-new">'+nw+' new</span></span></div>'
      +'<div class="ai-load-sub">✨ '+verb.toLowerCase()+' item names · matching the database…</div>'
      +'<div class="ai-load-bar"><span style="width:'+pct+'%"></span></div></div></div>';
  });
  await page.waitForTimeout(500);
  await page.locator('#vault-intake-report').screenshot({ path:'/tmp/vload.png' });
});
