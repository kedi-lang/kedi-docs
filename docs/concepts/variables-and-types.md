# Variables and Types

Kedi is a strongly typed language that bridges Python's type system with LLM outputs. This ensures data flows correctly between your logic and AI-generated content.

---

## Variables

Variables are defined using square brackets `[name]` or `[name: type]`.

### Basic Assignment

```python
# Simple assignment (type inferred as str)
[greeting] = Hello, World!

# Typed assignment
[count: int] = `42`
[name: str] = `"Kedi"`
[is_active: bool] = `True`
[score: float] = `3.14`
```

### Assignment from LLM Output

When a variable appears in a template line, the LLM fills it:

```python
# LLM determines the capital (single LLM call)
The capital of France is [capital].

# Now 'capital' contains "Paris" and can be used
<capital> is known for the Eiffel Tower.
```

### Assignment from Python

Use backticks for Python expressions:

```python
# Direct Python value
[items: list[str]] = `["apple", "banana", "cherry"]`

# Python expression
[total: int] = `sum([1, 2, 3, 4, 5])`

# Multiline Python block
[result: float] = ```
import math
radius = 5
return math.pi * radius ** 2
```
```

---

## Standard Types

Kedi supports all Python built-in types:

| Type | Description | Example |
|------|-------------|---------|
| `str` | Text string | `[name: str]` |
| `int` | Integer number | `[count: int]` |
| `float` | Floating-point number | `[score: float]` |
| `bool` | Boolean value | `[active: bool]` |
| `list[T]` | List of type T | `[items: list[str]]` |
| `dict[K, V]` | Dictionary | `[data: dict[str, int]]` |
| `set[T]` | Set of type T | `[unique: set[str]]` |
| `tuple[...]` | Tuple | `[pair: tuple[str, int]]` |

### Collection Types

```python
# List of strings (single LLM call)
List all major cities in Japan: [cities: list[str]].

# List of integers from Python
[numbers: list[int]] = `[1, 2, 3, 4, 5]`

# Nested collections
[matrix: list[list[int]]] = `[[1, 2], [3, 4], [5, 6]]`

# Dictionary
[scores: dict[str, int]] = `{"Alice": 95, "Bob": 87}`
```

### Optional Types

Use union types for optional values:

```python
# May be None (single LLM call with optional output)
The user's nickname is [nickname: str | None], if any.

# Multiple possible types
[value: int | str] = `42`
```

---

## Custom Types

Define structured data types using the `~` syntax. These compile to Pydantic models.

### Basic Custom Types

```python
# Simple type with fields
~Person(name, age: int, email)

# Fields default to str if not specified
~City(name, country, population: int)

# Nested types
~Address(street, city, postal_code, country)
~Company(name, address: Address, employees: int)
```

### Type Field Annotations

```python
# All field types
~Product(
    name,                    # str (default)
    price: float,            # float
    quantity: int,           # int
    tags: list[str],         # list of strings
    in_stock: bool,          # boolean
    metadata: dict[str, str] # dictionary
)
```

### Using Custom Types

```python
~Movie(title, year: int, director, rating: float)

@recommend_movie(genre) -> Movie:
    Recommend a classic <genre> movie with [title], [year: int], [director], and [rating: float].
    = `Movie(title=title, year=year, director=director, rating=rating)`

# Use in output
[movie: Movie] = `recommend_movie("sci-fi")`

# Access fields
The movie <`movie.title`> was directed by <`movie.director`>.
```

### Custom Types with LLMs

When you use a custom type annotation, Kedi instructs the LLM to generate matching structured data:

```python
~Recipe(
    name,
    ingredients: list[str],
    prep_time: int,
    instructions: list[str]
)

@get_recipe(dish) -> Recipe:
    Provide a recipe for <dish> with [name], [ingredients: list[str]], \
    [prep_time: int] minutes prep time, and [instructions: list[str]].
    = `Recipe(name=name, ingredients=ingredients, prep_time=prep_time, instructions=instructions)`
```

---

## Inline Python Type Annotations

You can use backtick-wrapped Python expressions for type annotations:

### Basic Inline Types

```python
# Equivalent to regular annotations
[x: `int`] = `42`
[y: `str`] = `"hello"`
[z: `float`] = `3.14`
```

### Complex Inline Types

```python
# Complex generic types
[numbers: `list[int]`] = `[1, 2, 3, 4, 5]`
[words: `list[str]`] = `["apple", "banana", "cherry"]`
[mapping: `dict[str, list[int]]`] = `{"evens": [2, 4, 6], "odds": [1, 3, 5]}`
```

