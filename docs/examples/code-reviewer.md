# Code Reviewer Example

This example demonstrates building an automated code review system with Kedi that analyzes code for issues, suggests improvements, and generates detailed reports.

---

## Overview

We'll build a code reviewer that:

1. Parses code and identifies the programming language
2. Analyzes for bugs, security issues, and code smells
3. Suggests specific improvements with diffs
4. Generates a structured review report

---

## The Complete Code Reviewer

```python title="code_reviewer.kedi" linenums="1"
# Prelude: Import code analysis utilities
```
import re
from enum import Enum
from dataclasses import dataclass
```

# Define severity levels and issue types
~Issue(
    severity,           # "critical", "warning", "info"
    category,           # "bug", "security", "performance", "style"
    line_number: int,
    description,
    suggestion
)

~CodeSuggestion(
    original_code,
    improved_code,
    explanation,
    impact            # "high", "medium", "low"
)

~ReviewReport(
    file_name,
    language,
    summary,
    issues: list[Issue],
    suggestions: list[CodeSuggestion],
    overall_score: float,
    approved: bool
)

# Detect programming language from code
@detect_language(code) -> str:
    Analyze this code snippet and identify the programming language: \
    ```<code>``` \
    The programming language is [language] (e.g., Python, JavaScript, TypeScript, Go, Rust, Java).
    = `language.strip()`

# Analyze code for issues
@find_issues(code, language) -> list[Issue]:
    Review this <language> code for bugs, security vulnerabilities, \
    performance issues, and code style problems: ```<code>``` \
    Identify all [issues: list[Issue]] with specific line numbers and actionable suggestions.
    = `issues`

# Generate code improvement suggestions
@suggest_improvements(code, language, issues: list[Issue]) -> list[CodeSuggestion]:
    Based on these issues in the <language> code: \
    <`'\n'.join([f"- Line {i.line_number}: {i.description}" for i in issues])`> \
    Original code: ```<code>``` \
    Generate [suggestions: list[CodeSuggestion]] with before/after code examples.
    = `suggestions`

# Calculate overall code quality score
@calculate_score(issues: list[Issue]) -> float:
    [score: float] = ```
    if not issues:
        return 1.0
    
    # Weight by severity
    weights = {"critical": 0.3, "warning": 0.1, "info": 0.02}
    penalty = sum(weights.get(i.severity, 0.05) for i in issues)
    
    # Cap between 0 and 1
    return max(0.0, min(1.0, 1.0 - penalty))
    ```
    = `score`

# Generate summary based on findings
@generate_summary(language, issues: list[Issue], score: float) -> str:
    Given a <language> code review with <`len(issues)`> issues found, \
    <`len([i for i in issues if i.severity == 'critical'])`> critical, \
    <`len([i for i in issues if i.severity == 'warning'])`> warnings, \
    overall score <`f'{score:.0%}'`>, write a concise [summary] (2-3 sentences).
    = `summary`

# AI-generated procedure for security-specific analysis
@analyze_security(code, language) -> list[Issue]:
    > Perform a deep security analysis of the code, looking for \
    SQL injection, XSS, hardcoded secrets, insecure cryptography, \
    path traversal, and unsafe deserialization vulnerabilities. \
    Return Issue objects with severity="critical" for security issues.

# Main review procedure
@review_code(code, file_name) -> ReviewReport:
    # Detect language
    [language] = `detect_language(code)`
    
    # Find general issues
    [general_issues: list[Issue]] = `find_issues(code, language)`
    
    # Perform security analysis
    [security_issues: list[Issue]] = `analyze_security(code, language)`
    
    # Combine all issues
    [all_issues: list[Issue]] = `general_issues + security_issues`
    
    # Remove duplicates by line number and description
    [unique_issues: list[Issue]] = ```
    seen = set()
    unique = []
    for issue in all_issues:
        key = (issue.line_number, issue.description[:50])
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return sorted(unique, key=lambda x: (
        {"critical": 0, "warning": 1, "info": 2}.get(x.severity, 3),
        x.line_number
    ))
    ```
    
    # Generate suggestions
    [suggestions: list[CodeSuggestion]] = `suggest_improvements(code, language, unique_issues)`
    
    # Calculate score
    [score: float] = `calculate_score(unique_issues)`
    
    # Generate summary
    [summary] = `generate_summary(language, unique_issues, score)`
    
    # Determine approval
    [approved: bool] = ```
    critical_count = len([i for i in unique_issues if i.severity == "critical"])
    return critical_count == 0 and score >= 0.7
    ```
    
    = `ReviewReport(
        file_name=file_name,
        language=language,
        summary=summary,
        issues=unique_issues,
        suggestions=suggestions,
        overall_score=score,
        approved=approved
    )`

# Format the review as markdown
@format_review_markdown(report: ReviewReport) -> str:
    [markdown] = ```
    lines = [
        f"# Code Review: {report.file_name}",
        "",
        f"**Language:** {report.language}",
        f"**Score:** {report.overall_score:.0%}",
        f"**Status:** {'✅ Approved' if report.approved else '❌ Changes Requested'}",
        "",
        "## Summary",
        report.summary,
        "",
        "## Issues",
        ""
    ]
    
    for issue in report.issues:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity, "⚪")
        lines.append(f"### {icon} Line {issue.line_number}: {issue.category.title()}")
        lines.append(f"**Severity:** {issue.severity}")
        lines.append(f"**Description:** {issue.description}")
        lines.append(f"**Suggestion:** {issue.suggestion}")
        lines.append("")
    
    if report.suggestions:
        lines.append("## Suggested Improvements")
        lines.append("")
        for i, sug in enumerate(report.suggestions, 1):
            lines.append(f"### Improvement {i} ({sug.impact} impact)")
            lines.append(sug.explanation)
            lines.append("")
            lines.append("**Before:**")
            lines.append(f"```{report.language.lower()}")
            lines.append(sug.original_code)
            lines.append("```")
            lines.append("")
            lines.append("**After:**")
            lines.append(f"```{report.language.lower()}")
            lines.append(sug.improved_code)
            lines.append("```")
            lines.append("")
    
    return "\n".join(lines)
    ```
    = `markdown`

# Example: Review a Python function
[sample_code] = ```
return '''
def process_user_data(user_id, data):
    # Get user from database
    query = "SELECT * FROM users WHERE id = " + user_id
    user = db.execute(query)
    
    password = "admin123"  # Default password
    
    if data:
        eval(data)  # Process dynamic code
    
    return user
'''
```

[report: ReviewReport] = `review_code(sample_code, "user_processor.py")`
[markdown_output] = `format_review_markdown(report)`

= <markdown_output>
```

