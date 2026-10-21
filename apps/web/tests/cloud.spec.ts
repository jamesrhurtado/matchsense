import {test,expect} from '@playwright/test';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

// Explicit opt-in: this test starts a real, billable Azure model workflow.
test('hosted Azure workflow: evidence, real model review, approval and companion',async({page,context,request})=>{
 test.skip(process.env.WHY_NOW_CLOUD_TEST!=='1','Set WHY_NOW_CLOUD_TEST=1 to test the Azure deployment.');
 test.setTimeout(210_000);
 const root=path.resolve(__dirname,'../../..');
 const access=JSON.parse(readFileSync(path.join(root,'.azure/qa-access.json'),'utf8')) as {url?:string;producer_key:string};
 if(!access.producer_key)throw new Error('Private QA producer key is missing');
 const base=access.url||'https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io';
 const headers={'X-Producer-Token':access.producer_key};
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.goto(base);
 await page.getByLabel('Producer access key').fill(access.producer_key);
 await page.getByLabel('Replay segment').selectOption('match-001');
 await page.getByRole('button',{name:'Open producer console'}).click();
 await expect(page).toHaveURL(/\/studio\//,{timeout:30_000});
 const sid=page.url().split('/').pop()!;
 await page.getByLabel('Replay speed').selectOption('1');
 await page.getByRole('button',{name:'Play',exact:true}).click();
 await expect.poll(async()=>{
  const response=await request.get(`${base}/api/replay-sessions/${sid}/snapshot`,{headers});
  if(!response.ok())throw new Error(`Snapshot failed (${response.status()})`);
  return (await response.json()).clock_ms as number;
 },{timeout:40_000,intervals:[1000]}).toBeGreaterThanOrEqual(24_500);
 await page.getByRole('button',{name:'Pause',exact:true}).click();
 await expect(page.getByRole('button',{name:'Show why',exact:true})).toBeVisible({timeout:90_000});
 const response=await request.get(`${base}/api/replay-sessions/${sid}/diagnostics`,{headers});
 expect(response.ok()).toBeTruthy();
 const diagnostics=await response.json();
 mkdirSync(path.join(root,'.run'),{recursive:true});
 writeFileSync(path.join(root,'.run/cloud-latest-diagnostics.json'),JSON.stringify({session_id:sid,...diagnostics},null,2)+'\n');
 expect(diagnostics.azure_deployed).toBe(true);
 expect(diagnostics.mode).toBe('Microsoft Agent Framework + Azure OpenAI');
 expect(diagnostics.model_calls).toBeGreaterThanOrEqual(3);
 expect(diagnostics.model_tokens).toBeGreaterThan(0);
 expect(diagnostics.model_usage.usage_complete).toBe(true);
 const modelTrace=diagnostics.trace.filter((entry:{action:string})=>entry.action==='model_decision');
 expect(modelTrace.length).toBeGreaterThanOrEqual(3);
 expect(new Set(modelTrace.map((entry:{role:string})=>entry.role)).size).toBeGreaterThanOrEqual(3);
 expect(diagnostics.trace.some((entry:{action:string})=>entry.action==='template_fallback')).toBe(false);
 await page.getByRole('button',{name:'Show why',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Follow the escape.'})).toBeVisible();
 await page.getByRole('button',{name:'Approve',exact:true}).click();
 await expect(page.getByText(/On air · revision/)).toBeVisible({timeout:30_000});
 const viewer=await context.newPage();
 viewer.on('pageerror',error=>errors.push(error.message));
 await viewer.goto(`${base}/watch/${sid}`);
 await expect(viewer.getByRole('heading',{name:'Understand this sequence'})).toBeVisible({timeout:30_000});
 await viewer.getByRole('button',{name:'Show the detail',exact:true}).click();
 await viewer.getByLabel('Language',{exact:true}).selectOption('es');
 await viewer.getByLabel('Follow a player or team').selectOption('blue-08');
 await expect(viewer.locator('p[lang="es"]').first()).toContainText('Theo Vega',{timeout:30_000});
 await viewer.getByRole('button',{name:'Catch me up'}).click();
 await expect(viewer.getByRole('heading',{name:'El partido hasta ahora'})).toBeVisible({timeout:30_000});
 const artifactDir=path.join(root,'.run');mkdirSync(artifactDir,{recursive:true});
 await page.screenshot({path:path.join(artifactDir,'cloud-producer.png'),fullPage:true});
 await viewer.setViewportSize({width:390,height:844});
 await viewer.screenshot({path:path.join(artifactDir,'cloud-viewer-mobile.png'),fullPage:true});
 expect(await viewer.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.getByRole('button',{name:'Retract',exact:true}).click();
 await expect(viewer.getByRole('heading',{name:'The next story is taking shape'})).toBeVisible({timeout:30_000});
 await expect(viewer.getByRole('heading',{name:'El partido hasta ahora'})).not.toBeVisible();
 expect(errors).toEqual([]);
 // Persist only nonsecret verification data for the deployment report.
 writeFileSync(path.join(artifactDir,'cloud-browser-verification.json'),JSON.stringify({
  checked_at:new Date().toISOString(),session_id:sid,url:base,mode:diagnostics.mode,
  model_calls:diagnostics.model_calls,model_usage:diagnostics.model_usage,
  roles:[...new Set(modelTrace.map((entry:{role:string})=>entry.role))],
  approved:true,retracted:true,mobile_overflow:false,browser_errors:errors,
 },null,2)+'\n');
});
