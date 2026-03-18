import { expect, test, type Page } from "@playwright/test";

const defaultBoardState = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
};

const login = async (page: Page) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /sign in to kanban studio/i })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

const resetBoard = async (page: Page) => {
  const response = await page.request.put("/api/boards/main", {
    data: { state: defaultBoardState },
  });
  expect(response.ok()).toBeTruthy();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

const waitForBoardSave = async (page: Page) => {
  await page.waitForResponse(
    (response) =>
      response.url().includes("/api/boards/main") &&
      response.request().method() === "PUT" &&
      response.status() === 200
  );
};

test("loads the kanban board", async ({ page }) => {
  await login(page);
  await resetBoard(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("persists added card after refresh", async ({ page }) => {
  await login(page);
  await resetBoard(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await waitForBoardSave(page);
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await expect(page.getByText("Playwright card")).toBeVisible();
});

test("persists card movement after refresh", async ({ page }) => {
  await login(page);
  await resetBoard(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await waitForBoardSave(page);
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();

  await page.reload();
  await expect(page.getByTestId("column-col-review").getByTestId("card-card-1")).toBeVisible();
});

test("persists renamed column after refresh", async ({ page }) => {
  await login(page);
  await resetBoard(page);

  const firstColumn = page.getByTestId("column-col-backlog");
  const titleInput = firstColumn.getByLabel("Column title");
  await titleInput.fill("Roadmap");
  await waitForBoardSave(page);
  await expect(firstColumn.getByLabel("Column title")).toHaveValue("Roadmap");

  await page.reload();
  await expect(page.getByTestId("column-col-backlog").getByLabel("Column title")).toHaveValue(
    "Roadmap"
  );
});

test("ai chat updates board state in UI", async ({ page }) => {
  await login(page);
  await resetBoard(page);

  await page.route("**/api/ai/chat", async (route) => {
    const updatedState = JSON.parse(JSON.stringify(defaultBoardState));
    updatedState.columns[0].title = "AI Roadmap";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: "openai/gpt-oss-120b:free",
        boardKey: "main",
        assistantResponse: "Renamed Backlog to AI Roadmap.",
        boardUpdated: true,
        state: updatedState,
        warning: null,
      }),
    });
  });

  await page
    .getByPlaceholder("Example: Move card-1 to Review and rename Backlog to Roadmap.")
    .fill("Rename backlog to AI Roadmap");
  await page.getByRole("button", { name: /send to ai/i }).click();

  await expect(page.getByText("Renamed Backlog to AI Roadmap.")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByLabel("Column title")).toHaveValue(
    "AI Roadmap"
  );
});

test("logs out and returns to login screen", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in to kanban studio/i })).toBeVisible();
});
