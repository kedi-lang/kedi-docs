const { test, expect } = require("@playwright/test");
const legacyRoutes = require("../fixtures/legacy-routes.json");
const currentRoutes = Object.keys(legacyRoutes).map((route) => route.replace(/^\/docs/, "") || "/");
const categories = ["Learn Kedi", "Language Reference", "Modules and Packages", "Agents and Orchestration", "Context and Runtime", "Python API", "Models and Integrations", "Testing and Optimization", "Tools and Environments", "Cookbook", "Benchmarks"];
const localOrigin = "http://127.0.0.1:8794";

const article = "/core-language/templates-and-invokes/";
const pages = [
  "/",
  article,
  "/agent-adapters/typesafe/",
  "/reference/capability-matrix/",
];

async function keepCanonicalRequestsLocal(context) {
  await context.route("https://docs.kedi-lang.org/**", async (route) => {
    const url = new URL(route.request().url());
    const response = await route.fetch({
      url: `${localOrigin}${url.pathname}${url.search}`,
    });
    await route.fulfill({
      response,
      headers: { ...response.headers(), "access-control-allow-origin": "*" },
    });
  });
}

test.beforeEach(async ({ context }) => {
  await keepCanonicalRequestsLocal(context);
});

for (const width of [390, 1440]) {
  test(`${width}px: navigation mascot sits above the chapters without a duplicate shortcut`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(article);
    if (width < 1220) {
      await page.getByRole("button", { name: "Open navigation" }).click();
    }
    const mascot = page.locator(".kedi-nav-title .kedi-nav-mascot");
    await expect(mascot).toBeInViewport();
    expect(await mascot.evaluate((img) => img.complete && img.naturalWidth > 0)).toBe(true);
    const picture = await mascot.boundingBox();
    const home = await page.locator(".md-nav--primary > .md-nav__list > li").first().boundingBox();
    expect(picture.y + picture.height).toBeLessThanOrEqual(home.y);
    await expect(page.locator('.md-nav--primary a[href*="reference/syntax/"]')).toHaveCount(1);
    await expect(page.locator(".kedi-nav-colophon")).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath("navigation-mascot.png") });
  });
}

for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
  for (const colorScheme of ["light", "dark"]) {
    test(`${width}px ${colorScheme}: reading layout, tables and assets`, async ({
      browser,
    }, info) => {
      const context = await browser.newContext({
        viewport: { width, height: 1000 },
        colorScheme,
      });
      await keepCanonicalRequestsLocal(context);
      const page = await context.newPage();
      const errors = [];
      const failedAssets = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("response", (response) => {
        if (
          response.status() >= 400 &&
          response.url().startsWith(`${localOrigin}/`)
        ) {
          failedAssets.push(`${response.status()} ${response.url()}`);
        }
      });
      for (const path of pages) {
        await page.goto(`${localOrigin}${path}`);
        await expect(page.locator(".kedi-page-meta")).toBeVisible();
        await page.evaluate(() => document.fonts.ready);
        await expect(page.locator("article h1")).toBeVisible();
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
        expect(
          await page
            .locator("img")
            .evaluateAll((images) =>
              images.every(
                (image) =>
                  image.loading === "lazy" ||
                  (image.complete && image.naturalWidth > 0),
              ),
            ),
        ).toBe(true);
        expect(
          await page
            .locator('[contenteditable="true"]', { hasText: "" })
            .count(),
        ).toBe(0);
        if (path === "/")
          await expect(page.locator(".kedi-directory li")).toHaveCount(categories.length);
        if (path === article) {
          await expect(page.locator(".kedi-code-frame")).toHaveCount(5);
          await expect(
            page.locator(".kedi-code-frame .md-code__button").first(),
          ).toBeHidden();
          if (width >= 1220) {
            await expect(page.locator(".md-sidebar--primary")).toBeVisible();
            await expect(page.locator(".kedi-mobile-toc")).toBeHidden();
            const sidebar = await page
              .locator(".md-sidebar--primary")
              .boundingBox();
            const content = await page.locator(".md-content").boundingBox();
            expect(sidebar.x + sidebar.width).toBeLessThanOrEqual(content.x);
          }
        }
        if (
          (width === 390 || width === 1440) &&
          (path === article || path === "/")
        ) {
          await page.screenshot({
            path: info.outputPath(
              path === article ? "article.png" : "index.png",
            ),
          });
        }
      }
      expect(errors).toEqual([]);
      expect(failedAssets).toEqual([]);
      await context.close();
    });
  }
}