---

## Key Components Explained

### Issue Detection

The `find_issues` procedure analyzes code holistically:

```python
@find_issues(code, language) -> list[Issue]:
    Review this <language> code for bugs, security vulnerabilities, \
    performance issues, and code style problems:
    ...
    Identify all [issues: list[Issue]] with specific line numbers...
```

### Security Analysis

The AI-generated `analyze_security` procedure performs deep security analysis:

```python
@analyze_security(code, language) -> list[Issue]:
    > Perform a deep security analysis of the code, looking for:
    - SQL injection vulnerabilities
    - XSS vulnerabilities
    - Hardcoded secrets or API keys
    ...
```

!!! info "AI-Generated Procedures"
    The `>` syntax tells Kedi to generate the implementation automatically based on the specification.

### Score Calculation

Python handles the scoring logic:

```python
@calculate_score(issues: list[Issue]) -> float:
    [score: float] = ```
    weights = {"critical": 0.3, "warning": 0.1, "info": 0.02}
    penalty = sum(weights.get(i.severity, 0.05) for i in issues)
    return max(0.0, min(1.0, 1.0 - penalty))
    ```
    = `score`
```

---

## Running the Code Reviewer

### Basic Usage

```bash
# Run the example
kedi code_reviewer.kedi

# With a specific model for better analysis
kedi code_reviewer.kedi --adapter-model openai:gpt-4o
```

