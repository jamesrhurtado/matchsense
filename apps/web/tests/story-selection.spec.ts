import {test,expect} from '@playwright/test';
const first={id:'story-pass-1',revision:1,title:'First supported sequence',evidence_revision:'e1',eligible_from_ms:22200,expires_at_ms:52200,status:'approved',package_hash:'first-hash'};
const second={...first,id:'story-pass-2',title:'Second supported sequence',evidence_revision:'e2',eligible_from_ms:72200,expires_at_ms:102200,package_hash:'second-hash'};
const snapshot={session_id:'queue-demo',clock_ms:80000,duration_ms:180000,running:false,speed:1,mode:'Local deterministic workflow',story:second,story_status:'approved',stories:[first,second],overlay:'Shared second overlay',delivered_count:800,frame:null,teams:[],players:[],cursor:80};
async function mockQueue(page:import('@playwright/test').Page){
 await page.route('**/api/replay-sessions/queue-demo/**',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname.endsWith('/snapshot')){const story=url.searchParams.get('story_id')===first.id?first:second;await route.fulfill({json:{...snapshot,story,story_status:story.id===first.id?'expired':'approved'}});}
  else if(url.pathname.endsWith('/variants')){const story=url.pathname.includes(first.id)?first:second;await route.fulfill({json:{id:`variant-${story.id}`,text:`Explanation for ${story.title}`,language:'en',detail:'simple',focus:null}});}
  else if(url.pathname.endsWith('/stream'))await route.fulfill({contentType:'text/event-stream',body:`event: resync\ndata: ${JSON.stringify(snapshot)}\n\n`});
  else if(url.pathname.endsWith('/control'))await route.fulfill({json:{session_id:'queue-demo'}});
  else await route.fulfill({json:{detail:{code:'not_found'}},status:404});
 });
}
test('producer selects independent moments and navigates a longer replay',async({page})=>{
 await mockQueue(page);await page.goto('/studio/queue-demo');
 await expect(page.getByText('180-second segment')).toBeVisible();await expect(page.getByRole('button',{name:'Play',exact:true})).toBeEnabled();
 const queue=page.getByRole('group',{name:'Story queue moments'});await expect(queue.getByRole('button')).toHaveCount(2);
 await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();await queue.getByRole('button',{name:/Moment 1/}).click();
 await expect(queue.getByRole('button',{name:/Moment 1/})).toHaveAttribute('aria-pressed','true');await expect(page.getByText('Explanation for First supported sequence')).toBeVisible();
 await expect(page.getByRole('button',{name:'Retract',exact:true})).toBeEnabled();await expect(page.getByText('Shared second overlay',{exact:true})).toBeVisible();
 await page.getByLabel('Jump to second').fill('120');const seek=page.waitForRequest(request=>request.url().endsWith('/control')&&request.method()==='POST');await page.getByRole('button',{name:'Jump forward',exact:true}).click();expect((await seek).postDataJSON()).toEqual({action:'seek',clock_ms:120000});
 await page.getByLabel('Jump to second').fill('20');await expect(page.getByRole('button',{name:'Jump forward',exact:true})).toBeDisabled();
});
test('viewer selects approved history without changing the shared overlay',async({page})=>{
 await mockQueue(page);await page.goto('/watch/queue-demo');await page.getByText('Approved history · 2',{exact:true}).click();const moments=page.getByRole('group',{name:'Approved moments'});await expect(moments.getByRole('button')).toHaveCount(2);await moments.getByRole('button',{name:/Moment 1/}).click();await expect(page.getByText('Explanation for First supported sequence')).toBeVisible();await expect(page.getByText('Shared second overlay',{exact:true})).toBeVisible();
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
test('fixture options come from the public catalogue',async({page})=>{
 await page.route('**/api/matches',route=>route.fulfill({json:{matches:[{match_id:'match-001',label:'Segment 01',duration_ms:60000,synthetic:true},{match_id:'match-aabbccddeeff0011',label:'Segment 04',duration_ms:180000,synthetic:true}]}}));await page.goto('/');await expect(page.getByLabel('Replay segment').locator('option')).toHaveCount(2);await page.getByLabel('Replay segment').selectOption('match-aabbccddeeff0011');
 const create=page.waitForRequest(request=>request.url().endsWith('/api/replay-sessions')&&request.method()==='POST');await page.route('**/api/replay-sessions',route=>route.fulfill({json:{session_id:'queue-demo'}}));await mockQueue(page);await page.getByRole('button',{name:'Open producer console'}).click();expect((await create).postDataJSON()).toEqual({match_id:'match-aabbccddeeff0011'});await expect(page).toHaveURL(/\/studio\/queue-demo/);
});

test('a delayed earlier selection cannot replace the latest selected moment',async({page})=>{
 await mockQueue(page);
 await page.route('**/api/replay-sessions/queue-demo/snapshot?story_id=story-pass-1',async route=>{await new Promise(resolve=>setTimeout(resolve,500));await route.fulfill({json:{...snapshot,story:first,story_status:'expired'}});});
 await page.goto('/studio/queue-demo');const queue=page.getByRole('group',{name:'Story queue moments'});await expect(queue.getByRole('button')).toHaveCount(2);
 const earlier=page.waitForRequest('**/snapshot?story_id=story-pass-1');await queue.getByRole('button',{name:/Moment 1/}).click();await earlier;await queue.getByRole('button',{name:/Moment 2/}).click();
 await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();await page.waitForTimeout(650);await expect(queue.getByRole('button',{name:/Moment 2/})).toHaveAttribute('aria-pressed','true');await expect(page.getByText('Explanation for Second supported sequence')).toBeVisible();
});
