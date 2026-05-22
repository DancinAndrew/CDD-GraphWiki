# Delta Specification: NVIDIA NIM Integration (nvidia-nim-integration)

This specification defines the system behavior and contracts for integrating the NVIDIA NIM platform with the CDD-GraphWiki regulatory ingestion layer.

---

## ADDED Requirements

### Requirement: Configure Task-Specific NVIDIA NIM Models
The system **SHALL** allow administrators to configure separate models for different extraction tasks. Specifically, the system **MUST** support the configuration of a chunking model (`NIM_CHUNKER_MODEL`) and an extraction model (`NIM_EXTRACTOR_MODEL`) via environment variables.

#### Scenario: Verify Task-Specific Model Dispatching
- **GIVEN** that the `.env` file is configured with `NIM_CHUNKER_MODEL=meta/llama-3.3-70b-instruct` and `NIM_EXTRACTOR_MODEL=meta/llama-3.3-70b-instruct`.
- **WHEN** the `LLMHierarchicalChunker` is triggered to segment a document.
- **THEN** the chunking task **MUST** be routed to `meta/llama-3.3-70b-instruct`.
- **AND WHEN** the `LLMStructuredExtractor` is triggered to extract compliance obligations.
- **THEN** the extraction task **MUST** be routed to `meta/llama-3.3-70b-instruct`.

### Requirement: Standardize API Communications with NVIDIA NIM
The LLM client **SHALL** communicate with the NVIDIA NIM platform using the standard OpenAI-compatible Chat Completions API protocol over HTTPS. It **MUST** securely pass the API key in the `Authorization` header and request JSON outputs using Pydantic schema mappings.

#### Scenario: Successfully Retrieve Structured JSON Obligations
- **GIVEN** a valid `NVIDIA_API_KEY` in the environment variables.
- **WHEN** the system calls the `LLMClient` with a structured `response_schema` for `ObligationsExtractionResult`.
- **THEN** the client **SHALL** execute an HTTP POST request to the NVIDIA NIM endpoint.
- **AND** the response **MUST** be validated successfully against the `ObligationsExtractionResult` schema before returning it to the pipeline.

### Requirement: Graceful Offline Ingestion Fallback
When the NVIDIA NIM API calls fail due to network errors, invalid credentials, or rate limits, the system **SHALL** catch the exception, log the failure, and gracefully fallback to the offline Mock LLM client mode to ensure pipeline continuity.

#### Scenario: Fallback to Mock Data on Connectivity Failure
- **GIVEN** an invalid `NVIDIA_API_KEY` or a blocked connection to `https://integrate.api.nvidia.com/v1`.
- **WHEN** the system attempts to run the ingestion pipeline.
- **THEN** the client **MUST** log the error and **SHALL** fallback to the `_generate_mock` generator to produce contract-compliant mock Clauses and Obligations.
