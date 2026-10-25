import {test,expect} from '@playwright/test';

const headers={'X-Producer-Token':'local-demo-producer'};
test('five approved moments keep the mobile explanation and pitch together; contrast links to three exact passes',async({page,request},testInfo)=>{
 const created=await request.post('/api/replay-sessions',{headers,data:{match_id:'match-57c134ad6e6457a4'}});
 expect(created.ok()).toBeTruthy();
 const sid=(await created.json()).session_id;const base=`/api/replay-sessions/${sid}`;
 for(const [index,at] of [20000,45000,70000,95000,120000].entries()){
  expect((await request.post(base+'/control',{headers,data:{action:'seek',clock_ms:at}})).ok()).toBeTruthy();
  const state=await (await request.get(base+'/snapshot',{headers})).json();
  const story=state.stories.find((s:{id:string})=>s.id===`story-pass-${index+1}`);
  expect((await request.post(`${base}/stories/${story.id}/review`,{headers,data:{action:'approve',expected_revision:story.revision,package_hash:story.package_hash,idempotency_key:crypto.randomUUID()}})).ok()).toBeTruthy();
 }
 await page.setViewportSize({width:390,height:844});
 await page.goto(`/watch/${sid}`);
 await expect(page.getByTestId('inline-evidence')).toBeVisible();
 await expect(page.getByText('Approved match insights · 5',{exact:true})).toBeVisible();
 await expect(page.getByRole('group',{name:'Approved match insights'})).not.toBeVisible();
 const pitch=page.getByTestId('inline-evidence').getByRole('img');
 const box=await pitch.boundingBox();expect(box!.y+box!.height).toBeLessThan(844);
 const why=await page.getByRole('button',{name:'Show why',exact:true}).boundingBox();expect(why!.y+why!.height).toBeLessThan(844);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.getByText('Approved match insights · 5',{exact:true}).click();
 await page.getByRole('group',{name:'Approved match insights'}).getByRole('button',{name:/Insight 4/}).click();
 await expect(page.getByTestId('audience-explanation')).toContainText('previous three completed passes in this replay');
 await page.getByText('Inspect the facts',{exact:true}).click();
 await page.getByRole('button',{name:/farther forward than each/}).click();
 await expect(page.getByTestId('earlier-moment')).toContainText('Viewing an earlier moment');
 await expect(page.getByTestId('pass-comparison').getByRole('list')).toContainText('Current pass');
 await page.getByText('Original values and sources',{exact:true}).click();
 await expect(page.getByRole('table')).toContainText('pass-3');
 await expect(page.getByRole('table')).toContainText('16');
 await expect(page.getByRole('table')).toContainText('12');
 await expect(page.getByRole('table')).toContainText('8');
 await page.getByLabel('Language',{exact:true}).selectOption('es');
 await expect(page.getByTestId('audience-explanation')).toContainText('tres pases completados anteriores');
 await expect(page.getByRole('button',{name:'Ver evidencia',exact:true})).toBeVisible();
 await page.screenshot({path:testInfo.outputPath('context-mobile.png'),fullPage:true});
 await page.setViewportSize({width:1366,height:768});
 await page.screenshot({path:testInfo.outputPath('context-desktop.png'),fullPage:true});
 await page.getByRole('button',{name:'Ver evidencia',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Repite la secuencia.'})).toBeVisible();
 await expect(page.getByRole('group',{name:'Etapas de la evidencia'})).toBeVisible();
 await page.getByRole('button',{name:'Cerrar evidencia'}).click();
 await page.getByRole('button',{name:'Volver al directo',exact:true}).click();
 await expect(page.getByTestId('earlier-moment')).toHaveCount(0);
});
