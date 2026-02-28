# Tool Registry (Where Applicable)

## Intent
Use registry-style lookup when behavior varies by key/type and hardcoded branching would grow unmaintainable.

## When To Use
- Parser or handler selection by file type/stage.
- Plugin-like extension points where implementations are added over time.

## How To Apply
1. Define a minimal registry contract.
2. Register implementations explicitly at composition root.
3. Resolve by key and fail fast on unknown key.
4. Keep fallback behavior explicit (do not silently pick defaults unless required).

## Example
- Parse worker uses a parser registry to resolve parser implementation from source key/file type.

## Anti-Patterns
- Large `if/elif` chains for extensible handler selection.
- Hidden implicit registration via import side effects.
- Silent fallback to incorrect handler.

## Notes
- This pattern is applicable to parser selection today; broader tool/plugin registry usage is limited in current repo.
