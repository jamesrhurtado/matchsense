import { test, expect, APIRequestContext } from '@playwright/test';
const headers = {'X-Producer-Token':'local-demo-producer'};
test.beforeEach(async ({request}) => {
  const catalogue=await (await request.get('/api/matches')).json();
  const enabled=catalogue.matches.some((m:{match_id:string})=>m.match_id==='match-0c0a000000000001');
  if(process.env.WHY_NOW_MATCH_COVERAGE_E2E==='1') expect(enabled).toBeTruthy();
  test.skip(!enabled,'Mixed-event catalogue is opt-in; start the API with WHY_NOW_MATCH_COVERAGE=1.');
});
async function session(request: APIRequestContext, correction=false) {
  const response = await request.post('/api/replay-sessions', {headers,data:{match_id:`match-0c0a00000000000${correction ? 2 : 1}`}});
  expect(response.ok()).toBeTruthy();
  return `/api/replay-sessions/${(await response.json()).session_id}`;
}
async function seek(request: APIRequestContext, base: string, at: number) {
  expect((await request.post(base+'/control',{headers,data:{action:'seek',clock_ms:at}})).ok()).toBeTruthy();
}
async function packageFor(request: APIRequestContext, base: string, id: string) {
  const response = await request.get(`${base}/stories/${id}/evidence`,{headers});expect(response.ok()).toBeTruthy();
  return (await response.json()).story;
}
async function approve(request: APIRequestContext, base: string, id: string, archive=false) {
  const p = await packageFor(request,base,id);
  const response=await request.post(`${base}/stories/${id}/review`,{headers,data:{action:archive?'approve_archive':'approve',expected_revision:p.revision,package_hash:p.package_hash,idempotency_key:crypto.randomUUID()}});
  expect(response.ok()).toBeTruthy();return p;
}

