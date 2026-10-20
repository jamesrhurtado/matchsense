import {test,expect} from '@playwright/test';

test('producer evidence → wording review → approval → viewer preferences → retraction',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.getByRole('button',{name:'Open producer console'}).click();await expect(page).toHaveURL(/\/studio\//);
 const sid=page.url().split('/').pop()!;
 await page.getByLabel('Replay speed').selectOption('8');await page.getByRole('button',{name:'Play',exact:true}).click();
 await expect(page.getByRole('button',{name:'Show why',exact:true})).toBeVisible({timeout:10000});await page.getByRole('button',{name:'Pause',exact:true}).click();
 await page.getByRole('button',{name:'Show why',exact:true}).click();await expect(page.getByRole('heading',{name:'Follow the escape.'})).toBeVisible();
 await page.getByRole('button',{name:'Play evidence replay',exact:true}).click();await page.waitForTimeout(300);await page.getByRole('button',{name:'Pause evidence replay',exact:true}).click();
 await page.getByRole('button',{name:'Propose an edit'}).click();await page.getByLabel('Propose wording for local review').fill('Harbor City now controls the match.');await page.getByRole('button',{name:'Submit for review'}).click();
 await expect(page.getByText('Producer edit reviewed')).toBeVisible();
 await page.getByRole('button',{name:'Approve',exact:true}).click();await expect(page.getByText('On air · revision 2')).toBeVisible();
 const before=await page.locator('#live').innerText();
 const viewer=await context.newPage();await viewer.goto(`/watch/${sid}`);await expect(viewer.getByRole('heading',{name:'Why this pass mattered'})).toBeVisible();
 await viewer.getByRole('button',{name:'Show the detail',exact:true}).click();await expect(viewer.getByText(/Before the pass, up to 2 opponents/)).toBeVisible();
 await viewer.getByLabel('Language',{exact:true}).selectOption('es');await viewer.getByLabel('Follow a player or team').selectOption('blue-08');await expect(viewer.getByText(/Theo Vega dio el pase/)).toBeVisible();
 await viewer.getByRole('button',{name:'Catch me up'}).click();await expect(viewer.getByRole('heading',{name:'El partido hasta ahora'})).toBeVisible();
 expect(await page.locator('#live').innerText()).toEqual(before);
 await page.screenshot({path:'../../.run/studio-desktop.png',fullPage:true});
 await viewer.setViewportSize({width:390,height:844});await viewer.screenshot({path:'../../.run/viewer-mobile.png',fullPage:true});
 expect(await viewer.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:'Retract',exact:true}).click();await expect(viewer.getByRole('heading',{name:'The next story is taking shape'})).toBeVisible();
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
