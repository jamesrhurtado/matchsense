import {test,expect} from '@playwright/test';

test('three-minute replay preserves independent approvals, archived evidence, and recap',async({page,context,request})=>{
 const headers={'X-Producer-Token':'local-demo-producer'};
 const created=await request.post('/api/replay-sessions',{headers,data:{match_id:'match-ce88c61d5a0c5d1d'}});
 expect(created.ok()).toBeTruthy();const sid=(await created.json()).session_id;const path=`/api/replay-sessions/${sid}`;
 await page.addInitScript(()=>sessionStorage.setItem('why-now-token','local-demo-producer'));
 await page.goto(`/studio/${sid}`);await expect(page.getByText('3-minute demo replay')).toBeVisible();
 if(!(await page.getByLabel('Skip to time (seconds)').isVisible()))await page.getByText('Replay navigation',{exact:true}).click();await page.getByLabel('Skip to time (seconds)').fill('20');await page.getByRole('button',{name:'Skip forward',exact:true}).click();
 const queue=page.getByRole('group',{name:'Suggested insights'});
 await expect(queue.getByRole('button')).toHaveCount(1);await page.getByRole('button',{name:'Approve',exact:true}).click();
 await expect(page.getByRole('button',{name:'Retract',exact:true})).toBeVisible();
 if(!(await page.getByLabel('Skip to time (seconds)').isVisible()))await page.getByText('Replay navigation',{exact:true}).click();await page.getByLabel('Skip to time (seconds)').fill('80');await page.getByRole('button',{name:'Skip forward',exact:true}).click();
 await expect(queue.getByRole('button')).toHaveCount(2);await queue.getByRole('button',{name:/Insight 2/}).click();await page.getByRole('button',{name:'Approve',exact:true}).click();
 await expect(page.getByRole('button',{name:'Retract',exact:true})).toBeVisible();
 const viewer=await context.newPage();await viewer.goto(`/watch/${sid}`);
 await viewer.getByText('Approved match insights · 2',{exact:true}).click();
 const history=viewer.getByRole('group',{name:'Approved match insights'});await expect(history.getByRole('button')).toHaveCount(2);
 await history.getByRole('button',{name:/Insight 1/}).click();await expect(history.getByRole('button',{name:/Insight 1/})).toHaveAttribute('aria-pressed','true');
 await viewer.getByRole('button',{name:'Show why',exact:true}).click();await expect(viewer.getByRole('heading',{name:'Replay the sequence.'})).toBeVisible();
 await viewer.getByRole('button',{name:'Catch me up',exact:true}).click();await expect(viewer.getByRole('heading',{name:'Match so far'})).toBeVisible();
 const recap=await request.post(`${path}/recaps`,{data:{language:'en'}});const projected=await recap.json();expect(projected.approved_count).toBe(2);expect(projected.moments[0].similar_moments).toHaveLength(2);
 if(!(await page.getByLabel('Skip to time (seconds)').isVisible()))await page.getByText('Replay navigation',{exact:true}).click();await page.getByLabel('Skip to time (seconds)').fill('90');await page.getByRole('button',{name:'Skip forward',exact:true}).click();
 await queue.getByRole('button',{name:/Insight 1/}).click();await expect(page.getByRole('button',{name:'Retract',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Retract',exact:true}).click();
 await expect.poll(async()=>{const response=await request.get(`${path}/snapshot`);const state=await response.json();return state.stories?.map((story:{id:string})=>story.id);}).toEqual(['story-pass-2']);
 const remaining=await request.get(`${path}/snapshot`);expect((await remaining.json()).overlay).toBeTruthy();
 const recapAfter=await request.post(`${path}/recaps`,{data:{language:'en'}});expect((await recapAfter.json()).moments).toHaveLength(1);
 await viewer.setViewportSize({width:390,height:844});expect(await viewer.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
