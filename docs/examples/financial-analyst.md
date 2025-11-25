# Financial Analyst

This example demonstrates a powerful pattern: **LLM-Python Hybrid Analysis**.

We use the LLM to extract structured data from unstructured text, use Python to perform accurate calculations (which LLMs are often bad at), and then feed the results back to the LLM for a final summary.

## The Scenario

We have a raw text report about a company's quarterly performance. We want to:

1.  Extract revenue and expense figures.
2.  Calculate profit and margin (using Python).
3.  Generate a professional executive summary.

## The Code

```python
~FinancialData(revenue: float, expenses: float, currency: str)

@extract_data(report_text: str) -> FinancialData:
    Analyze the following financial report text: """<report_text>""" \
    and extract the total revenue, total expenses, and currency into [data: FinancialData].
    = <data>
```

```python
@generate_summary(data: FinancialData, profit: float, margin: float) -> str:
    You are a senior financial analyst. \
    The company had a revenue of <data.revenue> <data.currency> and expenses of <data.expenses> <data.currency>. \
    The calculated profit is <profit> <data.currency> with a margin of <margin>%. \
    Write a concise executive [summary].
    = <summary>
```

````python
@analyze_report(raw_text: str) -> str:
    # Step 1: Extract Data (LLM)
    [financials: FinancialData] = <extract_data(raw_text)>

    # Step 2: Calculate Metrics (Python)
    # LLMs are bad at math, so we do it in Python!
    [metrics: dict] = ```
    profit = financials.revenue - financials.expenses
    margin = (profit / financials.revenue) * 100 if financials.revenue > 0 else 0
    return {"profit": profit, "margin": margin}
    ```

    # Step 3: Generate Summary (LLM)
    = <generate_summary(financials, `metrics["profit"]`, `metrics["margin"]`)>
````

## Running the Analysis

```python
[report] = """
Q3 Performance Report:
Despite market headwinds, we achieved a total turnover of 1,500,000 USD.
Operational costs were higher than expected at 1,200,000 USD due to supply chain issues.
"""

[executive_summary] = <analyze_report(report)>
= <executive_summary>
```

## Key Takeaways

- **Separation of Concerns**: Use LLMs for understanding (extraction) and generation (summarizing), but use Python for logic and math.
- **Robustness**: By extracting to a typed object (`FinancialData`), we ensure the Python block receives valid numbers, preventing runtime errors.
- **Single-Line Prompts**: Notice how we used `\` in `@extract_data` and `@generate_summary` to keep the prompt and output capture in a single logical line, ensuring a single, coherent LLM call.