test("navigation retains open groups across instant navigation and reloads", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(article);
  await page
    .locator('label[aria-label="Toggle Testing and Optimization"]')
    .click();
  await page.locator('label[aria-label="Toggle Context and Runtime"]').click();
  await page.locator('label[aria-label="Toggle Execution"]').click();
  await expect(
    page.locator('label[aria-label="Toggle Context and Runtime"]'),
  ).toHaveAttribute("aria-expanded", "true");
  await page.evaluate(() => {
    window.manualNavigationTest = true;
  });
  await page
    .locator(".md-nav--primary")
    .getByRole("link", { name: "Concurrency", exact: true })
    .click();
  await expect(page).toHaveURL(/runtime\/concurrency\/$/);
  await expect(page.locator("article h1")).toHaveText(/^Concurrency(?:¶)?$/);
  expect(await page.evaluate(() => window.manualNavigationTest)).toBe(true);
  await expect(
    page.locator('label[aria-label="Toggle Testing and Optimization"]'),
  ).toHaveAttribute("aria-expanded", "true");
  await page.reload();
  await expect(
    page.locator('label[aria-label="Toggle Testing and Optimization"]'),
  ).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator(".kedi-copy-markdown")).toHaveCount(1);
  await expect(page.locator(".kedi-code-frame .kedi-code-frame")).toHaveCount(
    0,
  );
});

test("copying a source block does not include its title or controls", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(article);
  const code = page.locator(".kedi-code-frame pre > code").first();
  const source = await code.textContent();
  await page.locator(".kedi-code-copy").first().click();
  await expect(page.locator(".kedi-code-copy").first()).toHaveAttribute(
    "aria-label",
    "Copied",
  );
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    source,
  );
});

test("Markdown copy uses the served docs base and retains source syntax", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(article);
  const request = page.waitForRequest((request) =>
    request.url().endsWith("/core-language/templates-and-invokes.md"),
  );
  await page.locator(".kedi-copy-markdown").click();
  await request;
  await expect(page.locator(".kedi-copy-markdown")).toHaveClass(/is-copied/);
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(
    "# Templates and Invokes",
  );
});

test("mobile navigation and page contents are separate and usable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(article);
  await page.locator(".kedi-menu-toggle").focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#__drawer")).toBeChecked();
  await expect(page.locator(".kedi-nav-title")).toBeVisible();
  await page.getByRole("button", { name: "Close navigation" }).click();
  await expect(page.locator("#__drawer")).not.toBeChecked();
  await page.locator(".kedi-mobile-toc > summary").click();
  await page
    .locator(".kedi-mobile-toc a")
    .filter({ hasText: "Raw Model Invokes" })
    .click();
  await expect(page).toHaveURL(/#raw-model-invokes-with/);
  await expect(page.locator(".kedi-mobile-toc")).not.toHaveAttribute("open");
  await expect(page.locator("h2#raw-model-invokes-with")).toBeInViewport();
});

test("Markdown copy follows instant navigation to the new page", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(article);
  await page.locator(".md-nav--primary").getByRole("link", { name: "Substitutions and Calls", exact: true }).click();
  await expect(page).toHaveURL(/substitutions-and-calls\/$/);
  await page.locator(".kedi-copy-markdown").click();
  await expect(page.locator(".kedi-copy-markdown")).toHaveClass(/is-copied/);
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain("# Substitutions and Calls");
});

