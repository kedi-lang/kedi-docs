# Data Pipeline Example

This example demonstrates building a data processing pipeline with Kedi that extracts, transforms, and analyzes data using LLMs.

---

## Overview

We'll build a pipeline that:

1. Extracts structured data from unstructured text
2. Validates and enriches the data
3. Generates insights and summaries

---

## The Complete Pipeline

```python title="data_pipeline.kedi" linenums="1"
# Prelude: Import data processing libraries
```
import json
from datetime import datetime
from collections import Counter
```

# Define data models
~Customer(
    name,
    email,
    company,
    industry,
    sentiment: float,
    key_concerns: list[str]
)

~Insight(
    category,
    finding,
    confidence: float,
    affected_customers: int
)

~PipelineReport(
    processed_count: int,
    timestamp: str,
    customers: list[Customer],
    insights: list[Insight],
    summary
)

# Stage 1: Extract structured data from raw text
@extract_customer(raw_text) -> Customer:
    Extract customer information from this support ticket: "<raw_text>" \
    Customer name: [name], Email: [email], Company: [company], \
    Industry: [industry], Sentiment score (0.0-1.0): [sentiment: float], \
    Key concerns: [key_concerns: list[str]]
    
    = `Customer(
        name=name,
        email=email,
        company=company,
        industry=industry,
        sentiment=sentiment,
        key_concerns=key_concerns
    )`

# Stage 2: Validate and enrich customer data
@enrich_customer(customer: Customer) -> Customer:
    # Validate email format
    [valid_email: bool] = ```
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, customer.email))
    ```
    
    # Normalize industry if needed
    Given this industry name: "<`customer.industry`>" \
    Provide the standardized [industry_normalized] from: Technology, Healthcare, Finance, Retail, Manufacturing, Other.
    
    = `Customer(
        name=customer.name,
        email=customer.email if valid_email else "invalid@unknown.com",
        company=customer.company,
        industry=industry_normalized,
        sentiment=customer.sentiment,
        key_concerns=customer.key_concerns
    )`

# Stage 3: Analyze patterns across customers
@analyze_patterns(customers: list[Customer]) -> list[Insight]:
    # Calculate statistics in Python
    [stats] = ```
    sentiments = [c.sentiment for c in customers]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
    all_concerns = []
    for c in customers:
        all_concerns.extend(c.key_concerns)
    concern_counts = Counter(all_concerns).most_common(5)
    
    industries = Counter(c.industry for c in customers)
    
    return {
        "avg_sentiment": avg_sentiment,
        "top_concerns": concern_counts,
        "industries": dict(industries),
        "total": len(customers)
    }
    ```
    
    Based on this customer analysis data: \
    Average sentiment: <`stats['avg_sentiment']:.2f`>, \
    Top concerns: <`stats['top_concerns']`>, \
    Industry breakdown: <`stats['industries']`>, \
    Total customers: <`stats['total']`>. \
    Generate [insights: list[Insight]] with actionable findings.
    
    = `insights`

# Stage 4: Generate executive summary
@generate_summary(customers: list[Customer], insights: list[Insight]) -> str:
    # Prepare data for summary
    [high_risk: list[str]] = `[c.name for c in customers if c.sentiment < 0.3]`
    [top_insight] = `insights[0].finding if insights else "No insights available"`
    
    Create an executive [summary] for stakeholders about \
    <`len(customers)`> customer interactions analyzed, \
    <`len(high_risk)`> high-risk customers identified, \
    and key finding: <top_insight>.
    
    = `summary`

# Main pipeline orchestration
@run_pipeline(raw_tickets: list[str]) -> PipelineReport:
    # Stage 1: Extract
    [customers: list[Customer]] = ```
    extracted = []
    for ticket in raw_tickets:
        try:
            customer = extract_customer(ticket)
            extracted.append(customer)
        except Exception as e:
            print(f"Failed to extract: {e}")
    return extracted
    ```
    
    # Stage 2: Enrich
    [enriched: list[Customer]] = `[enrich_customer(c) for c in customers]`
    
    # Stage 3: Analyze
    [insights: list[Insight]] = `analyze_patterns(enriched)`
    
    # Stage 4: Summarize
    [summary] = `generate_summary(enriched, insights)`
    
    = `PipelineReport(
        processed_count=len(enriched),
        timestamp=datetime.now().isoformat(),
        customers=enriched,
        insights=insights,
        summary=summary
    )`

# Example usage with sample data
[tickets: list[str]] = `[
    "Hi, I'm John Smith from Acme Corp (john@acme.com). We're having major issues with the API response times. This is affecting our production systems. Very frustrated!",
    "Sarah Johnson here, TechStart Inc (sarah@techstart.io). Love the new dashboard features! Just wondering about enterprise pricing options.",
    "URGENT: Mike Brown, HealthFirst (mike@healthfirst.org). Compliance audit next week and we can't export our data. Need immediate assistance!"
]`

[report: PipelineReport] = `run_pipeline(tickets)`

= <`report.summary`>
```

