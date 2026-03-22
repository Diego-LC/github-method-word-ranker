# AGENTS.md

## Project Intent

Build a two-container system that mines Python and Java repositories from GitHub, extracts words from function and method names, and renders a near real-time ranking through a producer-consumer architecture.

## Non-Negotiable Constraints

- Keep `miner` and `visualizer` as separate components and separate containers.
- Use Redis as the only integration point between both components.
- Preserve descending processing order by repository stars.
- Support Python and Java naming conventions when extracting words.
- Keep the visualizer responsive without depending on in-memory browser state.

## Repository Map

- `docs/architecture.md`: high-level architecture and runtime flow.
- `docs/event-contract.md`: stream payloads, aggregate keys, and shared environment variables.
- `miner/`: GitHub traversal, parsing, splitting, and event publishing.
- `visualizer/`: Redis consumer, aggregate readers, and Streamlit UI.

## Working Rules For Future Agents

- Read `implementation_plan.md`, `docs/architecture.md`, and `docs/event-contract.md` before changing runtime behavior.
- If you change event payloads or Redis keys, update `docs/event-contract.md` in the same change.
- Do not replace the Java parser with regex unless you also document the tradeoff and acceptance limits.
- Keep GitHub traversal state outside transient memory. Cursor and dedup state must survive restarts.
- Do not move stream consumption into ad hoc Streamlit widget callbacks.
- Documentation files and code comments should be written in Spanish.
- Prefer small, verifiable changes. Add or update tests when behavior changes.

## Implementation Priorities

1. Finalize Redis contract and configuration model.
2. Implement miner traversal by descending star ranges.
3. Implement Python and Java parsers.
4. Implement splitter and normalization rules.
5. Implement continuous consumer and Redis aggregates.
6. Implement Streamlit ranking UI.
7. Finish container wiring, docs, and verification.

## Verification Expectations

- Miner tests should cover splitting, parsing, and traversal logic.
- Visualizer tests should cover event consumption and aggregate updates.
- Integration verification should include `docker compose up --build` and a manual check of the UI at `http://localhost:8501`.

## Safe Defaults

- Prefer ASCII in new files unless the file already uses other characters.
- Keep code under `src/` layouts for both Python components.
- Treat this repository as a scaffold until runtime behavior is explicitly implemented and verified.
