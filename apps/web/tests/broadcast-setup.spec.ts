import { test, expect } from "@playwright/test";
import { companionUrl, publicOrigin } from "../lib/broadcast-links";

test("public companion URLs exclude local hosts, credentials and ambiguous base paths", () => {
  for (const value of [
    "http://matchsense.example.com",
    "https://localhost",
    "https://127.0.0.1",
    "https://192.168.1.3",
    "https://[::1]",
    "https://matchsense.local",
    "https://matchsense.internal",
    "https://demo.home.arpa",
    "https://user:secret@matchsense.example.com",
    "https://matchsense.example.com/path",
    "https://matchsense.example.com?token=x",
    "javascript:alert(1)",
  ])
    expect(publicOrigin(value)).toBeNull();
  expect(companionUrl("", "http://127.0.0.1:3190", "session-1")).toBeNull();
  expect(
    companionUrl(
      "https://matchsense.example.com",
      "http://127.0.0.1:3190",
      "session-1",
    ),
  ).toBe("https://matchsense.example.com/watch/session-1");
  expect(companionUrl("", "https://matchsense.example.com", "session-1")).toBe(
    "https://matchsense.example.com/watch/session-1",
  );
});

test("main producer demo exposes same-session OBS links, clipboard feedback and honest connection status", async ({
  page,
  request,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const response = await request.post("/api/replay-sessions", {
    headers: { "X-Producer-Token": "local-demo-producer" },
    data: {
      match_id: "match-0c0a000000000005",
      mode: "guided",
      execution: "template",
    },
  });
  expect(response.ok()).toBeTruthy();
  const { session_id: id } = await response.json();
  await page.addInitScript(() =>
    sessionStorage.setItem("why-now-token", "local-demo-producer"),
  );
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(`/studio/${id}`);
  const button = page.getByRole("button", {
    name: "Prepare broadcast",
    exact: true,
  });
  await expect(button).toHaveAttribute("aria-expanded", "false");
  await button.click();
  const panel = page.getByRole("region", {
    name: "Prepare broadcast",
    exact: true,
  });
  await expect(
    panel.getByText("App feed connected", { exact: true }),
  ).toBeVisible();
  await expect(
    panel.getByText("Template rehearsal:", { exact: false }),
  ).toBeVisible();
  await expect(
    panel.getByText(
      "App connection does not confirm OBS or YouTube delivery.",
      { exact: false },
    ),
  ).toBeVisible();
  for (const [label, path] of [
    ["Broadcast stage", "broadcast"],
    ["OBS overlay", "overlay"],
    ["Viewer companion", "watch"],
  ]) {
    const link = panel.getByRole("link", {
      name: `Open ${label}`,
      exact: true,
    });
    await expect(link).toHaveAttribute("href", new RegExp(`/${path}/${id}$`));
    await panel
      .getByRole("button", { name: `Copy ${label} link`, exact: true })
      .click();
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    expect(copied).toMatch(new RegExp(`/${path}/${id}$`));
  }
  await expect(panel.getByTestId("companion-qr")).toHaveCount(0);
  await expect(
    panel.getByText("Companion QR is not available locally"),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../../.run/broadcast-setup-mobile.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await panel.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "../../.run/broadcast-setup-desktop.png",
    fullPage: true,
  });
  await page.goto(`/broadcast/${id}`);
  await expect(
    page.getByText("Local broadcast rehearsal", { exact: false }),
  ).toBeVisible();
  await expect(page.getByTestId("companion-qr")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("clipboard failure leaves manually selectable session links", async ({
  page,
  request,
}) => {
  const created = await (
    await request.post("/api/replay-sessions", {
      headers: { "X-Producer-Token": "local-demo-producer" },
      data: { match_id: "match-001", mode: "guided", execution: "template" },
    })
  ).json();
  await page.addInitScript(() => {
    sessionStorage.setItem("why-now-token", "local-demo-producer");
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: () => Promise.reject(new Error("denied")) },
    });
  });
  await page.goto(`/studio/${created.session_id}`);
  await page
    .getByRole("button", { name: "Prepare broadcast", exact: true })
    .click();
  const panel = page.getByRole("region", {
    name: "Prepare broadcast",
    exact: true,
  });
  await panel
    .getByRole("button", { name: "Copy Broadcast stage link", exact: true })
    .click();
  await expect(panel.getByRole("alert")).toContainText("Select the link");
  await expect(
    panel.getByRole("link", { name: "Open Broadcast stage" }),
  ).toHaveAttribute("href", new RegExp(`/broadcast/${created.session_id}$`));
});

test("configured public origin produces a QR for the exact same session in setup and on the broadcast", async ({
  page,
  request,
}) => {
  test.skip(
    !process.env.PUBLIC_PREVIEW_URL,
    "Requires a second frontend with MATCHSENSE_PUBLIC_URL set.",
  );
  const created = await (
    await request.post("/api/replay-sessions", {
      headers: { "X-Producer-Token": "local-demo-producer" },
      data: { match_id: "match-001", mode: "guided", execution: "template" },
    })
  ).json();
  const base = process.env.PUBLIC_PREVIEW_URL!;
  await page.addInitScript(() =>
    sessionStorage.setItem("why-now-token", "local-demo-producer"),
  );
  await page.goto(`${base}/studio/${created.session_id}`);
  await page
    .getByRole("button", { name: "Prepare broadcast", exact: true })
    .click();
  const qr = page.getByTestId("companion-qr");
  const expected = `https://matchsense.example.com/watch/${created.session_id}`;
  await expect(qr.getByRole("link")).toHaveAttribute("href", expected);
  await expect(qr.locator("svg path")).not.toHaveCount(0);
  await page.goto(`${base}/broadcast/${created.session_id}`);
  await expect(
    page.getByTestId("companion-qr").getByRole("link"),
  ).toHaveAttribute("href", expected);
  await page.screenshot({
    path: "../../.run/broadcast-public-qr.png",
    fullPage: true,
  });
});
