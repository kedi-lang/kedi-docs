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
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  async function copyMarkdown(button, markdownUrl) {
    button.disabled = true;
    try {
      const response = await fetch(markdownUrl, {
        headers: { Accept: "text/markdown" }
      });
      if (!response.ok) {
        throw new Error(`Markdown request failed with ${response.status}`);
      }
      const markdown = await response.text();
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(markdown);
      } else {
        copyFallback(markdown);
      }
      button.classList.add("is-copied");
      button.querySelector("span").textContent = "Copied";
    } catch {
      button.classList.add("has-error");
      button.querySelector("span").textContent = "Copy failed";
    } finally {
      window.setTimeout(() => {
        button.disabled = false;
        button.classList.remove("is-copied", "has-error");
        button.querySelector("span").textContent = COPY_LABEL;
      }, 1800);
    }
  }

  function addCopyMarkdownAction() {
    const article = document.querySelector(".md-content__inner");
    const alternate = document.querySelector(
      'link[rel="alternate"][type="text/markdown"]'
    );
    if (!article || !alternate || article.querySelector(".kedi-copy-markdown")) {
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
      `<span>${COPY_LABEL}</span>`
    ].join("");
    button.addEventListener("click", () => {
      void copyMarkdown(button, alternate.href);
    });
    article.prepend(button);
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(addCopyMarkdownAction);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addCopyMarkdownAction);
  } else {
    addCopyMarkdownAction();
  }
})();