test("mobile drawer opens and closes using Space", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(article);
  const open = page.getByRole("button", { name: "Open navigation" });
  await open.focus();
  await page.keyboard.press("Space");
  await expect(page.locator("#__drawer")).toBeChecked();
  await expect(open).toHaveAttribute("aria-expanded", "true");
  await expect.poll(async () => (await page.locator(".md-sidebar--primary").boundingBox()).x).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: info.outputPath("mobile-navigation.png") });
  await page.getByRole("button", { name: "Close navigation" }).focus();
  await page.keyboard.press("Space");
  await expect(page.locator("#__drawer")).not.toBeChecked();
  await expect(open).toHaveAttribute("aria-expanded", "false");
  await page.locator(".md-footer__link--next").click();
  await expect(page).toHaveURL(/substitutions-and-calls\/$/);
  await expect(page.locator("article h1")).toHaveText(/^Substitutions and Calls(?:¶)?$/);
  // Zensical 0.0.51 closes drawers on a 125ms debounced location event.
  await page.waitForTimeout(200);
  await open.focus();
  await page.keyboard.press("Space");
  await expect(page.locator("#__drawer")).toBeChecked();
  await page.getByRole("button", { name: "Close navigation" }).focus();
  await page.keyboard.press("Space");
  await expect(page.locator("#__drawer")).not.toBeChecked();
});

test("failed clipboard fallback is not reported as copied", async ({ page }) => {
  await page.goto(article);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", { value: undefined, configurable: true });
    document.execCommand = () => false;
  });
  await page.locator(".kedi-copy-markdown").click();
  await expect(page.locator(".kedi-copy-markdown")).toHaveClass(/has-error/);
  await expect(page.locator(".kedi-copy-markdown")).toHaveAttribute("aria-label", "Copy failed");
  await expect(page.locator(".kedi-copy-markdown")).not.toHaveClass(/is-copied/);
});

test("source and the complete navigation remain readable without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  await page.goto(`${localOrigin}${article}`);
  await expect(page.locator("article h1")).toBeVisible();
  await expect(page.locator("pre.kedi").first()).toContainText(
    "@extract_owner",
  );
  await expect(
    page.locator(".md-nav--primary > .md-nav__list > li"),
  ).toHaveCount(categories.length + 1);
  await context.close();
});

test("every page in the full navigation is published at the documentation root", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const routes = await page
    .locator(".md-nav--primary a[href]")
    .evaluateAll((links) => [
      ...new Set(links.map((link) => new URL(link.href).pathname)),
    ]);
  expect(routes).toEqual(expect.arrayContaining(currentRoutes));
  for (const route of routes) {
    expect(route).toMatch(/^\//);
    const response = await request.get(route);
    expect(response.ok(), route).toBe(true);
    expect(await response.text()).toContain("kedi-page-meta");
  }
});

test("directory counts leaf pages and links even when a chapter has no index", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".kedi-section-description strong")).toHaveText(categories);
  const counts = await page.locator(".kedi-section-description > span").allTextContents();
  const routes = await page.locator(".md-nav--primary a[href]").evaluateAll(
    links => [...new Set(links.map(link => new URL(link.href).pathname))],
  );
  expect(counts.reduce((sum, text) => sum + parseInt(text, 10), 0)).toBe(routes.length - 1);
  await page.locator(".kedi-directory").getByRole("link", { name: /Benchmarks/ }).click();
  await expect(page).toHaveURL(/tooling\/terminal-bench\/$/);
  await expect(page.locator(".kedi-breadcrumb")).toContainText("Benchmarks");
  await expect(page.locator(".kedi-breadcrumb")).toContainText("Terminal-Bench 2.1");
});

