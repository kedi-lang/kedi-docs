# Word Chain Game

This example demonstrates a recursive-like flow where the LLM generates a sequence of words, each starting with the last letter of the previous one.

## The Code

```python
@word_chain(word):
  <`print(f"word chain starts with {word}...")`>

  [word] is a word that starts with the last letter of <word>.
  <`print(word)`>

  [word] is a word that starts with the last letter of <word>.
  <`print(word)`>

  [word] is a word that starts with the last letter of <word>.
  <`print(word)`>

  [word] is a word that starts with the last letter of <word>.
  <`print(word)`>

  [word] is a word that starts with the last letter of <word>.
  <`print(f"word chain ends with {word}...")`>

  = <word>
```

## How it Works

1.  **Variable Reassignment**: Notice how `[word]` is defined multiple times. In Kedi, defining a variable with `[]` assigns a new value to it.
2.  **Context**: The LLM sees the previous prompts and outputs in its context window (unless explicitly cleared), so it "knows" the chain it is building.
3.  **Python Side Effects**: We use `<`print(...)`>` to log progress to the console during execution.

## Running It

```python
= <word_chain("apple")>
```

**Possible Output:**

```text
word chain starts with apple...
elephant
tiger
rabbit
turtle
eagle
word chain ends with eagle...
```
