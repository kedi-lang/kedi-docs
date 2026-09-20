const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/browser",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8794",
    channel: "chrome",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "python3 -m http.server 8794 --bind 127.0.0.1 --directory site",
    url: "http://127.0.0.1:8794/",
    reuseExistingServer: false,
  },
});
