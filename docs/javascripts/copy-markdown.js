(function () {
  "use strict";

  const COPY_LABEL = "Copy as Markdown";

  function copyFallback(markdown) {
    const textarea = document.createElement("textarea");
    textarea.value = markdown;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    const focused = document.activeElement;
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    focused?.focus();
    if (!copied) throw new Error("Clipboard unavailable");
  }

  // The current page's Markdown: read when clicked, since instant navigation swaps pages without reloading
  // the head this script first saw.
  function markdownPath() {
    const alternate = document.querySelector(
      'link[rel="alternate"][type="text/markdown"]',
    );
    const here = location.pathname.replace(/\/(index\.html)?$/, "");
    const path = alternate ? new URL(alternate.href, location.href).pathname : "";
    return path.replace(/\.md$/, "") === here ? path : `${here}.md`;
  }

  // Safari (WebKit) lets a page write to the clipboard only within the click: a write started after an awaited
  // fetch is refused. So the write starts in the click, with the Markdown as a promise of its contents.
  async function copyMarkdown(button) {
    button.disabled = true;
    const markdown = fetch(markdownPath(), {
      headers: { Accept: "text/markdown" },
    }).then((response) => {
      if (!response.ok) {
        throw new Error(`Markdown request failed with ${response.status}`);
      }
      return response.text();
    });
    try {
      let copied = false;
      if (navigator.clipboard && window.isSecureContext) {
        try {
          if (window.ClipboardItem && navigator.clipboard.write) {
            const blob = markdown.then(
              (text) => new Blob([text], { type: "text/plain" }),
            );
            await navigator.clipboard.write([
              new ClipboardItem({ "text/plain": blob }),
            ]);
          } else {
            await navigator.clipboard.writeText(await markdown);
          }
          copied = true;
        } catch {
          copied = false;
        }
      }
      if (!copied) copyFallback(await markdown);
      button.classList.add("is-copied");
      button.querySelector("span").textContent = "Copied";
      button.setAttribute("aria-label", "Copied");
    } catch {
      button.classList.add("has-error");
      button.querySelector("span").textContent = "Copy failed";
      button.setAttribute("aria-label", "Copy failed");
    } finally {
      window.setTimeout(() => {
        button.disabled = false;
        button.classList.remove("is-copied", "has-error");
        button.querySelector("span").textContent = COPY_LABEL;
        button.setAttribute("aria-label", COPY_LABEL);
      }, 1800);
    }
  }

  function addCopyMarkdownAction() {
    const article = document.querySelector(".md-content__inner");
    const alternate = document.querySelector(
      'link[rel="alternate"][type="text/markdown"]',
    );
    if (
      !article ||
      !alternate ||
      article.querySelector(".kedi-copy-markdown")
    ) {
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "kedi-copy-markdown";
    button.setAttribute("aria-label", COPY_LABEL);
    button.innerHTML = [
      '<svg viewBox="0 0 24 24" aria-hidden="true">',
      '<rect width="13" height="13" x="9" y="9" rx="2"></rect>',
      '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>',
      "</svg>",
      `<span>${COPY_LABEL}</span>`,
    ].join("");
    button.addEventListener("click", () => {
      void copyMarkdown(button);
    });
    const actions = article.querySelector(".kedi-page-actions");
    if (actions) actions.append(button);
    else article.prepend(button);
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(addCopyMarkdownAction);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addCopyMarkdownAction);
  } else {
    addCopyMarkdownAction();
  }
})();
