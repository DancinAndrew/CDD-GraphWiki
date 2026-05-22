# Delta Spec - Evaluation Harness

This specification defines the behavior of the compliance evaluation harness and decoupled diagnostic engine.

## ADDED Requirements

### Requirement: Multi-dimensional Quantitative Evaluation
The evaluation harness MUST evaluate compliance reasoning quality across five dimensions: retrieval, extraction, conflict detection, checklist correctness, and citation faithfulness.

#### Scenario: Evaluate Ingested CDD-GraphWiki Output
* **GIVEN** a gold ground truth dataset containing customer contexts, obligations, and checklists
* **WHEN** the `EvaluationHarness` is executed with the CDD-GraphWiki output
* **THEN** it SHALL calculate precision, recall, f1-score, and accuracy for each dimension
* **AND** it SHALL output an `EvaluationMetrics` object for each dimension without hallucination.

### Requirement: Decoupled Error Diagnosis
The evaluation system SHALL decouple and diagnose any mismatches between the generated checklists and the gold dataset to pinpoint the exact failing phase.

#### Scenario: Identify Retrieval and Reasoning Failures
* **GIVEN** a generated checklist that does not match the gold checklist decision or requirements
* **WHEN** the diagnostic engine runs the decoupled diagnostic tree
* **THEN** it MUST classify the root cause into exactly one of: `retrieval`, `extraction`, `graph_modeling`, `conflict_handling`, or `reasoning`
* **AND** it SHALL output a structured `DiagnosticReport`.

### Requirement: Citation Faithfulness & Hallucination Checking
The evaluation harness MUST inspect the citations generated within the checklists to verify their absolute authenticity.

#### Scenario: Detect Fabricated Citation
* **GIVEN** a checklist citation referencing a nonexistent clause or a mismatched section
* **WHEN** the faithfulness checker validates the citation against the global graph or source clauses
* **THEN** it SHALL identify the citation as unfaithful
* **AND** it SHALL trigger a citation hallucination warning in the final comparison report.

### Requirement: Baseline Comparison Benchmarking
The system SHALL support benchmarking against a naive `VectorRAGBaseline` chatbot simulator.

#### Scenario: Benchmarking Comparison Report Generation
* **GIVEN** the `EvaluationHarness` runs benchmarking on both CDD-GraphWiki and `VectorRAGBaseline`
* **WHEN** the comparison is completed
* **THEN** it MUST generate a `ComparisonReport` summarizing metrics for both systems
* **AND** it SHALL demonstrate lower citation hallucination rate and higher checklist accuracy for CDD-GraphWiki.
