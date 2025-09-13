# LLM Candidate Arbitrator Model Card

## Goals
- Select the best response from multiple language model candidates.
- Balance response quality and context adherence via weighted scoring.

## Data
- Consumes candidate outputs produced by upstream LLMs.
- No parameter training; uses simple deterministic scoring.

## Limitations
- Effectiveness depends on quality of provided candidate scores.
- Linear weighting may not capture complex evaluation criteria.

## Version
- 1.0