---

## Pipeline Stages Explained

### Stage 1: Extraction

The `extract_customer` procedure uses the LLM to parse unstructured text:

```python
@extract_customer(raw_text) -> Customer:
    Extract customer information from this support ticket: \
    "<raw_text>"
    
    Customer name: [name]
    Email: [email]
    ...
```

!!! tip "Multi-Field Extraction"
    Each `[field]` on the same line or continued line is extracted in a single LLM call.

### Stage 2: Enrichment

The `enrich_customer` procedure validates and normalizes data:

```python
@enrich_customer(customer: Customer) -> Customer:
    # Python validation
    [valid_email: bool] = ```
    import re
    pattern = r'^...'
    return bool(re.match(pattern, customer.email))
    ```
    
    # LLM normalization
    Given this industry name: "<`customer.industry`>"
    Provide the standardized [industry_normalized] from: ...
```

### Stage 3: Analysis

The `analyze_patterns` procedure combines Python statistics with LLM insights:

```python
@analyze_patterns(customers: list[Customer]) -> list[Insight]:
    # Python aggregation
    [stats] = ```
    sentiments = [c.sentiment for c in customers]
    ...
    ```
    
    # LLM insight generation
    Based on this customer analysis data: ...
    Generate [insights: list[Insight]] with actionable findings.
```

### Stage 4: Summary

The `generate_summary` procedure creates a human-readable report:

```python
@generate_summary(customers: list[Customer], insights: list[Insight]) -> str:
    Create an executive [summary] for stakeholders about: ...
```

---

## Running the Pipeline

```bash
# Run with default settings
kedi data_pipeline.kedi

# Run with specific model for better extraction
kedi data_pipeline.kedi --adapter-model openai:gpt-4o

# Run with tests
kedi data_pipeline.kedi --test
```

---

## Adding Tests

```python title="data_pipeline.kedi (continued)"
@test: extract_customer:
    > case: basic_extraction:
        ```
        ticket = "John Doe, john@example.com, works at TestCo in Technology sector."
        customer = extract_customer(ticket)
        assert customer.name == "John Doe"
        assert "example.com" in customer.email
        ```
    
    > case: sentiment_range:
        ```
        ticket = "Very angry customer from BigCorp!"
        customer = extract_customer(ticket)
        assert 0.0 <= customer.sentiment <= 1.0
        ```

@test: analyze_patterns:
    > case: generates_insights:
        ```
        customers = [
            Customer(name="A", email="a@a.com", company="A", 
                    industry="Tech", sentiment=0.8, key_concerns=["speed"]),
            Customer(name="B", email="b@b.com", company="B",
                    industry="Tech", sentiment=0.2, key_concerns=["bugs"])
        ]
        insights = analyze_patterns(customers)
        assert len(insights) > 0
        assert all(0.0 <= i.confidence <= 1.0 for i in insights)
        ```
```

---

## Evaluation Metrics

```python title="data_pipeline.kedi (continued)"
@eval: run_pipeline:
    > metric: extraction_accuracy:
        = ```
        # Test with known data
        test_tickets = [
            "John Smith, john@test.com, TestCorp, Technology"
        ]
        report = run_pipeline(test_tickets)
        
        # Check extraction quality
        if report.customers and report.customers[0].name == "John Smith":
            return (1.0, "Perfect extraction")
        return (0.5, "Partial extraction")
        ```
    
    > metric: processing_speed:
        = ```
        import time
        start = time.time()
        report = run_pipeline(["Test ticket from user@test.com at TestCo"])
        elapsed = time.time() - start
        
        # Score based on speed (under 5s is perfect)
        score = max(0, 1 - (elapsed / 10))
        return (score, f"Processed in {elapsed:.2f}s")
        ```
```

---

## Best Practices

!!! success "Pipeline Design"
    - **Separate Concerns** — Each stage has a single responsibility
    - **Type Safety** — Custom types ensure data consistency
    - **Error Handling** — Use try/except in Python blocks
    - **Validation** — Validate data between stages

!!! success "Performance"
    - **Batch Processing** — Process multiple items with list comprehensions
    - **Parallel Extraction** — Each `[field]` on the same line is extracted together
    - **Caching** — Use `--no-cache` only when needed

---

## See Also

- [Code Reviewer Example](code-reviewer.md) — Another complex workflow
- [Procedures](../concepts/procedures.md) — Procedure fundamentals
- [Python Interop](../concepts/python-interop.md) — Working with Python
