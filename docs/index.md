# Welcome to Kedi

<div class="hero-section" markdown>

**:material-cat: A typed reasoning layer for LLM orchestration.**

Kedi is a powerful DSL that transforms how you build LLM-powered applications. Write multi-step AI workflows with **strong typing**, **Python interop**, and **clear dataflow** — all in a clean, indentation-scoped syntax that compiles to production-ready code.

[Get Started :material-arrow-right:](getting-started/installation.md){ .md-button .md-button--primary }
[View Examples](examples/trip-planner.md){ .md-button }

</div>

---

## :material-star-shooting: The Power of Kedi

```python title="research_assistant.kedi" linenums="1"
# Prelude: Import Python libraries available throughout
```
from datetime import datetime
from collections import Counter
```

# Define structured types for type-safe LLM outputs
~Source(title, url, credibility_score: float, summary)
~ResearchFinding(claim, evidence: list[str], confidence: float, sources: list[Source])
~ResearchReport(topic, findings: list[ResearchFinding], methodology, \
    conclusion, generated_at: str)

# Procedure to analyze a single source with typed output
@analyze_source(url, topic) -> Source:
    Analyze the source at <url> for information about "<topic>". \
    Provide [title], [summary], and [credibility_score: float] (0.0-1.0).
    = `Source(title=title, url=url, credibility_score=credibility_score, summary=summary)`

# Procedure to synthesize findings from multiple sources
@synthesize_findings(sources: list[Source], topic) -> list[ResearchFinding]:
    Given these sources about "<topic>": \
    <`'\n'.join([f"- {s.title}: {s.summary}" for s in sources])`> \
    Extract key [findings: list[ResearchFinding]] with evidence and confidence scores.
    = `findings`

# AI-generated procedure with specification
@generate_methodology(topic, source_count: int) -> str:
    > Generate a methodology section describing how <source_count> sources \
    were analyzed to research the topic. Include search strategy, \
    evaluation criteria, and synthesis approach.

# Main research pipeline
@research(topic, urls: list[str]) -> ResearchReport:
    # Analyze all sources in parallel (Python list comprehension)
    [sources: list[Source]] = `[analyze_source(url, topic) for url in urls]`
    
    # Filter credible sources
    [credible: list[Source]] = `[s for s in sources if s.credibility_score > 0.6]`
    
    # Synthesize findings from credible sources
    [findings: list[ResearchFinding]] = `synthesize_findings(credible, topic)`
    
    # Generate methodology and conclusion
    [methodology] = `generate_methodology(topic, len(credible))`
    
    Based on these findings about "<topic>": \
    <`'\n'.join([f.claim for f in findings])`> \
    Write a comprehensive [conclusion] summarizing the research.
    
    = `ResearchReport(
        topic=topic,
        findings=findings,
        methodology=methodology,
        conclusion=conclusion,
        generated_at=datetime.now().isoformat()
    )`

# Execute the research
[urls: list[str]] = `[
    "https://example.com/ai-safety",
    "https://example.com/ml-research",
    "https://example.com/tech-trends"
]`
[report: ResearchReport] = `research("AI Safety in 2025", urls)`

= <`report.conclusion`>
```

!!! success "What This Demonstrates"
    - **Custom Types** (`~Source`, `~ResearchFinding`, `~ResearchReport`) for structured LLM outputs
    - **Typed Procedures** with parameters and return types
    - **Python Interop** with list comprehensions and datetime
    - **AI-Generated Procedures** using `>` specification syntax
    - **Line Continuation** with `\` for readable multi-line prompts
    - **Multi-step Pipelines** chaining LLM calls with data transformations

---

## :material-lightning-bolt: Key Features

<div class="grid cards" markdown>

-   :material-check-decagram:{ .lg .middle } **Typed Procedures**

    ---

    Define inputs and outputs with full type annotations. Get compile-time validation and structured data from LLMs automatically.

    ```python
    @greet(name: str) -> str:
        Hello [greeting] for <name>!
        = `greeting`
    ```

-   :material-language-python:{ .lg .middle } **Python Interop**

    ---

    Seamlessly mix Python logic with LLM prompts. Use inline expressions, multiline blocks, and import any library.

    ```python
    [result: float] = `math.sqrt(16)`
    ```

-   :material-code-json:{ .lg .middle } **Structured Output**

    ---

    Define custom types with `~` syntax. Get validated Pydantic objects back from LLMs automatically.

    ```python
    ~Person(name, age: int, email)
    [user: Person] = ...
    ```

-   :material-robot:{ .lg .middle } **Multiple Adapters**

    ---

    Use PydanticAI, DSPy, or create custom adapters. Run against OpenAI, Anthropic, Groq, or local models.

    ```bash
    kedi --adapter pydantic
    kedi --adapter dspy
    ```

</div>

---

## :material-table: Core Syntax at a Glance

| Syntax | Purpose | Example |
|--------|---------|---------|
| `@name()` | Define a procedure | `@greet(name: str) -> str:` |
| `~Type()` | Define a custom type | `~Person(name, age: int)` |
| `<var>` | Substitute a variable | `Hello, <name>!` |
| `[out]` | Capture LLM output | `The capital is [capital].` |
| `[out: type]` | Typed LLM output | `[cities: list[str]]` |
| `\` | Continue to next line | `Long prompt \` |
| `` `expr` `` | Inline Python | `` <`2 + 2`> `` |
| ` ``` ` | Python code block | Multiline Python execution |
| `>` | AI-generated procedure | `> Specification for AI...` |

---

## :material-speedometer: Quick Start

=== "Install"

    ```bash
    pip install kedi
    ```

=== "Create"

    ```python title="hello.kedi"
    @greet(name) -> str:
        Hello! A warm [greeting] for <name>.
        = `greeting`
    
    = <greet(World)>
    ```

=== "Run"

    ```bash
    kedi hello.kedi --adapter pydantic
    ```

---

## :material-book-open-page-variant: Explore the Documentation

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **[Installation](getting-started/installation.md)**

    Get Kedi installed in under a minute with pip.

-   :material-code-braces:{ .lg .middle } **[Your First Program](getting-started/hello-world.md)**

    Write and run your first Kedi program step by step.

-   :material-function:{ .lg .middle } **[Procedures](concepts/procedures.md)**

    Learn about typed procedures and return values.

-   :material-shape:{ .lg .middle } **[Variables & Types](concepts/variables-and-types.md)**

    Understand Kedi's type system and custom types.

-   :material-console:{ .lg .middle } **[CLI Reference](reference/cli.md)**

    Master the command-line interface options.

-   :material-puzzle:{ .lg .middle } **[Agent Adapters](adapters/index.md)**

    Use PydanticAI, DSPy, or build custom adapters.

</div>