for (const width of [390, 1440]) {
  test(`runtime and API reference guides remain readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    for (const path of [
      "runtime/artifact-retrieval", "runtime/prefix-cache",
      "core-language/scopes-and-bindings", "core-language/loops-and-map",
      "python-api/public-parameters", "agent-adapters/jev-workflow",
      "modules-and-packaging/filesystem",
      "evals-and-optimization/validation-workflow",
      "evals-and-optimization/reproducibility",
      "tooling/notebook", "tooling/notebook-runtimes", "tooling/notebook-files",
    ]) {
      await page.goto(`/${path}/`);
      await expect(page.locator("article h1")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    }
    await page.goto("/python-api/query/");
    await expect(page.locator(".kedi-brand")).toHaveText("kedi");
    const code = page.locator("article pre code").filter({ hasText: "def title_for" }).first();
    await expect(code).toBeVisible();
    expect(await code.textContent()).toContain('\n    >> A guide to <topic> could be titled');
    await page.screenshot({ path: `test-results/python-api-${width}.png` });
  });

  for (const [group, paths] of Object.entries({
    cookbook: ["examples", "examples/structured-extraction", "examples/tools-and-approvals",
      "examples/agent-delegation", "examples/evaluation-and-optimization",
      "examples/modules-and-packaging", "examples/complete-program"],
    learning: ["getting-started", "getting-started/installation",
      "getting-started/projects-and-execution", "reference", "getting-started/first-program"],
    benchmarks: ["tooling/terminal-bench", "tooling/terminal-bench-results"],
  })) {
    test(`${group} guides remain readable at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      for (const path of paths) {
        await page.goto(`/${path}/`);
        await expect(page.locator("article h1")).toBeVisible();
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      }
      await page.screenshot({ path: `test-results/${group}-${width}.png` });
    });
  }

  test(`orchestration guides remain readable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    for (const slug of ["subagent-limits", "reviewed-evidence", "tool-reasons", "codemode-sandbox"]) {
      await page.goto(`/agentic-engineering/${slug}/`);
      await expect(page.locator("article h1")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    }
    await page.goto("/agentic-engineering/reviewed-evidence/");
    await expect(page.locator("pre.kedi").first()).toContainText("~Review");
    await page.screenshot({ path: `test-results/orchestration-${width}.png`, fullPage: true });
  });
}

test("unindexed subgroups toggle by keyboard and persist independently", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(article);
  const group = page.locator('label[aria-label="Toggle Values and Types"]');
  await group.focus();
  await page.keyboard.press("Enter");
  await expect(group).toHaveAttribute("aria-expanded", "true");
  await page.reload();
  await expect(group).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator('label[aria-label="Toggle Procedures"]')).toHaveAttribute("aria-expanded", "false");
  await group.focus();
  await page.keyboard.press("Space");
  await expect(group).toHaveAttribute("aria-expanded", "false");
});

for (const width of [390, 1440]) {
  test(`${width}px: search finds reference pages and returns to reading`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(article);
    await page.locator(".md-search__button").click();
    const input = page.getByRole("combobox");
    await expect(input).toBeVisible();
    await input.fill("concurrency");
    await expect(
      page.getByRole("link", { name: /Concurrency/ }).first(),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    // Zensical fades its shadow-root search panel out instead of removing it.
    await expect
      .poll(() =>
        input.evaluate((input) => {
          for (
            let node = input;
            node;
            node = node.parentElement || node.getRootNode().host
          ) {
            if (getComputedStyle(node).opacity === "0") return true;
          }
          return false;
        }),
      )
      .toBe(true);
    await expect(page.locator("#__search")).not.toBeChecked();
    await page.locator("article h1").click();
    await expect(page.locator("article h1")).toBeVisible();
  });
}

test("theme choice persists through navigation and reload", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto(article);
  for (let attempt = 0; attempt < 3; attempt++) {
    if (
      (await page.locator("body").getAttribute("data-md-color-scheme")) ===
      "slate"
    )
      break;
    await page.locator(".md-header__option label:visible").click();
  }
  await expect(page.locator("body")).toHaveAttribute(
    "data-md-color-scheme",
    "slate",
  );
  await page.reload();
  await expect(page.locator("body")).toHaveAttribute(
    "data-md-color-scheme",
    "slate",
  );
});
