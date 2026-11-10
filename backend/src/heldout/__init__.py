"""
Held-out evaluation: test the rule-based extractor on MAS Notice 626 paragraphs
that were never used while the rules were written.

- convert: official PDF -> verbatim Markdown in the same format as data/sources/
- evaluate: run the extractor on held-out paragraphs and score it against data/heldout/gold_obligations.yaml
- llm_compare: run an LLM extractor on the same paragraphs, cache its raw answers, and score them offline
"""
