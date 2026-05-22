# Tasks for NVIDIA NIM Integration (nvidia-nim-integration)

This task list tracks the step-by-step implementation of the NVIDIA NIM platform model integration and task-specific model configurations.

## 1. Environment Setup

- [ ] 1.1 Create the `.env` configuration file in the project root and write the `NVIDIA_API_KEY`, `NIM_CHUNKER_MODEL`, `NIM_EXTRACTOR_MODEL`, and `NIM_BASE_URL` variables.
- [ ] 1.2 Update `.gitignore` to ensure the `.env` file is excluded from version control to prevent credential leaks.

## 2. Extend LLM Client

- [ ] 2.1 Modify `src/extraction/llm_client.py` to parse NVIDIA NIM environment variables (`NVIDIA_API_KEY`, `NIM_BASE_URL`).
- [ ] 2.2 Implement the NVIDIA NIM HTTP client logic using `httpx` to send OpenAI-compatible Chat Completion requests.
- [ ] 2.3 Add structured response parsing to guarantee that the JSON payload returned by NVIDIA NIM is successfully validated against the Pydantic schema using `response_schema.model_validate_json()`.
- [ ] 2.4 Preserve the fallback mechanism to Gemini API and the offline Mock mode if NVIDIA NIM calls fail.

## 3. Adapt Task-Specific Models

- [ ] 3.1 Modify `src/extraction/llm_extractor.py` to allow the chunker and extractor to dynamically fetch their configured model names from the `LLMClient` or environmental variables.
- [ ] 3.2 Ensure `LLMHierarchicalChunker` uses `NIM_CHUNKER_MODEL` (e.g., `meta/llama-3.3-70b-instruct`) and `LLMStructuredExtractor` uses `NIM_EXTRACTOR_MODEL` (e.g., `meta/llama-3.3-70b-instruct`).

## 4. Connection Test and Demo Ingestion

- [ ] 4.1 Create a lightweight verification script `scripts/test_nim_connection.py` to test the API connectivity of the NVIDIA NIM platform and verify both chunker and extractor model configurations.
- [ ] 4.2 Create the interactive ingestion demo runner `demo_ingestion_nim.py` to allow the user to run a complete two-stage ingestion pipeline with MAS Notice 626 sample text using real NIM LLMs.

## 5. Verification and Archiving

- [ ] 5.1 Run all unit tests via `pytest` to confirm that the existing test suite passes and that the new integration works flawlessly under mock and active client modes.
- [ ] 5.2 Validate the OpenSpec change via `openspec validate nvidia-nim-integration --strict --no-interactive`.
- [ ] 5.3 Archive the active change via `openspec archive nvidia-nim-integration --yes`.
- [ ] 5.4 Write a final walkthrough to summarize achievements, including visual output structures and logs.
