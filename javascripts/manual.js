(function () {
  "use strict";

  const installed = Symbol.for("kedi.manual.enhancements");
  if (window[installed]) return;
  window[installed] = true;

  const NAV_STATE = "kedi.manual.navigation.v1";
  const NAV_SCROLL = "kedi.manual.scroll.v1";
  const boundElements = new WeakSet();

  function readState(key, fallback) {
    try {
      return JSON.parse(sessionStorage.getItem(key)) ?? fallback;
    } catch {
      return fallback;
    }
  }

  function writeState(key, value) {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Navigation remains usable when browser storage is disabled.
    }
  }

  // Keep keyboard activation working when instant navigation replaces controls.
  document.addEventListener("keydown", (event) => {
    if (event.key !== " ") return;
    const label = event.target.closest?.("label[for]");
    if (!label || !(label.closest(".md-nav--primary") || label.matches(".kedi-menu-toggle"))) return;
    event.preventDefault();
    event.stopPropagation();
    label.click();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest?.(".kedi-nav-close")) return;
    const drawer = document.querySelector("#__drawer");
    if (!drawer) return;
    drawer.checked = false;
    drawer.dispatchEvent(new Event("change", { bubbles: true }));
    document.querySelector(".kedi-menu-toggle")?.focus();
  });

  function enhanceDrawer() {
    const drawer = document.querySelector("#__drawer");
    if (!drawer) return;
    const selector = ".kedi-menu-toggle, .kedi-nav-close";
    const update = () => document.querySelectorAll(selector).forEach((control) => {
      control.setAttribute("aria-expanded", String(drawer.checked));
    });
    if (!boundElements.has(drawer)) {
      boundElements.add(drawer);
      drawer.addEventListener("change", update);
    }
    update();
  }

  function enhanceNavigation() {
    const nav = document.querySelector(".md-nav--primary");
    const scroll = nav?.closest(".md-sidebar__scrollwrap");
    if (!nav || !scroll || boundElements.has(nav)) return;
    boundElements.add(nav);
    const state = readState(NAV_STATE, {});

    nav.querySelectorAll(".md-nav__toggle").forEach((toggle) => {
      const item = toggle.closest(".md-nav__item--nested");
      const groupLink = item?.querySelector(":scope > .md-nav__container > a");
      if (!item) return;
      const group = item.querySelector(":scope > nav");
      const label = item.querySelector(`label[for="${toggle.id}"]`);
      const title = groupLink?.textContent.trim() || label?.textContent.trim();
      const ancestors = [];
      for (let node = item; node; node = node.parentElement?.closest(".md-nav__item--nested")) {
        const heading = node.querySelector(":scope > .md-nav__container > a, :scope > label.md-nav__link");
        ancestors.unshift(heading?.textContent.trim());
      }
      const key = groupLink ? new URL(groupLink.href).pathname : ancestors.join(" / ");
      label?.setAttribute("role", "button");
      if (item.classList.contains("md-nav__item--active") || state[key]) {
        toggle.checked = true;
      }
      const update = () => {
        const expanded = String(toggle.checked);
        group?.setAttribute("aria-expanded", expanded);
        label?.setAttribute("aria-expanded", expanded);
        label?.setAttribute(
          "aria-label",
          `Toggle ${title}`,
        );
      };
      update();
      toggle.addEventListener("change", () => {
        update();
        const current = readState(NAV_STATE, {});
        current[key] = toggle.checked;
        writeState(NAV_STATE, current);
      });
    });

    scroll.scrollTop = readState(NAV_SCROLL, 0);
    scroll.addEventListener(
      "scroll",
      () => writeState(NAV_SCROLL, scroll.scrollTop),
      { passive: true },
    );
    requestAnimationFrame(() => {
      if (!matchMedia("(min-width: 1220px)").matches) return;
      const active = nav.querySelector("a.md-nav__link--active");
      if (!active) return;
      const bounds = scroll.getBoundingClientRect();
      const target = active.getBoundingClientRect();
      if (target.top < bounds.top || target.bottom > bounds.bottom) {
        scroll.scrollTop += target.top - bounds.top - 90;
      }
    });
  }

  async function copySource(source) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(source);
      return;
    }
    const field = document.createElement("textarea");
    field.value = source;
    field.setAttribute("readonly", "");
    field.style.cssText = "position:fixed;opacity:0;left:-9999px";
    const focused = document.activeElement;
    document.body.append(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    focused?.focus();
    if (!copied) throw new Error("Clipboard unavailable");
  }

  function enhanceCode() {
    const icon = document.querySelector("#kedi-code-copy-icon");
    document
      .querySelectorAll(".md-content__inner pre > code")
      .forEach((code) => {
        if (code.closest(".kedi-code-frame")) return;
        const pre = code.parentElement;
        if (pre.closest(".highlighttable")) return;
        const source = code.textContent;
        const container = pre.parentElement.classList.contains("highlight")
          ? pre.parentElement
          : pre;
        const classes = `${container.className} ${pre.className} ${code.className}`;
        const language =
          classes.match(/language-([\w+-]+)/)?.[1] ||
          (pre.classList.contains("kedi") ? "kedi" : "text");
        const filename = container.querySelector(".filename")?.textContent;
        const names = {
          kedi: "Kedi",
          python: "Python",
          py: "Python",
          bash: "Shell",
          sh: "Shell",
          shell: "Shell",
          json: "JSON",
          toml: "TOML",
          text: "Text",
        };
        const frame = document.createElement("div");
        frame.className = "kedi-code-frame";
        const heading = document.createElement("div");
        heading.className = "kedi-code-heading";
        const label = document.createElement("span");
        label.textContent = filename || names[language] || language;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "kedi-code-copy";
        button.title = "Copy code";
        button.setAttribute("aria-label", "Copy code");
        if (icon) button.append(icon.content.cloneNode(true));
        else button.textContent = "Copy";
        button.addEventListener("click", async () => {
          try {
            await copySource(source);
            button.dataset.copied = "true";
            button.title = "Copied";
            button.setAttribute("aria-label", "Copied");
          } catch {
            button.title = "Copy failed";
            button.setAttribute("aria-label", "Copy failed");
          }
          window.setTimeout(() => {
            delete button.dataset.copied;
            button.title = "Copy code";
            button.setAttribute("aria-label", "Copy code");
          }, 1800);
        });
        heading.append(label, button);
        container.before(frame);
        frame.append(heading, container);
      });
  }

  function addMobileContents() {
    const article = document.querySelector(".md-content__inner");
    const headings = article?.querySelectorAll("h2[id]");
    if (
      !article ||
      !headings.length ||
      article.querySelector(".kedi-mobile-toc, .kedi-manual-home")
    )
      return;
    const details = document.createElement("details");
    details.className = "kedi-mobile-toc";
    const summary = document.createElement("summary");
    summary.textContent = "On this page";
    const icon = document.querySelector("#kedi-chevron-icon");
    if (icon) summary.append(icon.content.cloneNode(true));
    const list = document.createElement("ul");
    headings.forEach((heading) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = `#${heading.id}`;
      link.textContent = [...heading.childNodes]
        .filter(
          (node) =>
            !(node.nodeType === 1 && node.classList.contains("headerlink")),
        )
        .map((node) => node.textContent)
        .join("");
      link.addEventListener("click", () => {
        details.open = false;
      });
      item.append(link);
      list.append(item);
    });
    details.append(summary, list);
    article.querySelector(".kedi-page-meta")?.after(details);
  }

  function enhance() {
    enhanceDrawer();
    enhanceNavigation();
    enhanceCode();
    addMobileContents();
  }

  if (typeof document$ !== "undefined") document$.subscribe(enhance);
  else if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", enhance);
  else enhance();
})();