test('mixed producer and mobile viewer: every family, evidence, Spanish, focus, recap, archived navigation',async({page,request,context},testInfo)=>{
  test.setTimeout(120000);
  await page.goto('/');
  await expect(page.getByLabel('Replay segment')).toHaveValue('match-0c0a000000000005');
  await expect(page.getByRole('heading',{name:'Producer demo entrance'})).toBeVisible();
  const base=await session(request);const sid=base.split('/').at(-1)!;
  for(const [at,id] of [[25000,'story-pass-1'],[33000,'story-recovery-loose-1'],[47000,'story-shot-attempt-1'],[60000,'story-possession-60000']] as const) {
    await seek(request,base,at);await approve(request,base,id);
  }
  await seek(request,base,105000);
  const publicBefore=(await (await request.get(base+'/snapshot')).json());
  expect(publicBefore.score.blue).toBe(1);expect(publicBefore.stories.some((s:{family:string})=>s.family==='goal')).toBeFalsy();
  await page.addInitScript(()=>sessionStorage.setItem('why-now-token','local-demo-producer'));
  await page.goto(`/studio/${sid}`);
  await expect(page.getByText('1 : 0',{exact:true})).toBeVisible();
  const queue=page.getByRole('group',{name:'Story queue moments'});
  await queue.getByLabel('Event family').selectOption('goal');
  await queue.getByRole('button',{name:/Confirmed goal/}).click();
  await page.getByRole('button',{name:'Show why',exact:true}).click();
  await expect(page.getByTestId('event-evidence').first()).toContainText('Scorer:');
  await page.getByRole('button',{name:'Approve',exact:true}).click();
  await expect(page.getByText('On air',{exact:false}).first()).toBeVisible();
  const viewer=await context.newPage();await viewer.setViewportSize({width:390,height:844});
  await viewer.goto(`/watch/${sid}`);
  await expect(viewer.getByTestId('audience-explanation')).toContainText('Confirmed goal');
  await expect(viewer.getByText('1 : 0',{exact:true})).toBeVisible();
  expect(await viewer.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await viewer.getByLabel('Language',{exact:true}).selectOption('es');
  await expect(viewer.getByTestId('audience-explanation')).toContainText('Gol confirmado');
  await viewer.getByLabel('Seguir a un jugador o equipo').selectOption('blue-09');
  await expect(viewer.getByTestId('audience-explanation')).toContainText('Autor:');
  await viewer.getByLabel('Seguir a un jugador o equipo').selectOption('amber');
  await expect(viewer.getByTestId('audience-explanation')).toContainText('Posesión');
  await viewer.getByLabel('Seguir a un jugador o equipo').selectOption('blue-01');
  await expect(viewer.getByText('No hay participación aprobada en este intervalo.')).toBeVisible();
  await viewer.getByLabel('Seguir a un jugador o equipo').selectOption('');
  await viewer.getByRole('button',{name:'Ponerme al día'}).click();
  await expect(viewer.getByRole('heading',{name:'Resumen del segmento'})).toBeVisible();
  await expect(viewer.getByText('Marcador confirmado actual: 1 : 0')).toBeVisible();
  await viewer.getByRole('button',{name:'Close recap'}).click();
  await viewer.getByText('Historial aprobado · 5',{exact:true}).click();
  const history=viewer.getByRole('group',{name:'Momentos aprobados'});
  await history.getByLabel('Categoría').selectOption('shot');
  await history.getByRole('button',{name:/Resultado del remate/}).click();
  await expect(viewer.getByTestId('audience-explanation')).toContainText('atajado');
  await viewer.getByRole('button',{name:'Ver evidencia',exact:true}).click();
  await expect(viewer.getByRole('img',{name:'Ubicación observada del remate'}).last()).toBeVisible();
  await viewer.getByRole('button',{name:'Cerrar evidencia'}).click();
  await history.getByLabel('Categoría').selectOption('possession');
  await history.getByRole('button',{name:/Posesión/}).click();
  await expect(viewer.getByTestId('event-evidence').first()).toContainText('Base asignada');
  await expect(viewer.getByTestId('event-evidence').first().getByRole('table')).toBeVisible();
  await history.getByLabel('Categoría').selectOption('recovery');
  await history.getByRole('button',{name:/Cambio de control/}).click();
  await expect(viewer.getByTestId('audience-explanation')).toContainText('recuperó');
  await viewer.screenshot({path:testInfo.outputPath('mixed-mobile.png'),fullPage:true});
  await viewer.setViewportSize({width:1366,height:768});
  await viewer.screenshot({path:testInfo.outputPath('mixed-desktop.png'),fullPage:true});
  // Viewing archived moments changes neither shared overlay nor other viewers.
  expect((await (await request.get(base+'/snapshot')).json()).overlay_story_id).toBe('story-goal-goal-1');
  await seek(request,base,150000);
  await approve(request,base,'story-shot-attempt-2',true);
  const grouped=await (await request.get(base+'/snapshot')).json();
  expect(grouped.stories.filter((s:{incident_id:string})=>s.incident_id==='shot:attempt-2')).toHaveLength(1);
  expect(grouped.overlay).toBeNull();
});

test('source score correction revokes affected narrative; reapproval, duplicate grouping, reconnect and recap refresh',async({page,request})=>{
  test.setTimeout(120000);
  const base=await session(request,true);const sid=base.split('/').at(-1)!;
  await seek(request,base,105000);await approve(request,base,'story-goal-goal-1');await approve(request,base,'story-shot-attempt-2');
  await page.goto(`/watch/${sid}`);
  await expect(page.getByTestId('audience-explanation')).toContainText('Confirmed goal');
  await page.getByRole('button',{name:'Catch me up'}).click();
  await expect(page.getByRole('heading',{name:'Segment catch-up'})).toBeVisible();
  await seek(request,base,136000);
  await expect(page.getByText('0 : 0',{exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Segment catch-up'})).toHaveCount(0);
  await expect(page.getByTestId('audience-explanation')).not.toContainText('Confirmed goal');
  await approve(request,base,'story-shot-attempt-2');
  await expect(page.getByTestId('audience-explanation')).toContainText('cancelled');
  await page.reload();
  await expect(page.getByTestId('audience-explanation')).toContainText('cancelled');
  await page.getByRole('button',{name:'Catch me up'}).click();
  await expect(page.getByText('Current source-confirmed score: 0 : 0')).toBeVisible();
  const recap=await (await request.post(base+'/recaps',{data:{}})).json();expect(recap.moments).toHaveLength(1);
  expect(recap.moments[0].text).toContain('cancelled');
});

test('expired producer candidates have an explicit archive-only approval control',async({page,request})=>{
  const base=await session(request);const sid=base.split('/').at(-1)!;
  await seek(request,base,105000);
  await page.addInitScript(()=>sessionStorage.setItem('why-now-token','local-demo-producer'));
  await page.goto(`/studio/${sid}`);
  const queue=page.getByRole('group',{name:'Story queue moments'});
  await queue.getByLabel('Include archived candidates').check();
  await queue.getByLabel('Event family').selectOption('shot');
  await queue.getByRole('button',{name:/00:46/}).click();
  await page.getByRole('button',{name:'Approve for history only'}).click();
  await expect(page.getByText('Approved · archived',{exact:false}).first()).toBeVisible();
  const state=await (await request.get(base+'/snapshot')).json();expect(state.overlay).toBeNull();
  expect(state.stories).toHaveLength(1);expect(state.stories[0].family).toBe('shot');
});

test('linked approved shot remains selectable for a shooter different from the scorer',async({page})=>{
  const shot={id:'story-shot-s',revision:1,title:'Shot outcome',family:'shot',incident_id:'shot:s',participants:{shooter:'blue-09'},team_id:'blue',evidence_revision:'shot-rev',eligible_from_ms:1000,expires_at_ms:31000,status:'approved',approved:true};
  const goal={id:'story-goal-g',revision:1,title:'Confirmed goal',family:'goal',incident_id:'shot:s',participants:{scorer:'blue-08'},team_id:'blue',evidence_revision:'goal-rev',eligible_from_ms:2000,expires_at_ms:32000,status:'approved',approved:true,related_stories:[shot]};
  const snap={session_id:'linked-demo',clock_ms:3000,duration_ms:240000,running:false,speed:1,mode:'local deterministic template',story:goal,stories:[goal],story_status:'approved',overlay:'Approved goal',overlay_story_id:goal.id,delivered_count:2,frame:null,teams:[],players:[{id:'blue-09',name:'Verified Shooter',number:9,team_id:'blue'},{id:'blue-08',name:'Verified Scorer',number:8,team_id:'blue'}],cursor:3};
  await page.route('**/api/replay-sessions/linked-demo/**',async route=>{
    const url=new URL(route.request().url());
    if(url.pathname.endsWith('/snapshot')) await route.fulfill({json:{...snap,story:url.searchParams.get('story_id')===shot.id?shot:goal}});
    else if(url.pathname.endsWith('/stream'))await route.fulfill({contentType:'text/event-stream',body:`event: resync\ndata: ${JSON.stringify(snap)}\n\n`});
    else if(url.pathname.endsWith('/variants'))await route.fulfill({json:{id:'v',text:url.pathname.includes(shot.id)?'Verified Shooter: shot saved.':'Confirmed goal by Verified Scorer.',language:'en',detail:'simple',focus:url.searchParams.get('focus')}});
    else await route.fulfill({status:404,json:{detail:{code:'unavailable'}}});
  });
  await page.goto('/watch/linked-demo');
  await expect(page.getByTestId('audience-explanation')).toContainText('Verified Scorer');
  await page.getByLabel('Follow a player or team').selectOption('blue-09');
  await expect(page.getByTestId('audience-explanation')).toContainText('Verified Shooter');
  await expect(page.getByText('Relevant approved history · 1',{exact:true})).toBeVisible();
  await page.getByLabel('Follow a player or team').selectOption('blue');
  await expect(page.getByText('Relevant approved history · 1',{exact:true})).toBeVisible();
  await page.getByText('Relevant approved history · 1',{exact:true}).click();
  await page.getByRole('group',{name:'Approved moments'}).getByLabel('Event family').selectOption('shot');
  await page.getByRole('group',{name:'Approved moments'}).getByRole('button',{name:/Shot outcome/}).click();
  await expect(page.getByTestId('audience-explanation')).toContainText('Verified Shooter');
});
