import { test, expect, APIRequestContext } from '@playwright/test';
const headers = { 'X-Producer-Token': 'local-demo-producer' };
async function create(request: APIRequestContext, match='match-0c0a000000000002', mode='guided') {
  const r=await request.post('/api/replay-sessions',{headers,data:{match_id:match,mode,execution:'template'}});
  expect(r.ok()).toBeTruthy(); return (await r.json()).session_id as string;
}
async function seek(request: APIRequestContext,sid:string,time:number) {
  expect((await request.post(`/api/replay-sessions/${sid}/control`,{headers,data:{action:'seek',clock_ms:time}})).ok()).toBeTruthy();
}
async function approve(request: APIRequestContext,sid:string,id:string) {
  const p=await(await request.get(`/api/replay-sessions/${sid}/stories/${id}/evidence`,{headers})).json();
  const r=await request.post(`/api/replay-sessions/${sid}/stories/${id}/review`,{headers,data:{action:'approve',expected_revision:p.story.revision,package_hash:p.story.package_hash,idempotency_key:crypto.randomUUID()}});
  expect(r.ok()).toBeTruthy();
}

test('continuous viewer starts match-first; preview is private, bilingual and optional on mobile',async({page,context,request})=>{
  test.setTimeout(75000);
  const sid=await create(request,'match-0c0a000000000005','live');
  try {
    const hiddenFetches:string[]=[];
    page.on('request',r=>{if(/\/stories\/.*\/(variants|evidence)/.test(r.url())) hiddenFetches.push(r.url());});
    await page.goto(`/watch/${sid}`);
    await expect(page.getByRole('button',{name:'Match first',exact:true})).toHaveAttribute('aria-pressed','true');
    await expect(page.getByTestId('audience-explanation')).toHaveCount(0);
    const producer=await context.newPage();
    await producer.addInitScript(()=>sessionStorage.setItem('why-now-token','local-demo-producer'));
    await producer.goto(`/studio/${sid}`);
    await expect(producer.getByRole('button',{name:'Approve',exact:true})).toBeVisible({timeout:35000});
    await producer.getByText('Preview for viewers · draft',{exact:true}).click();
    await expect(producer.getByTestId('audience-preview')).not.toContainText('Loading this revision');
    await expect(producer.getByTestId('audience-preview')).toContainText('Casual viewer');
    await expect(producer.getByTestId('audience-preview')).toContainText('Analyst');
    expect((await(await request.get(`/api/replay-sessions/${sid}/snapshot`)).json()).stories).toHaveLength(0);
    await producer.getByLabel('Preview language',{exact:true}).selectOption('es');
    await expect(producer.getByTestId('audience-preview')).toContainText('Para seguir el partido');
    await expect(producer.getByTestId('audience-preview')).not.toContainText('Cargando esta revisión');
    await producer.setViewportSize({width:390,height:844});
    await producer.getByLabel('Perspectiva de vista previa').selectOption('detail');
    expect(await producer.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await producer.screenshot({path:'../../.run/editorial-producer-mobile.png',fullPage:true});
    await producer.getByRole('button',{name:'Approve',exact:true}).click();
    await expect.poll(async()=> (await(await request.get(`/api/replay-sessions/${sid}/snapshot`)).json()).stories.length).toBeGreaterThan(0);
    expect(hiddenFetches).toEqual([]);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'../../.run/editorial-match-first-mobile.png',fullPage:true});
    await page.getByRole('button',{name:'Explore explanations',exact:true}).click();
    await expect(page.getByTestId('audience-explanation')).not.toBeEmpty();
    await page.getByLabel('Language',{exact:true}).selectOption('es');
    await expect(page.getByTestId('audience-explanation')).not.toBeEmpty();
    await page.getByRole('button',{name:'Ponerme al día',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Resumen del segmento'})).toBeVisible();
    await page.getByLabel('Intervalo del resumen').selectOption('visit');
    await expect(page.getByTestId('catch-up-panel')).toContainText('Hechos ocurridos en este intervalo');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    expect((await(await request.get(`/api/replay-sessions/${sid}/snapshot`)).json()).running).toBeTruthy();
  } finally {await request.post(`/api/replay-sessions/${sid}/control`,{headers,data:{action:'stop'}});}
});

test('catch-up stays open on correction, restores private visit interval, and never repeats withdrawn copy',async({page,request})=>{
  const sid=await create(request); await seek(request,sid,105000);
  await approve(request,sid,'story-goal-goal-1'); await approve(request,sid,'story-shot-attempt-2');
  await page.addInitScript(id=>localStorage.setItem(`why-now-visit:${id}`,'20000'),sid);
  await page.goto(`/watch/${sid}`);
  await page.getByRole('button',{name:'Catch me up',exact:true}).click();
  await page.getByLabel('Catch-up interval').selectOption('visit');
  await expect(page.getByTestId('catch-up-panel')).toContainText('00:20–01:45');
  await expect(page.getByTestId('catch-up-panel')).toContainText('Beni');
  await seek(request,sid,136000);
  await expect(page.getByTestId('catch-up-panel')).toContainText('withdrawn');
  await expect(page.getByTestId('catch-up-panel')).not.toContainText('Beni');
  await expect(page.getByTestId('catch-up-panel')).toContainText('Current source-confirmed score: 0 : 0');
  await expect(page.getByTestId('catch-up-panel')).toContainText('No approved explanations in this interval');
  await page.getByLabel('Language',{exact:true}).selectOption('es');
  await expect(page.getByTestId('catch-up-panel')).toContainText('se retiró');
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'../../.run/editorial-correction-mobile.png',fullPage:true});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('preview refuses a response for another revision and never approves the draft',async({page,request})=>{
  const sid=await create(request);await seek(request,sid,105000);
  await page.addInitScript(()=>sessionStorage.setItem('why-now-token','local-demo-producer'));
  let intercepted=0;
  await page.route('**/stories/**/variants?**',async route=>{
    intercepted++;
    await route.fulfill({json:{id:'stale',story_id:'story-goal-goal-1',revision:99,language:'en',detail:'simple',focus:null,text:'STALE REVISION SHOULD NEVER DISPLAY'}});
  });
  await page.goto(`/studio/${sid}`);
  await page.getByText('Preview for viewers · draft',{exact:true}).click();
  await expect.poll(()=>intercepted).toBeGreaterThanOrEqual(3);
  await expect(page.getByTestId('audience-preview')).toContainText('Loading this revision');
  await expect(page.locator('body')).not.toContainText('STALE REVISION SHOULD NEVER DISPLAY');
  expect((await(await request.get(`/api/replay-sessions/${sid}/snapshot`)).json()).stories).toHaveLength(0);
  await page.unrouteAll({behavior:'wait'});
});