### Custom Types in Inline Annotations

```python
~Person(name, age: int)

# Reference custom type
[person: `Person`] = `Person(name="Alice", age=30)`

# List of custom types
[team: `list[Person]`] = ```
return [
    Person(name="Alice", age=30),
    Person(name="Bob", age=25)
]
```
```

### Mixed Annotations

Regular and inline annotations work interchangeably:

```python
# These are equivalent
[x: int] = `10`
[y: `int`] = `20`

# Can mix in same program
@calculate(a: int, b: `int`) -> `int`:
    = `a + b`
```

!!! info "When to Use Inline Annotations"
    Inline annotations (`` `type` ``) are evaluated at runtime with full access to prelude, globals, and local scope. Use them when:
    
    - Referencing dynamically defined types
    - Using complex type expressions
    - Need runtime type evaluation

---

## Type Validation

Kedi validates types at multiple stages using Pydantic's `TypeAdapter`:

- **Parse-Time**: Type annotation strings are validated to ensure they reference valid Python types
- **Runtime**: Values are validated against their declared types using Pydantic
- **LLM Output**: Responses from LLMs are coerced and validated to match expected types

---

## Type Coercion

Kedi performs automatic type coercion when possible:

| From | To | Example |
|------|-----|---------|
| `"42"` | `int` | LLM string → integer |
| `"3.14"` | `float` | LLM string → float |
| `"true"`, `"yes"`, `"1"` | `bool` | LLM string → True |
| `"false"`, `"no"`, `"0"` | `bool` | LLM string → False |
| JSON array string | `list` | LLM JSON → list |

---

## Advanced Types from `typing`

Kedi supports types from Python's `typing` and `typing_extensions` modules. This enables powerful type constraints for LLM outputs.

### Literal Types

Use `Literal` to constrain outputs to specific values. The LLM **must** return one of the specified options:

```python
# LLM can only output "Istanbul" or "Paris"
What is the best city to visit? [city: Literal['Istanbul', 'Paris']]

# Multiple options for classification
Classify this sentiment: [sentiment: Literal['positive', 'negative', 'neutral']]

# Rating constraints
Rate this from 1-5: [rating: Literal[1, 2, 3, 4, 5]]
```

### Union Types

```python
# In template string output fields
The user's [nickname: str | None] if they have one.

# In custom type fields
~User(
    name,
    nickname: str | None,
    age: int | None
)
```

### Optional Type

```python
# In custom type fields
~Product(
    name,
    description: Optional[str],
    tags: list[str]
)

# In template string output fields
Get user info: [name] and [nickname: Optional[str]].
```

### TypedDict

For dictionaries with specific keys, define a `TypedDict` class in the prelude:

```python
# Prelude - Python block for class definitions

from typing import TypedDict

class UserDict(TypedDict):
    name: str
    age: int
    email: str
```

# Now use UserDict as a type annotation 
[user: UserDict] = `{"name": "Alice", "age": 30, "email": "alice@example.com"}`
```

!!! info "Native Type Parsing"
    Type names like `Literal`, `Optional`, `list`, `dict` are parsed natively by Kedi in type annotations.

### Combining with Custom Types

```python
~City(name, country, population: int)

# Literal with custom type field
~Trip(
    destination: Literal['Istanbul', 'Paris', 'Tokyo'],
    duration: int,
    budget: float
)

@plan_trip(preference) -> Trip:
    Based on <preference>, plan a trip with \
    [destination: Literal['Istanbul', 'Paris', 'Tokyo']], \
    [duration: int] days, and [budget: float] USD budget.
    = `Trip(destination=destination, duration=duration, budget=budget)`
```

!!! tip "Literal for Controlled Outputs"
    `Literal` types are especially powerful for:
    
    - **Classification tasks**: `Literal['spam', 'not_spam']`
    - **Categorical choices**: `Literal['small', 'medium', 'large']`
    - **Enum-like values**: `Literal['draft', 'published', 'archived']`
    - **Constrained selections**: `Literal['TR', 'US', 'UK', 'DE']`

---

## Comprehensive Examples with `typing`

### Example 1: Content Moderation System

A complete content moderation pipeline using `Literal` types for classification:

```python
# Prelude: Import typing modules
```
from typing import Literal
```

# Custom types with Literal constraints
~ModerationResult(
    category: Literal['safe', 'spam', 'hate_speech', 'violence', 'adult'],
    confidence: float,
    action: Literal['approve', 'flag', 'reject'],
    reason
)

