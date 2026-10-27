import { test, expect } from '@playwright/test';

for (const width of [390, 1440]) {
  test(`broadcast stage keeps confirmed state distinct from approved text at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    let corrected = false;
    const snapshot = () => ({
      session_id: 'stage-demo', coverage_enabled: true, clock_ms: 105000,
      duration_ms: 240000, running: false, speed: 1, mode: 'Local deterministic workflow',
      score: { blue: corrected ? 0 : 1, amber: 0 },
      match_state: { score: { blue: corrected ? 0 : 1, amber: 0 }, period: 1, period_elapsed_ms: 105000, period_status: 'playing', source_status: 'confirmed' },
      story: null, stories: [], story_status: 'none', overlay: null,
      overlay_selection_reason: { en: 'Only eligible, approved stories can appear.', es: 'Solo aparecen historias aprobadas y elegibles.' },
      delivered_count: 105, frame: null,
      teams: [{ id: 'blue', name: 'Club del Faro', color: '#60a5fa' }, { id: 'amber', name: 'Puerto Lumbre FC', color: '#fbbf24' }],
      players: [], cursor: 105,
    });
    await page.route('**/api/replay-sessions/stage-demo/**', route => {
      if (new URL(route.request().url()).pathname.endsWith('/stream')) return route.fulfill({ contentType: 'text/event-stream', body: ': connected\n\n' });
      return route.fulfill({ json: snapshot() });
    });
    await page.goto('/watch/stage-demo');
    const stage = page.getByRole('region', { name: 'Match centre' });
    await expect(stage.getByText('1 : 0', { exact: true })).toBeVisible();
    await expect(stage.getByText('Source-confirmed score', { exact: true })).toHaveCount(0);
    await expect(stage.getByText('Pitch view', { exact: true })).toHaveCount(0);
    await expect(stage.getByText('Observed positions', { exact: true })).toHaveCount(0);
    await expect(stage.getByText('Producer approved', { exact: true })).toHaveCount(0);
    await expect(stage.getByText('No observed team control')).toBeVisible();
    await expect(stage.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '105000');
    const policy = stage.locator('summary');
    await policy.focus();
    await page.keyboard.press('Enter');
    await expect(stage.getByText(/Explanations require producer approval/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    corrected = true;
    await expect(stage.getByText('0 : 0', { exact: true })).toBeVisible({ timeout: 6000 });
    await page.getByLabel('Language', { exact: true }).selectOption('es');
    await expect(page.getByRole('region', { name: 'Centro del partido' }).getByText('Marcador confirmado por la fuente', { exact: true })).toHaveCount(0);
    await expect(page.getByText('Sin control de equipo observado')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  });
}

test('keeper kits use recorded roles and the linked ball preserves the observed coordinate', async ({ page }) => {
  const snapshot = {
    session_id: 'marker-demo', clock_ms: 105000, duration_ms: 240000, running: false, speed: 1,
    mode: 'Local deterministic workflow', story: null, stories: [], story_status: 'none', overlay: null,
    delivered_count: 1, cursor: 1,
    teams: [{ id: 'blue', name: 'Club del Faro', color: '#60a5fa' }, { id: 'amber', name: 'Puerto Lumbre FC', color: '#fbbf24' }],
    players: [
      { id: 'blue-01', team_id: 'blue', number: 1, name: 'Home Keeper', role: 'keeper' },
      { id: 'amber-01', team_id: 'amber', number: 1, name: 'Away Keeper', role: 'keeper' },
      { id: 'blue-09', team_id: 'blue', number: 9, name: 'Forward', role: 'outfield' },
    ],
    frame: { players: [
      { player_id: 'blue-01', team_id: 'blue', x_m: 10, y_m: 6 },
      { player_id: 'amber-01', team_id: 'amber', x_m: 90, y_m: 24 },
      { player_id: 'blue-09', team_id: 'blue', x_m: 55, y_m: 33 },
    ], ball: { x_m: 55, y_m: 33 }, controlling_player_id: null, possession_team_id: null },
  };
  await page.route('**/api/replay-sessions/marker-demo/**', route => new URL(route.request().url()).pathname.endsWith('/stream')
    ? route.fulfill({ contentType: 'text/event-stream', body: ': connected\n\n' })
    : route.fulfill({ json: snapshot }));
  await page.goto('/watch/marker-demo');
  const stage = page.getByRole('region', { name: 'Match centre' });
  await expect(stage.getByText('FAR goalkeeper', { exact: true })).toBeVisible();
  const home = stage.locator('[data-player-id="blue-01"]');
  const away = stage.locator('[data-player-id="amber-01"]');
  await expect(home).toHaveAttribute('data-role', 'keeper');
  await expect(home.locator('rect')).toHaveCount(1);
  await expect(away.locator('rect')).toHaveCount(1);
  expect(await home.locator('rect').getAttribute('fill')).not.toEqual(await away.locator('rect').getAttribute('fill'));
  await home.hover();
  await expect(stage.getByText('Player #1 Home Keeper · Club del Faro · Goalkeeper', { exact: true })).toBeVisible();
  // The fixture's awkward keeper positions remain recorded positions, not silently relocated.
  await expect(home.locator('text')).toHaveAttribute('x', '15');
  await expect(home.locator('text')).toHaveAttribute('y', '11.42');
  await expect(stage.getByTestId('ball-observed-position')).toHaveAttribute('cx', '60');
  await expect(stage.getByTestId('ball-observed-position')).toHaveAttribute('cy', '38');
  await expect(stage.getByTestId('ball-position-link')).toHaveAttribute('x1', '60');
  expect(await stage.getByTestId('ball-symbol').getAttribute('cx')).not.toEqual('60');
  await expect(stage.locator('[data-player-id="blue-09"] text')).toHaveText('9');
  const forward = stage.getByRole('button', { name: 'Player #9, Forward, Club del Faro' });
  await forward.focus();
  await page.keyboard.press('Enter');
  await expect(forward).toHaveAttribute('aria-pressed', 'true');
  await expect(stage.getByText('Player #9 Forward · Club del Faro', { exact: true })).toBeVisible();
  await forward.click();
  await page.mouse.move(0, 0);
  await expect(forward).toHaveAttribute('aria-pressed', 'false');
  await expect(stage.getByText('Select a player to see their name, number and role.', { exact: true })).toBeVisible();
  await page.getByLabel('Language', { exact: true }).selectOption('es');
  await expect(page.getByText('Portero FAR', { exact: true })).toBeVisible();
});

for (const width of [390, 1440]) test(`carrier badge keeps two-digit numbers clear and releases to the observed ball at ${width}`, async ({ page }) => {
  await page.setViewportSize({width,height:1000});
  let control: string | null='blue-11';
  let ball: {x_m:number;y_m:number} | null={x_m:55,y_m:33};
  const snapshot=()=>({session_id:'carrier-demo',clock_ms:1000,duration_ms:240000,running:false,speed:1,mode:'Local deterministic workflow',story:null,stories:[],story_status:'none',overlay:null,delivered_count:1,cursor:1,teams:[],players:[],frame:{players:[{player_id:'blue-11',team_id:'blue',x_m:55,y_m:33},{player_id:'blue-10',team_id:'blue',x_m:57.3,y_m:34.8}],ball,controlling_player_id:control,possession_team_id:control?'blue':null}});
  await page.route('**/api/replay-sessions/carrier-demo/**',route=>new URL(route.request().url()).pathname.endsWith('/stream')?route.fulfill({contentType:'text/event-stream',body:': connected\n\n'}):route.fulfill({json:snapshot()}));
  await page.goto('/watch/carrier-demo');
  const stage=page.getByRole('region',{name:'Match centre'});
  const marker=stage.getByTestId('broadcast-ball');
  await expect(marker).toHaveAttribute('data-carrier-id','blue-11');
  await expect(marker).toHaveAttribute('data-source-x','55');
  await expect(marker).toHaveAttribute('data-source-y','33');
  await expect(stage.getByTestId('ball-position-link')).toHaveCount(0);
  await expect(stage.getByTestId('ball-observed-position')).toHaveCount(0);
  await expect(stage.getByText('The ball badge identifies the observed ball carrier.')).toBeVisible();
  const ballBox=(await stage.getByTestId('ball-symbol').boundingBox())!;
  for(const id of ['blue-11','blue-10']){
    const number=stage.locator(`[data-player-id="${id}"] text`);
    await expect(number).toHaveText(id==='blue-11'?'11':'10');
    const box=(await number.boundingBox())!;
    expect(ballBox.x+ballBox.width<=box.x || box.x+box.width<=ballBox.x || ballBox.y+ballBox.height<=box.y || box.y+box.height<=ballBox.y).toBeTruthy();
  }
  // No inferred carrier from proximity; without a controller use source coordinates.
  control=null;ball={x_m:70,y_m:33};
  await expect(marker).not.toHaveAttribute('data-carrier-id');
  await expect(stage.getByTestId('ball-symbol')).toHaveAttribute('cx','75');
  await expect(stage.getByTestId('controlled-player-indicator')).toHaveCount(0);
  ball=null;
  await expect(marker).toHaveCount(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
