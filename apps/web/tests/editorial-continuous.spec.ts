import { test, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

test('four-minute match-first viewer stays continuous through goal, cancellation and explicit end', async ({page,request}) => {
  test.skip(process.env.WHY_NOW_EDITORIAL_CONTINUOUS_E2E !== '1', 'Opt in to a four-minute zero-model browser run.');
  test.setTimeout(290000);
  const headers={'X-Producer-Token':'local-demo-producer'};
  const created=await request.post('/api/replay-sessions',{headers,data:{match_id:'match-0c0a000000000008',mode:'live',execution:'template'}});
  expect(created.ok()).toBeTruthy(); const sid=(await created.json()).session_id;
  const samples:{elapsed_ms:number;clock_ms:number;score:string}[]=[];
  const start=performance.now(); let previous=0; let sawGoal=false; let sawCorrection=false;
  try {
    await page.setViewportSize({width:390,height:844}); await page.goto(`/watch/${sid}`);
    await expect(page.getByRole('button',{name:'Match first',exact:true})).toHaveAttribute('aria-pressed','true');
    while (performance.now()-start<260000) {
      const clock=Number(await page.getByRole('progressbar',{name:'Segment progress'}).getAttribute('aria-valuenow'));
      const score=await page.getByTestId('match-state').innerText();
      expect(clock).toBeGreaterThanOrEqual(previous); previous=clock;
      samples.push({elapsed_ms:performance.now()-start,clock_ms:clock,score});
      if(/1\s*:\s*0/.test(score)) sawGoal=true;
      if(sawGoal && /0\s*:\s*0/.test(score)) sawCorrection=true;
      await expect(page.getByTestId('audience-explanation')).toHaveCount(0);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
      if(clock>=240000) break;
      await page.waitForTimeout(1000);
    }
    expect(previous).toBe(240000);expect(sawGoal).toBeTruthy();expect(sawCorrection).toBeTruthy();
    await expect(page.getByText('Simulation ended',{exact:true})).toBeVisible();
    expect(page.url()).toContain(sid);
    await page.getByRole('button',{name:'Catch me up',exact:true}).click();
    await expect(page.getByTestId('catch-up-panel')).toContainText('No approved explanations in this interval');
    const final=await(await request.get(`/api/replay-sessions/${sid}/snapshot`)).json();
    expect(final.running).toBeFalsy();expect(final.stories).toHaveLength(0);expect(final.score.blue).toBe(0);
    await mkdir('../../.run/editorial-continuous',{recursive:true});
    await page.screenshot({path:'../../.run/editorial-continuous/end-mobile.png',fullPage:true});
    await writeFile('../../.run/editorial-continuous/result.json',JSON.stringify({sid,execution:'template',model_calls:0,scope:'Four-minute UI continuity with no approvals or controls; not a model-timing or user-usefulness study.',elapsed_ms:performance.now()-start,sawGoal,sawCorrection,samples},null,2));
  } finally {await request.post(`/api/replay-sessions/${sid}/control`,{headers,data:{action:'stop'}});}
});
