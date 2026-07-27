(function () {
  "use strict";

  const KEDI_DIRECTIVES = new Set([
    "adapter", "agent", "model", "effort", "approval", "system", "settings",
    "profile", "subagent", "max_agents", "mcp", "use", "import", "export",
    "package", "case", "data", "test_data", "metric", "optimize", "auto"
  ]);
  const KEDI_TYPES = new Set([
    "Any", "Annotated", "Literal", "Optional", "Union", "str", "int", "float",
    "bool", "bytes", "object", "list", "dict", "tuple", "set", "datetime",
    "date", "time", "timedelta", "Regex", "Email", "HttpUrl", "FileUrl"
  ]);
  const PYTHON_KEYWORDS = new Set([
    "and", "as", "assert", "async", "await", "break", "case", "class",
    "continue", "def", "del", "elif", "else", "except", "finally", "for",
    "from", "global", "if", "import", "in", "is", "lambda", "match",
    "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
    "with", "yield"
  ]);
  const PYTHON_BUILTINS = new Set([
    "bool", "bytes", "dict", "enumerate", "filter", "float", "int", "len",
    "list", "map", "max", "min", "object", "open", "print", "range", "set",
    "sorted", "str", "sum", "tuple", "type", "zip"
  ]);

  function escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function token(value, className) {
    return `<span class="${className}">${escapeHtml(value)}</span>`;
  }

  function highlightInline(source, python) {
    let output = "";
    let offset = 0;
    const pattern = /\s+|#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*|->|==|!=|<=|>=|:=|>>|<<|[-+*/%=<>|&^~]+|[@[\](){},.:`]|./gy;

    while (offset < source.length) {
      pattern.lastIndex = offset;
      const match = pattern.exec(source);
      if (!match) {
        output += escapeHtml(source[offset]);
        offset += 1;
        continue;
      }

      const value = match[0];
      offset = pattern.lastIndex;
      if (/^\s+$/.test(value)) {
        output += value;
      } else if (value.startsWith("#")) {
        output += token(value, "c1");
      } else if (/^["']/.test(value)) {
        output += token(value, "s");
      } else if (/^\d/.test(value)) {
        output += token(value, value.includes(".") ? "mf" : "mi");
      } else if (/^[A-Za-z_]/.test(value)) {
        if (value === "True" || value === "False" || value === "None") {
          output += token(value, "kc");
        } else if (python && PYTHON_KEYWORDS.has(value)) {
          output += token(value, "k");
        } else if ((python && PYTHON_BUILTINS.has(value)) || (!python && KEDI_TYPES.has(value))) {
          output += token(value, "nb");
        } else {
          output += token(value, "n");
        }
      } else if (/^(?:->|==|!=|<=|>=|:=|>>|<<|[-+*/%=<>|&^~]+)$/.test(value)) {
        output += token(value, "o");
      } else {
        output += token(value, "p");
      }
    }
    return output;
  }

  function highlightBackticks(source) {
    let output = "";
    let offset = 0;
    const expression = /`([^`\n]*)`/g;
    for (const match of source.matchAll(expression)) {
      const index = match.index;
      output += highlightInline(source.slice(offset, index), false);
      output += token("`", "bt");
      output += highlightInline(match[1], true);
      output += token("`", "bt");
      offset = index + match[0].length;
    }
    return output + highlightInline(source.slice(offset), false);
  }

  function highlightKedi(source) {
    let inBlockComment = false;
    let inPython = false;

    return source.split("\n").map((line) => {
      if (/^\s*###\s*$/.test(line)) {
        inBlockComment = !inBlockComment;
        return token(line, "cm");
      }
      if (inBlockComment) {
        return token(line, "cm");
      }
      if (/^\s*```\s*$/.test(line)) {
        inPython = !inPython;
        return token(line, "bt");
      }
      if (inPython) {
        return highlightInline(line, true);
      }

      const directive = line.match(/^(\s*)(>)(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*)(:)(.*)$/);
      if (directive && KEDI_DIRECTIVES.has(directive[4])) {
        return directive[1] + token(directive[2], "p") + directive[3]
          + token(directive[4], "k") + directive[5] + token(directive[6], "p")
          + highlightBackticks(directive[7]);
      }

      const procedure = line.match(/^(\s*)(@)(?:(test|eval):)?([A-Za-z_][A-Za-z0-9_]*)(.*)$/);
      if (procedure) {
        const qualifier = procedure[3]
          ? token(procedure[3], "k") + token(":", "p")
          : "";
        return procedure[1] + token(procedure[2], "p") + qualifier
          + token(procedure[4], "nf") + highlightBackticks(procedure[5]);
      }

      const customType = line.match(/^(\s*)(~)([A-Za-z_][A-Za-z0-9_]*)(.*)$/);
      if (customType) {
        return customType[1] + token(customType[2], "p")
          + token(customType[3], "nc") + highlightBackticks(customType[4]);
      }

      const template = line.match(/^(\s*)(>>|<<)(.*)$/);
      if (template) {
        return template[1] + token(template[2], "k") + highlightBackticks(template[3]);
      }

      return highlightBackticks(line);
    }).join("\n");
  }

  function applyKediHighlighting() {
    document.querySelectorAll("pre.kedi > code:not([data-kedi-highlighted])").forEach((code) => {
      const source = code.textContent;
      code.innerHTML = highlightKedi(source);
      code.dataset.kediHighlighted = "true";
    });
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(applyKediHighlighting);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyKediHighlighting);
  } else {
    applyKediHighlighting();
  }
})();
