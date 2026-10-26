import { test, expect } from "@playwright/test";

test("prepared example works without the service and keeps facts across languages", async ({
  page,
}) => {
  await page.route("**/api/health", (r) => r.abort());
  await page.route("**/api/matches", (r) => r.abort());
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "One pass. Fewer opponents nearby." }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Experience", { exact: true }),
  ).not.toBeVisible();
  await page
    .getByRole("button", { name: "Check the evidence", exact: true })
    .click();
  await expect(
    page.getByText("Observed coverage: 100% in both windows."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Ejemplo en español" }).click();
  await page.getByRole("button", { name: "Ver detalle", exact: true }).click();
  await expect(
    page.getByText("El pase avanzó 30 m.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("Cobertura observada: 100% en ambas ventanas."),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../../.run/product-entry-mobile.png",
    fullPage: true,
  });
});

test("AI unavailable has an explicit working template alternative", async ({
  page,
}) => {
  await page.route("**/api/health", (r) =>
    r.fulfill({
      json: { mode: "local deterministic template", live_ai_configured: false },
    }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Start live simulation", exact: true }),
  ).toBeEnabled();
  await page.getByText("Demo options", { exact: true }).click();
  await page.getByLabel("Explanations", { exact: true }).selectOption("ai");
  await expect(
    page.getByRole("button", { name: "Start live simulation", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Use template preview instead" })
    .click();
  await expect(
    page.getByRole("button", { name: "Start live simulation", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Prepared wording · no AI calls")).toBeVisible();
  await page.screenshot({
    path: "../../.run/product-entry-desktop.png",
    fullPage: true,
  });
});

test("expired session offers recovery instead of a stale match desk", async ({
  page,
}) => {
  await page.route("**/api/replay-sessions/missing/snapshot*", (r) =>
    r.fulfill({ status: 404, json: { detail: { code: "unknown session" } } }),
  );
  await page.goto("/studio/missing");
  await expect(
    page.getByRole("heading", { name: "This replay is no longer available." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Suggested insights", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "Return to demo", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Explain the match. Let fans enjoy it.",
  );
});

test("listening is opt-in and stops when the example language changes", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const state = { spoken: "", canceled: 0 };
    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      value: class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    });
    Object.assign(window, { speechTest: state });
    Object.defineProperty(window, "speechSynthesis", {
      value: {
        speak: (u: SpeechSynthesisUtterance) => {
          state.spoken = u.text;
        },
        cancel: () => {
          state.canceled++;
        },
        pause: () => {},
        resume: () => {},
      },
    });
  });
  await page.goto("/");
  await expect(
    page.getByRole("button", {
      name: "Listen to approved explanation",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { speechTest: { spoken: string } }).speechTest
          .spoken,
    ),
  ).toBe("");
  await page
    .getByRole("button", {
      name: "Listen to approved explanation",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Pause audio", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Ejemplo en español" }).click();
  await expect(
    page.getByRole("button", {
      name: "Escuchar explicación aprobada",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { speechTest: { canceled: number } }).speechTest
          .canceled,
    ),
  ).toBeGreaterThan(0);
});