### Review Your Own Code

Modify the `sample_code` variable to review your code:

```python
[sample_code] = ```
# Read from file
with open("my_file.py", "r") as f:
    return f.read()
```

[report: ReviewReport] = `review_code(sample_code, "my_file.py")`
```

---

## Sample Output

Running the example produces a review like:

```markdown
# Code Review: user_processor.py

**Language:** Python
**Score:** 10%
**Status:** ❌ Changes Requested

## Summary
This code contains critical security vulnerabilities including SQL injection, 
hardcoded credentials, and arbitrary code execution via eval(). Immediate 
remediation is required before this code can be approved.

## Issues

### 🔴 Line 3: Security
**Severity:** critical
**Description:** SQL injection vulnerability - user_id is concatenated directly into query
**Suggestion:** Use parameterized queries: `db.execute("SELECT * FROM users WHERE id = ?", (user_id,))`

### 🔴 Line 6: Security  
**Severity:** critical
**Description:** Hardcoded password in source code
**Suggestion:** Use environment variables or a secrets manager

### 🔴 Line 9: Security
**Severity:** critical
**Description:** Arbitrary code execution via eval()
**Suggestion:** Use safe alternatives like ast.literal_eval() or JSON parsing
```

---

## Adding Tests

```python title="code_reviewer.kedi (continued)"
@test: detect_language:
    > case: python:
        `assert detect_language("def foo(): pass") == "Python"`
    
    > case: javascript:
        `assert detect_language("const foo = () => {}") == "JavaScript"`

@test: find_issues:
    > case: finds_sql_injection:
        ```
        code = 'query = "SELECT * FROM users WHERE id = " + user_id'
        issues = find_issues(code, "Python")
        assert any("SQL" in i.description or "injection" in i.description.lower() 
                   for i in issues)
        ```
    
    > case: finds_eval:
        ```
        code = 'eval(user_input)'
        issues = find_issues(code, "Python")
        assert any("eval" in i.description.lower() for i in issues)
        ```

@test: calculate_score:
    > case: perfect_score:
        `assert calculate_score([]) == 1.0`
    
    > case: critical_penalty:
        ```
        issues = [Issue(severity="critical", category="security", 
                       line_number=1, description="test", suggestion="fix")]
        score = calculate_score(issues)
        assert score < 0.8
        ```
```

---

## Extending the Reviewer

### Add Language-Specific Rules

```python
@check_python_style(code) -> list[Issue]:
    Check this Python code against PEP 8 style guidelines:
    ```
    <code>
    ```
    
    Identify [style_issues: list[Issue]] for style violations.
    = `style_issues`
```

### Add Complexity Analysis

```python
~ComplexityMetrics(
    cyclomatic: int,
    cognitive: int,
    lines_of_code: int,
    comment_ratio: float
)

@analyze_complexity(code) -> ComplexityMetrics:
    Analyze the complexity of this code:
    ```
    <code>
    ```
    
    Provide [cyclomatic: int] complexity, [cognitive: int] complexity, \
    [lines_of_code: int], and [comment_ratio: float] (0.0-1.0).
    
    = `ComplexityMetrics(
        cyclomatic=cyclomatic,
        cognitive=cognitive,
        lines_of_code=lines_of_code,
        comment_ratio=comment_ratio
    )`
```

---

## Best Practices

!!! success "Review Quality"
    - **Multiple Passes** — Separate security, style, and logic analysis
    - **Specific Suggestions** — Include before/after code examples
    - **Line Numbers** — Always reference specific locations

!!! success "Accuracy"
    - **Use GPT-4** — Better models provide more accurate reviews
    - **Language Context** — Always specify the programming language
    - **Test the Reviewer** — Validate with known vulnerable code

---

## See Also

- [Data Pipeline Example](data-pipeline.md) — Another complex workflow
- [Code Generation](../concepts/codegen.md) — AI-generated procedures
- [Python Interop](../concepts/python-interop.md) — Working with Python
