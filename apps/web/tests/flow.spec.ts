import {test,expect} from '@playwright/test';

test('producer evidence → wording review → approval → viewer preferences → retraction',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.getByRole('button',{name:'Open producer console'}).click();await expect(page).toHaveURL(/\/studio\//);
 const sid=page.url().split('/').pop()!;
 await page.getByLabel('Replay speed').selectOption('8');await page.getByRole('button',{name:'Play',exact:true}).click();
 await expect(page.getByRole('button',{name:'Show why',exact:true})).toBeVisible({timeout:10000});await page.getByRole('button',{name:'Pause',exact:true}).click();
 await page.getByRole('button',{name:'Show why',exact:true}).click();await expect(page.getByRole('heading',{name:'Replay the sequence.'})).toBeVisible();
 await page.getByRole('button',{name:'Play evidence replay',exact:true}).click();await page.waitForTimeout(300);await page.getByRole('button',{name:'Pause evidence replay',exact:true}).click();
 await page.getByRole('button',{name:'Suggest an emphasis'}).click();await page.getByLabel('Suggest an emphasis or wording for evidence review').fill('Harbor City now controls the match.');await page.getByRole('button',{name:'Submit for review'}).click();
 await expect(page.getByText('Proposed wording reviewed')).toBeVisible();
 await page.getByRole('button',{name:'Approve',exact:true}).click();await expect(page.getByText('On air · revision 2')).toBeVisible();
 const before=await page.locator('#live').innerText();
 const viewer=await context.newPage();await viewer.goto(`/watch/${sid}`);await expect(viewer.getByRole('heading',{name:/Theo Vega.*Sami Rios/})).toBeVisible();
 await viewer.getByRole('button',{name:'Show the detail',exact:true}).click();await viewer.getByText('Inspect the facts',{exact:true}).click();await expect(viewer.getByRole('button',{name:/up to 2 opponents were within 6 m/})).toBeVisible();
 await viewer.getByLabel('Language',{exact:true}).selectOption('es');await viewer.getByLabel('Seguir a un jugador o equipo').selectOption('blue-08');await expect(viewer.getByTestId('audience-explanation')).toContainText('Theo Vega dio el pase');
 await viewer.getByRole('button',{name:'Ponerme al día'}).click();await expect(viewer.getByRole('heading',{name:'El partido hasta ahora'})).toBeVisible();
 expect(await page.locator('#live').innerText()).toEqual(before);
 await page.screenshot({path:'../../.run/studio-desktop.png',fullPage:true});
 await viewer.setViewportSize({width:390,height:844});await viewer.screenshot({path:'../../.run/viewer-mobile.png',fullPage:true});
 expect(await viewer.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:'Retract',exact:true}).click();await expect(viewer.getByText('No hay participación aprobada en este intervalo.')).toBeVisible();
 await expect(viewer.getByRole('heading',{name:'El partido hasta ahora'})).not.toBeVisible();
 expect(errors).toEqual([]);
});

test('viewer stream delivers resync and state updates through the web proxy',async({page,request})=>{
 const created=await request.post('/api/replay-sessions',{headers:{'X-Producer-Token':'local-demo-producer'},data:{match_id:'match-001'}});const sid=(await created.json()).session_id;
 await request.post(`/api/replay-sessions/${sid}/control`,{headers:{'X-Producer-Token':'local-demo-producer'},data:{action:'start'}});
 await page.goto(`/watch/${sid}`);
 const result=await page.evaluate(async(sessionId)=>{
  const abort=new AbortController();const timeout=setTimeout(()=>abort.abort(),5000);let text='';
  try{const response=await fetch(`/api/replay-sessions/${sessionId}/stream`,{signal:abort.signal});const reader=response.body!.getReader();const decoder=new TextDecoder();while(!text.includes('event: state_update')){const {value,done}=await reader.read();if(done)break;text+=decoder.decode(value,{stream:true});}await reader.cancel();return text;}finally{clearTimeout(timeout);abort.abort();}
 },sid);
 expect(result).toContain('event: resync');expect(result).toContain('event: state_update');
});


test('web proxy preserves authorization errors and rejects oversized bodies', async({request}) => {
 const unauthorized=await request.post('/api/replay-sessions',{data:{match_id:'match-001'}});
 expect(unauthorized.status()).toBe(401);
 const oversized=await request.post('/api/replay-sessions',{headers:{'Content-Type':'application/json'},data:'x'.repeat(65537)});
 expect(oversized.status()).toBe(413);
 expect((await oversized.json()).detail.code).toBe('request_too_large');
});

test('pending AI review remains visible while replay continues',async({page})=>{
 await page.route('**/api/replay-sessions/pending-demo/snapshot',route=>route.fulfill({json:{
  session_id:'pending-demo',clock_ms:23000,duration_ms:60000,running:true,speed:1,
  mode:'Azure model workflow',workflow_pending:true,story:null,story_status:'waiting',
  overlay:null,delivered_count:2300,frame:null,teams:[],players:[],cursor:23000,
 }}));
 await page.goto('/studio/pending-demo');
 await expect(page.getByRole('status')).toContainText('AI review in progress');
 await expect(page.getByRole('status')).toContainText('Azure model workflow');
 await expect(page.getByRole('button',{name:'Pause',exact:true})).toBeEnabled();
 await expect(page.getByRole('button',{name:'Approve',exact:true})).toHaveCount(0);
});
