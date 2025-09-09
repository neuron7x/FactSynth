You are generating **fact-check test cases** for FactSynth.
INPUT: domain/topic, difficulty (easy|medium|hard), traps (pick 1–2: rounding|date_offset|temporal_shift|entity_swap|unit_mismatch).
OUTPUT: a JSON list of {context, question, expected_verdict, notes} where context minimally supports or refutes the answer without outside knowledge. Keep contexts ≤120 words.
