# Tasks for Phase 8: Regulatory Graph Construction & Visualization

## 1. Define Graph Data Contracts
- [ ] 1.1 Add GraphNode, GraphEdge, and RegulatoryGraph models in `src/contracts/models.py`
- [ ] 1.2 Export new models in `src/contracts/__init__.py`
- [ ] 1.3 Compile and export equivalent JSON Schemas to `schemas/` using the compile script
- [ ] 1.4 Add basic schema tests in `tests/test_schemas.py` or new test suite

## 2. Implement Graph Builder and Query Traversal
- [ ] 2.1 Create directory `src/graph/` and add `__init__.py` exporting builder and query classes
- [ ] 2.2 Implement `GraphBuilder` in `src/graph/builder.py` with multi-entity mapping to node/edge elements
- [ ] 2.3 Implement Decision Weaving to mark `decision_path = True` based on `ExplanationPath`
- [ ] 2.4 Implement `GraphQuery` in `src/graph/builder.py` with multi-hop BFS/DFS traversals
- [ ] 2.5 Implement upstream citation query and downstream impact analysis helper methods

## 3. Implement Premium Interactive D3.js HTML Exporter
- [ ] 3.1 Create `src/graph/visualization.py` and implement `GraphExporter`
- [ ] 3.2 Design visual style with Vanilla CSS: dark gradient background and glassmorphic drawer sidebar panel
- [ ] 3.3 Embed D3.js force-directed physics engine and dynamic drag-and-zoom behavior
- [ ] 3.4 Implement Dynamic Focus: click highlighting once-and-twice connected nodes and fading out others
- [ ] 3.5 Implement Neon neon glow HSL theme and decision flow active path animation line dashes
- [ ] 3.6 Ensure PII sensitive data redaction on client attributes panel

## 4. Automation Testing and Verification Loop
- [ ] 4.1 Write comprehensive automated tests in `tests/test_regulatory_graph.py`
- [ ] 4.2 Verify model schemas and serialization correctness
- [ ] 4.3 Verify graph building, relation matching, and decision path weaving correctness
- [ ] 4.4 Verify multi-hop BFS traversals and upstream/downstream search correctness
- [ ] 4.5 Verify HTML exporter outputs correct JSON payloads and css/js elements
- [ ] 4.6 Rerun pytest suite ensuring all 34+ unit tests pass successfully
- [ ] 4.7 Rerun openspec validator on the change directory ensuring all constraints pass

## 5. Delivery and Archiving
- [ ] 5.1 Rerun `openspec validate create-regulatory-graph-construction --strict --no-interactive`
- [ ] 5.2 Archive the change: `openspec archive create-regulatory-graph-construction --yes`
- [ ] 5.3 Commit code changes with Conventional Commits message
- [ ] 5.4 Push changes to remote main branch on github
- [ ] 5.5 Update global `walkthrough.md` with visual design snippets and verification records
