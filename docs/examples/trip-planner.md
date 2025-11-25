# Trip Planner

This example demonstrates how to build a multi-step travel planning agent using Kedi's custom types and procedure composition.

It showcases:

- **Custom Types**: Defining structured data for the LLM to populate.
- **Procedure Composition**: Breaking down a complex task into smaller, manageable steps.
- **Correct Prompting**: Using line continuation `\` to keep prompts and output fields in a single agent run.

## The Data Structures

We define custom types to ensure the LLM returns structured JSON data.

```python
~Activity(name: str, duration: str, cost: float)
~DayPlan(day: int, activities: list[Activity], summary: str)
~Trip(destination: str, total_cost: float, itinerary: list[DayPlan])
```

## The Procedures

### 1. Suggesting Activities

This procedure asks the LLM to suggest activities for a specific location and interest.

```python
@suggest_activities(location: str, interest: str) -> list[Activity]:
    You are a local travel guide. \
    Suggest 3 unique [activities: list[Activity]] in <location> for someone interested in <interest>.
    = <activities>
```

!!! success "Single Agent Run"
    Notice the use of `\` at the end of the lines. This ensures that the entire prompt and the output field `[activities]` are sent to the LLM in a **single request**.

### 2. Planning a Day

This procedure takes a list of activities and organizes them into a day plan.

```python
@plan_day(day_num: int, activities: list[Activity]) -> DayPlan:
    Organize these <activities> into a coherent [plan: DayPlan] for day <day_num>.
    = <plan>
```

### 3. The Main Planner

This procedure orchestrates the entire process.

````python
@create_trip(destination: str, interests: list[str], days: int) -> Trip:
    # Python block to initialize variables
    [itinerary: list[DayPlan]] = ```
    return []
    ```

    # Loop through each day (using Python logic)
    [daily_plans: list[DayPlan]] = ```
    plans = []
    for i in range(1, days + 1):
        # We can call Kedi procedures from Python!
        # Let's pick an interest for the day cyclically
        interest = interests[(i-1) % len(interests)]

        # 1. Get activities
        acts = suggest_activities(destination, interest)

        # 2. Plan the day
        day_plan = plan_day(i, acts)
        plans.append(day_plan)
    return plans
    ```

    # Calculate total cost using Python
    [total_cost: float] = ```
    cost = 0
    for plan in daily_plans:
        for act in plan.activities:
            cost += act.cost
    return cost
    ```

    = `Trip(destination=destination, total_cost=total_cost, itinerary=daily_plans)`
````

## Running the Planner

```python
[my_trip] = <create_trip("Tokyo", `["Food", "History", "Tech"]`, 3)>

# Print the result nicely
<`print(f"Trip to {my_trip.destination} (Total: ${my_trip.total_cost})")`>
<`print(my_trip.itinerary)`>
= Done
```
