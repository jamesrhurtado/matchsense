import { test, expect, APIRequestContext } from "@playwright/test";

test.skip(
  process.env.WHY_NOW_EPISODES_E2E !== "1",
  "Opt-in development data server required.",
);
const headers = { "X-Producer-Token": "local-demo-producer" };

async function create(
  request: APIRequestContext,
  passage: number,
  mode = "guided",
) {
  const catalogue = await (await request.get("/api/matches")).json();
  const match = catalogue.matches.find(
    (m: { label: string }) =>
      m.label === `Development passage ${String(passage).padStart(2, "0")}`,
  );
  expect(match).toBeTruthy();
  const response = await request.post("/api/replay-sessions", {
    headers,
    data: { match_id: match.match_id, mode, execution: "template" },
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()).session_id as string;
}

async function seek(request: APIRequestContext, sid: string, at: number) {
  expect(
    (
      await request.post(`/api/replay-sessions/${sid}/control`, {
        headers,
        data: { action: "seek", clock_ms: at },
      })
    ).ok(),
  ).toBeTruthy();
}

for (const sample of [
  { family: "pass", story: "story-p02", passage: 1, at: 25000 },
  { family: "pressure", story: "story-pressure-p02", passage: 1, at: 25000 },
  { family: "recovery", story: "story-recovery-i01", passage: 3, at: 20000 },
  { family: "shot", story: "story-shot-s01", passage: 5, at: 24000 },
  { family: "goal", story: "story-goal-g01", passage: 8, at: 36000 },
  {
    family: "possession",
    story: "story-possession-60000",
    passage: 9,
    at: 60000,
  },
]) {
  test(`new ${sample.family} scene renders evidence and approved viewer copy on desktop and phone`, async ({
    page,
    context,
    request,
  }) => {
    const sid = await create(request, sample.passage);
    await seek(request, sid, sample.at);
    await page.addInitScript(() =>
      sessionStorage.setItem("why-now-token", "local-demo-producer"),
    );
    await page.goto(`/studio/${sid}`);
    await page
      .getByLabel("Event family", { exact: true })
      .selectOption(sample.family);
    await page
      .getByRole("button", { name: /^Insight \d/ })
      .first()
      .click();
    await expect(
      page.getByRole("button", { name: "Approve", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Show why", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Close evidence", exact: true }),
    ).toBeVisible();
    if (sample.family !== "pass")
      await expect(page.getByTestId("event-evidence")).toBeVisible();
    await page
      .getByRole("button", { name: "Close evidence", exact: true })
      .click();
    await page.getByRole("button", { name: "Approve", exact: true }).click();
    const viewer = await context.newPage();
    await viewer.goto(`/watch/${sid}`);
    const en = await (
      await request.get(
        `/api/replay-sessions/${sid}/stories/${sample.story}/variants?language=en&detail=simple`,
      )
    ).json();
    await expect(viewer.getByTestId("audience-explanation")).toContainText(
      en.text,
    );
    await expect(viewer.getByTestId("match-state")).toContainText(
      `${String(Math.floor(sample.at / 60000)).padStart(2, "0")}:${String((sample.at / 1000) % 60).padStart(2, "0")}`,
    );
    await viewer.getByLabel("Language", { exact: true }).selectOption("es");
    const es = await (
      await request.get(
        `/api/replay-sessions/${sid}/stories/${sample.story}/variants?language=es&detail=simple`,
      )
    ).json();
    await expect(viewer.getByTestId("audience-explanation")).toContainText(
      es.text,
    );
    await viewer.setViewportSize({ width: 390, height: 844 });
    expect(
      await viewer.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await viewer.screenshot({
      path: `../../evals/synthetic-vnext/screenshots/${sample.family}-mobile.png`,
      fullPage: true,
    });
    await viewer
      .getByRole("button", { name: "Ponerme al día", exact: true })
      .click();
    await expect(viewer.getByTestId("catch-up-panel")).not.toBeEmpty();
  });
}

test("90-second mobile stream keeps its clock, withdraws a corrected goal and ends once", async ({
  page,
  request,
}) => {
  test.setTimeout(125000);
  const sid = await create(request, 8, "live");
  const base = `/api/replay-sessions/${sid}`;
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/watch/${sid}`);
    await expect(
      page.getByRole("button", { name: "Match first", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByTestId("match-state")).toContainText("1 : 1");
    await expect
      .poll(
        async () =>
          (
            await (await request.get(`${base}/snapshot`, { headers })).json()
          ).stories.some((s: { id: string }) => s.id === "story-goal-g01"),
        { timeout: 45000 },
      )
      .toBeTruthy();
    const evidence = await (
      await request.get(`${base}/stories/story-goal-g01/evidence`, { headers })
    ).json();
    expect(
      (
        await request.post(`${base}/stories/story-goal-g01/review`, {
          headers,
          data: {
            action: "approve",
            expected_revision: evidence.story.revision,
            package_hash: evidence.story.package_hash,
            idempotency_key: crypto.randomUUID(),
          },
        })
      ).ok(),
    ).toBeTruthy();
    await expect(page.getByTestId("match-state")).toContainText("2 : 1");
    await expect(page.getByTestId("audience-explanation")).toHaveCount(0);
    await page
      .getByRole("button", { name: "Catch me up", exact: true })
      .click();
    await expect(page.getByTestId("catch-up-panel")).toContainText("Beni");
    await expect(page.getByTestId("match-state")).toContainText("1 : 1", {
      timeout: 25000,
    });
    await expect(page.getByTestId("catch-up-panel")).not.toContainText("Beni");
    await expect(page.getByTestId("catch-up-panel")).toContainText("withdrawn");
    await expect
      .poll(
        async () =>
          (await (await request.get(`${base}/snapshot`)).json()).live_status,
        { timeout: 45000 },
      )
      .toBe("complete");
    const final = await (await request.get(`${base}/snapshot`)).json();
    expect(final.clock_ms).toBe(90000);
    expect(final.running).toBe(false);
    expect(final.score).toEqual({ blue: 1, amber: 1 });
    expect(final.session_id).toBe(sid);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: "../../evals/synthetic-vnext/screenshots/continuous-mobile.png",
      fullPage: true,
    });
    const diagnostics = await (
      await request.get(`${base}/diagnostics`, { headers })
    ).json();
    expect(JSON.stringify(diagnostics)).not.toContain(
      "Microsoft Agent Framework + Azure OpenAI",
    );
  } finally {
    await request.post(`${base}/control`, {
      headers,
      data: { action: "stop" },
    });
  }
});