# Moderate content with constrained outputs
@moderate_content(text) -> ModerationResult:
    Analyze this content for moderation: """<text>""" \
    Classify into [category: Literal['safe', 'spam', 'hate_speech', 'violence', 'adult']], \
    provide [confidence: float] score (0.0-1.0), \
    recommend [action: Literal['approve', 'flag', 'reject']], \
    and explain [reason].
    = `ModerationResult(category=category, confidence=confidence, action=action, reason=reason)`

# Process content
[result: ModerationResult] = `moderate_content("Hello, this is a friendly message!")`

# result.category will be one of: 'safe', 'spam', 'hate_speech', 'violence', 'adult'
# result.action will be one of: 'approve', 'flag', 'reject'
= `f"Category: {result.category}, Action: {result.action}"`
```

### Example 2: Multi-Language Translator

Using `Literal` to constrain language selection:

```python
```
from typing import Literal

# Define supported languages
SupportedLanguage = Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh']
```

~Translation(
    source_lang: Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh'],
    target_lang: Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh'],
    original_text,
    translated_text,
    confidence: float
)

@detect_language(text) -> Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh']:
    Detect the language of: """<text>""" \
    Return [language: Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh']].
    = `language`

@translate(text, target: Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh']) -> Translation:
    [source: Literal['tr', 'en', 'de', 'fr', 'es', 'ja', 'zh']] = `detect_language(text)`
    
    Translate from <source> to <target>: """<text>""" \
    Provide [translated_text] and [confidence: float].
    
    = `Translation(
        source_lang=source,
        target_lang=target,
        original_text=text,
        translated_text=translated_text,
        confidence=confidence
    )`

[result: Translation] = `translate("Merhaba dünya!", "en")`
= `f"{result.original_text} -> {result.translated_text} (confidence: {result.confidence:.0%})"`
```

### Example 3: E-Commerce Product Categorization

Using `Literal` for hierarchical categories:

```python
```
from typing import Literal
```

# Main categories
~ProductCategory(
    main: Literal['Electronics', 'Clothing', 'Home', 'Sports', 'Books'],
    sub: Literal['Phones', 'Laptops', 'TV', 'Shirts', 'Pants', 'Furniture', 'Kitchen', 'Fitness', 'Outdoor', 'Fiction', 'Non-Fiction'],
    confidence: float
)

~Product(
    name,
    description,
    price: float,
    category: ProductCategory,
    tags: list[str],
    condition: Literal['new', 'like_new', 'good', 'fair', 'poor']
)

@categorize_product(name, description) -> Product:
    Categorize this product: \
    Name: <name> \
    Description: <description> \
    Assign [main: Literal['Electronics', 'Clothing', 'Home', 'Sports', 'Books']] category, \
    [sub: Literal['Phones', 'Laptops', 'TV', 'Shirts', 'Pants', 'Furniture', 'Kitchen', 'Fitness', 'Outdoor', 'Fiction', 'Non-Fiction']] category, \
    [confidence: float], \
    suggest [price: float] in USD, \
    generate [tags: list[str]], \
    assume [condition: Literal['new', 'like_new', 'good', 'fair', 'poor']] is new.
    
    = `Product(
        name=name,
        description=description,
        price=price,
        category=ProductCategory(main=main, sub=sub, confidence=confidence),
        tags=tags,
        condition=condition
    )`

[laptop: Product] = `categorize_product(
    "MacBook Pro 16",
    "Apple M3 Max chip, 36GB RAM, 1TB SSD, Space Black"
)`

= `f"{laptop.name}: {laptop.category.main}/{laptop.category.sub} - ${laptop.price}"`
```

### Example 4: Survey Response Analyzer

Comprehensive survey analysis with multiple `Literal` constraints:

```python
```
from typing import Literal, Optional
```

~SurveyResponse(
    satisfaction: Literal[1, 2, 3, 4, 5],
    nps_score: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    sentiment: Literal['very_negative', 'negative', 'neutral', 'positive', 'very_positive'],
    category: Literal['product', 'service', 'pricing', 'support', 'other'],
    urgency: Literal['low', 'medium', 'high', 'critical'],
    follow_up_needed: bool,
    key_themes: list[str],
    summary
)

@analyze_survey(feedback) -> SurveyResponse:
    Analyze this customer feedback: """<feedback>""" \
    Rate [satisfaction: Literal[1, 2, 3, 4, 5]] (1=very unhappy, 5=very happy), \
    NPS [nps_score: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], \
    overall [sentiment: Literal['very_negative', 'negative', 'neutral', 'positive', 'very_positive']], \
    primary [category: Literal['product', 'service', 'pricing', 'support', 'other']], \
    [urgency: Literal['low', 'medium', 'high', 'critical']], \
    [follow_up_needed: bool], \
    extract [key_themes: list[str]], \
    and write a brief [summary].
    
    = `SurveyResponse(
        satisfaction=satisfaction,
        nps_score=nps_score,
        sentiment=sentiment,
        category=category,
        urgency=urgency,
        follow_up_needed=follow_up_needed,
        key_themes=key_themes,
        summary=summary
    )`

[feedback] = """
I've been using your product for 3 months. The core features are great,
but the customer support response time is terrible. I waited 5 days for
a simple question. Please improve this or I'll switch to a competitor.
"""

[response: SurveyResponse] = `analyze_survey(feedback)`

= ```
print(f"Satisfaction: {response.satisfaction}/5")
print(f"NPS: {response.nps_score}/10")
print(f"Sentiment: {response.sentiment}")
print(f"Category: {response.category}")
print(f"Urgency: {response.urgency}")
print(f"Follow-up: {'Yes' if response.follow_up_needed else 'No'}")
print(f"Themes: {', '.join(response.key_themes)}")
return response.summary
```
```

### Example 5: Code Review Bot

Using `Literal` for severity levels and issue categories:

```python
```
from typing import Literal
```

~CodeIssue(
    severity: Literal['critical', 'high', 'medium', 'low', 'info'],
    category: Literal['bug', 'security', 'performance', 'style', 'maintainability'],
    line_number: int,
    description,
    suggestion
)

~CodeReview(
    overall_quality: Literal['excellent', 'good', 'acceptable', 'needs_work', 'poor'],
    approval: Literal['approved', 'approved_with_comments', 'request_changes', 'rejected'],
    issues: list[CodeIssue],
    summary
)

@review_code(code, language: Literal['python', 'javascript', 'typescript', 'go', 'rust']) -> CodeReview:
    Review this <language> code: \
    ```<code>``` \
    Assess [overall_quality: Literal['excellent', 'good', 'acceptable', 'needs_work', 'poor']], \
    decide [approval: Literal['approved', 'approved_with_comments', 'request_changes', 'rejected']], \
    list all [issues: list[CodeIssue]] found, \
    and provide a [summary].
    = `CodeReview(overall_quality=overall_quality, approval=approval, issues=issues, summary=summary)`

[code_sample] = """
def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)
"""

[review: CodeReview] = `review_code(code_sample, "python")`

= ```
result = f"Quality: {review.overall_quality}\n"
result += f"Decision: {review.approval}\n"
result += f"Issues Found: {len(review.issues)}\n\n"
for issue in review.issues:
    result += f"[{issue.severity.upper()}] {issue.category} (line {issue.line_number})\n"
    result += f"  {issue.description}\n"
    result += f"  Suggestion: {issue.suggestion}\n\n"
return result
```
```

---

## Best Practices

!!! tip "Be Specific with Types"
    Always specify types for LLM outputs to get better structured responses:
    
    ```python
    # Good - specific type (single LLM call)
    List major cities: [cities: list[str]].
    
    # Less good - defaults to str
    List major cities: [cities].
    ```

!!! tip "Use Custom Types for Complex Data"
    For structured data, define custom types:
    
    ```python
    # Good - structured (single LLM call)
    ~Weather(temp: float, humidity: int, conditions)
    Get the weather forecast: [forecast: Weather].
    ```

!!! tip "Keep Outputs on Same Line"
    Remember: each line is a separate LLM call. Keep related outputs together:
    
    ```python
    # Good - single LLM call
    The capital of <country> is [capital] with population [population: int].
    
    # Also good - using line continuation
    Provide info about <country>: capital is [capital], \
    population is [population: int], currency is [currency].
    ```

!!! tip "Handle Optional Data"
    Use union types for fields that may be missing:
    
    ```python
    ~User(
        name,
        email,
        phone: str | None,      # Optional
        age: int | None         # Optional
    )
    ```

---

## See Also

- [Procedures](procedures.md) — Using types in procedure signatures
- [Python Interop](python-interop.md) — Working with Python types
- [Agent Adapters](../adapters/index.md) — How types flow through adapters
- [Syntax Reference](../reference/syntax.md) — Complete type syntax
