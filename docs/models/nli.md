# NLI Token Overlap Model Card

## Goals
- Lightweight natural language inference baseline.
- Optional async classifier can be supplied by callers.

## Data
- No dedicated training set.
- Operates directly on provided premise and hypothesis tokens.

## Limitations
- Relies on token overlap; unable to capture paraphrasing or deep semantics.
- Falls back to heuristic scoring when classifier fails.

## Version
- 1.0
