import { test, expect } from "@playwright/test";

for (const width of [1440, 390]) {
  test(`evidence stays in place during incoming updates at ${width}px`, async ({
    page,
    request,
  }) => {
    const headers = { "X-Producer-Token": "local-demo-producer" };
    const created = await request.post("/api/replay-sessions", {
      headers,
      data: {
        match_id: "match-0c0a000000000002",
        mode: "guided",
        execution: "template",
      },
    });
    expect(created.ok()).toBeTruthy();
    const sid = (await created.json()).session_id;
    await request.post(`/api/replay-sessions/${sid}/control`, {
      headers,
      data: { action: "seek", clock_ms: 105000 },
    });
    await page.setViewportSize({ width, height: 950 });
    await page.addInitScript(() =>
      sessionStorage.setItem("why-now-token", "local-demo-producer"),
    );
    let incoming = false;
    await page.route("**/snapshot*", async (route) => {
      const response = await route.fetch();
      const data = await response.json();
      data.workflow_pending = incoming;
      if (incoming) {
        const source = data.stories[0];
        data.stories = [
          ...data.stories,
          ...Array.from({ length: 12 }, (_, i) => ({
            ...source,
            id: `incoming-${i}`,
            incident_id: `incoming-${i}`,
            queue_state: "live",
          })),
        ];
        // Simulate the default selection advancing with incoming candidates.
        if (!new URL(route.request().url()).searchParams.has("story_id"))
          data.story = data.stories[data.stories.length - 1];
        data.overlay =
          "A newly approved explanation with enough text to wrap onto several lines on a small display. The live match keeps running while the producer reads the evidence.";
      }
      await route.fulfill({ response, json: data });
    });
    await page.goto(`/studio/${sid}`);
    await page.getByRole("button", { name: "Show why", exact: true }).click();
    const evidence = page.getByLabel("Evidence for the selected moment", {
      exact: true,
    });
    await expect(evidence).toBeVisible();
    const before = await evidence.boundingBox();
    const queue = await page.getByTestId("producer-insight-list").boundingBox();
    const selected = await page
      .getByRole("group", { name: "Suggested insights", exact: true })
      .locator('[aria-pressed="true"]')
      .textContent();
    incoming = true;
    await expect(page.getByTestId("review-status")).toContainText(
      "AI review in progress",
    );
    await expect(
      page
        .getByRole("group", { name: "Suggested insights", exact: true })
        .locator('[aria-pressed="true"]'),
    ).toHaveText(selected!);
    const after = await evidence.boundingBox();
    expect(Math.abs(after!.y - before!.y)).toBeLessThanOrEqual(1);
    expect(
      (await page.getByTestId("producer-insight-list").boundingBox())!.height,
    ).toBe(queue!.height);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    incoming = false;
    await expect(page.getByTestId("review-status")).toHaveCount(0);
    expect(
      Math.abs((await evidence.boundingBox())!.y - before!.y),
    ).toBeLessThanOrEqual(1);
    await page.screenshot({
      path: `../../.run/reading-stability-${width}.png`,
      fullPage: true,
    });
    await page.unrouteAll({ behavior: "ignoreErrors" });
  });
}
