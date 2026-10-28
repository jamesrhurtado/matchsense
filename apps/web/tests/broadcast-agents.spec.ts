import { test, expect } from "@playwright/test";

const headers = { "X-Producer-Token": "local-demo-producer" };

test("audience question is confirmed, reviewed and published only with the approved insight", async ({
  page,
  request,
}) => {
  const created = await request.post("/api/replay-sessions", {
    headers,
    data: { match_id: "match-001", mode: "guided", execution: "template" },
  });
  expect(created.ok()).toBeTruthy();
  const { session_id: id } = await created.json();
  const path = `/api/replay-sessions/${id}`;
  expect(
    (
      await request.post(`${path}/control`, {
        headers,
        data: { action: "seek", clock_ms: 23000 },
      })
    ).ok(),
  ).toBeTruthy();
  await page.addInitScript(() =>
    sessionStorage.setItem("why-now-token", "local-demo-producer"),
  );
  await page.goto(`/studio/${id}`);
  await page.getByText("Rehearse with simulated questions").click();
  await page
    .getByLabel(
      "One question per line. Each line simulates a different participant.",
    )
    .fill("What changed with that pass?\nWhat changed with that pass?");
  await page.getByRole("button", { name: "Analyze rehearsal" }).click();
  const question = page
    .locator("article")
    .filter({ hasText: "What changed with that pass?" });
  await expect(question).toContainText("2 messages · 2 participants");
  await expect(question).toContainText("Original chat message");
  await expect(question).toContainText("Grouping note");
  await expect(question).not.toContainText(
    "Show question and approved insight",
  );
  await question
    .getByRole("button", { name: "Confirm moment and review" })
    .click();
  await expect(page.locator("#selected-insight")).toContainText(
    "Ready for review",
  );
  await page
    .getByRole("button", { name: "Approve for viewers", exact: true })
    .click();
  await expect(
    question.getByRole("button", {
      name: "Show question and approved insight",
    }),
  ).toBeVisible();
  await question
    .getByRole("button", { name: "Show question and approved insight" })
    .click();
  const state = await (await request.get(`${path}/snapshot`)).json();
  expect(state.overlay_question).toBe("What changed with that pass?");
  const broadcast = await page.context().newPage();
  await broadcast.goto(`/overlay/${id}`);
  await expect(
    broadcast.getByText("What changed with that pass?", { exact: true }),
  ).toBeVisible();
});

test("broadcast producer recommends an eligible insight for human review", async ({
  page,
  request,
}) => {
  const created = await request.post("/api/replay-sessions", {
    headers,
    data: { match_id: "match-001", mode: "guided", execution: "template" },
  });
  expect(created.ok()).toBeTruthy();
  const { session_id: id } = await created.json();
  const path = `/api/replay-sessions/${id}`;
  expect(
    (
      await request.post(`${path}/control`, {
        headers,
        data: { action: "seek", clock_ms: 23000 },
      })
    ).ok(),
  ).toBeTruthy();
  await page.addInitScript(() =>
    sessionStorage.setItem("why-now-token", "local-demo-producer"),
  );
  await page.goto(`/studio/${id}`);
  await page
    .getByRole("button", { name: "Recommend next action" })
    .click();
  await expect(page.getByRole("status").filter({ hasText: "Show" })).toContainText(
    "Non-AI rules",
  );
  await expect(
    page.getByRole("button", { name: "Review recommendation" }),
  ).toBeVisible();
});
