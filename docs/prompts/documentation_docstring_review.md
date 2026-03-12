# Code and Documentation Review Prompt

Review **all code, documentation, and docstrings** under:

`<TARGET_PATH>`

## Goal
Review the codebase and improve documentation by enforcing **Google-style docstrings**.

## Focus
Examine:

- Code structure and readability
- Module docstrings
- Class docstrings
- Dataclass docstrings
- Function and method docstrings
- Consistency between implementation and documentation
- Naming and terminology consistency

## Documentation Expectations

Docstrings should follow **Google-style format** where applicable, including sections such as:

- `Args`
- `Returns`
- `Raises`
- `Attributes`
- `Yields`

Descriptions should be **clear, concise, and aligned with the implementation**.

## Dataclass Requirements

For **dataclasses**, ensure the docstring clearly documents fields using the **`Attributes:` section**.

Each field description should explain:

- What the field represents
- Its purpose in the object
- Expected values or format when relevant
- Relationships with other fields when applicable

The goal is that a reader can **understand the structure and semantics of the dataclass without reading the implementation**.

## Review Approach

Perform a **code review**, not a documentation audit report.

While reviewing:

- Suggest improvements to weak or unclear docstrings
- Provide **rewritten examples** when documentation is poor
- Recommend **Google-style structures** where missing
- Comment on inconsistencies between code and documentation
- Suggest improvements to clarity and terminology

## Output

Return the **review directly in the response**, organized by:

- file
- class
- function or method

Include **specific recommendations and improved docstring examples where appropriate**.