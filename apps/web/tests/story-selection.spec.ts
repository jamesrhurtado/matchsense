import {test,expect} from '@playwright/test';
const first={id:'story-pass-1',revision:1,title:'First supported sequence',evidence_revision:'e1',eligible_from_ms:22200,expires_at_ms:52200,status:'approved',package_hash:'first-hash'};
const second={...first,id:'story-pass-2',title:'Second supported sequence',evidence_revision:'e2',eligible_from_ms:72200,expires_at_ms:102200,package_hash:'second-hash'};
const snapshot={session_id:'queue-demo',clock_ms:80000,duration_ms:180000,running:false,speed:1,mode:'Local deterministic workflow',story:second,story_status:'approved',stories:[first,second],overlay:'Shared second overlay',delivered_count:800,frame:null,teams:[],players:[],cursor:80};
async function mockQueue(page:import('@playwright/test').Page){
 await page.route('**/api/replay-sessions/queue-demo/**',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname.endsWith('/snapshot')){const story=url.searchParams.get('story_id')===first.id?first:second;await route.fulfill({json:{...snapshot,story,story_status:story.id===first.id?'expired':'approved'}});}
  else if(url.pathname.endsWith('/variants')){const story=url.pathname.includes(first.id)?first:second;await route.fulfill({json:{id:`variant-${story.id}`,story_id:story.id,revision:story.revision,text:`Explanation for ${story.title}`,language:'en',detail:'simple',focus:null}});}
  else if(url.pathname.endsWith('/diagnostics'))await route.fulfill({json:{decision_summary:null,trace:[],model_calls:0,model_tokens:0,mode:'Local deterministic workflow'}});
  else if(url.pathname.endsWith('/stream'))await route.fulfill({contentType:'text/event-stream',body:`event: resync\ndata: ${JSON.stringify(snapshot)}\n\n`});
  else if(url.pathname.endsWith('/control'))await route.fulfill({json:{session_id:'queue-demo'}});
  else await route.fulfill({json:{detail:{code:'not_found'}},status:404});
 });
}
test('producer selects independent moments and navigates a longer replay',async({page})=>{
 await mockQueue(page);await page.goto('/studio/queue-demo');
 await expect(page.getByText('3-minute demo replay')).toBeVisible();await expect(page.getByRole('button',{name:'Play',exact:true})).toBeEnabled();
 const queue=page.getByRole('group',{name:'Suggested insights'});await expect(queue.getByRole('button')).toHaveCount(2);
 await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();await queue.getByRole('button',{name:/Insight 1/}).click();
 await expect(queue.getByRole('button',{name:/Insight 1/})).toHaveAttribute('aria-pressed','true');await expect(page.getByText('Explanation for First supported sequence')).toBeVisible();
 await expect(page.getByRole('button',{name:'Retract',exact:true})).toBeEnabled();await expect(page.getByText('Shared second overlay',{exact:true})).toBeVisible();
 if(!(await page.getByLabel('Skip to time (seconds)').isVisible()))await page.getByText('Replay navigation',{exact:true}).click();await page.getByLabel('Skip to time (seconds)').fill('120');const seek=page.waitForRequest(request=>request.url().endsWith('/control')&&request.method()==='POST');await page.getByRole('button',{name:'Skip forward',exact:true}).click();expect((await seek).postDataJSON()).toEqual({action:'seek',clock_ms:120000});
 if(!(await page.getByLabel('Skip to time (seconds)').isVisible()))await page.getByText('Replay navigation',{exact:true}).click();await page.getByLabel('Skip to time (seconds)').fill('20');await expect(page.getByRole('button',{name:'Skip forward',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Processing & review trace',exact:true}).click();
 const traceHeading=page.getByRole('heading',{name:'Processing & review trace',exact:true});
 await expect(traceHeading).toBeInViewport();await expect(traceHeading).toBeFocused();
});
test('producer labels a candidate for review and hides a repeated pressure explanation',async({page})=>{
 await mockQueue(page);
 await page.route('**/api/replay-sessions/queue-demo/snapshot*',route=>route.fulfill({json:{...snapshot,flagship_demo:true,story:{...second,family:'pressure',status:'ready',why_now:{en:'Average nearby opponents fell from 2.0 to 1.0 around an 18 m forward pass.'}},story_status:'ready'}}));
 await page.goto('/studio/queue-demo');
 await expect(page.getByRole('heading',{name:'Nearby pressure change',exact:true})).toBeVisible();
 await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
 await expect(page.getByRole('region',{name:'Why this moment'})).toHaveCount(0);
 await expect(page.getByText(/revision 1/)).toHaveCount(0);
});
test('viewer selects approved history without changing the shared overlay',async({page})=>{
 await mockQueue(page);await page.goto('/watch/queue-demo');await page.getByText('Approved match insights · 2',{exact:true}).click();const moments=page.getByRole('group',{name:'Approved match insights'});await expect(moments.getByRole('button')).toHaveCount(2);await moments.getByRole('button',{name:/Insight 1/}).click();await expect(page.getByText('Explanation for First supported sequence')).toBeVisible();await expect(page.getByText('Shared second overlay',{exact:true})).toBeVisible();
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
test('fixture options come from the public catalogue',async({page})=>{
 await page.route('**/api/matches',route=>route.fulfill({json:{matches:[{match_id:'match-001',label:'Segment 01',duration_ms:60000,synthetic:true},{match_id:'match-aabbccddeeff0011',label:'Segment 04',duration_ms:180000,synthetic:true}]}}));await page.goto('/');await page.getByLabel('Experience',{exact:true}).selectOption('guided');await page.getByLabel('Explanations',{exact:true}).selectOption('template');await expect(page.getByLabel('Replay segment').locator('option')).toHaveCount(2);await page.getByText('More demo scenarios',{exact:true}).click();await page.getByLabel('Replay segment').selectOption('match-aabbccddeeff0011');
 const create=page.waitForRequest(request=>request.url().endsWith('/api/replay-sessions')&&request.method()==='POST');await page.route('**/api/replay-sessions',route=>route.fulfill({json:{session_id:'queue-demo'}}));await mockQueue(page);await page.getByRole('button',{name:'Start the guided demo'}).click();expect((await create).postDataJSON()).toEqual({match_id:'match-aabbccddeeff0011',mode:'guided',execution:'template'});await expect(page).toHaveURL(/\/studio\/queue-demo/);
});

test('a delayed earlier selection cannot replace the latest selected moment',async({page})=>{
 await mockQueue(page);
 await page.route('**/api/replay-sessions/queue-demo/snapshot?story_id=story-pass-1',async route=>{await new Promise(resolve=>setTimeout(resolve,500));await route.fulfill({json:{...snapshot,story:first,story_status:'expired'}});});
 await page.goto('/studio/queue-demo');const queue=page.getByRole('group',{name:'Suggested insights'});await expect(queue.getByRole('button')).toHaveCount(2);
 const earlier=page.waitForRequest('**/snapshot?story_id=story-pass-1');await queue.getByRole('button',{name:/Insight 1/}).click();await earlier;await queue.getByRole('button',{name:/Insight 2/}).click();
 await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();await page.waitForTimeout(650);await expect(queue.getByRole('button',{name:/Insight 2/})).toHaveAttribute('aria-pressed','true');await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();
});
