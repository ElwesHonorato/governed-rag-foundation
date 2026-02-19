# DataHub Migration Plan (3 Steps)

## Goal
Replace Marquez with DataHub in `domains/lineage`, prove DataHub succeeds on the same lineage fanout scenario where Marquez failed, then complete downstream integration and validation work.

## Step 1: Replace Lineage Domain Runtime (Marquez -> DataHub)
Objective: Spin up DataHub architecture in containers following the repository domain pattern and remove Marquez runtime from `domains/lineage`.

Scope:
1. Remove Marquez runtime files and references from the lineage domain:
   - Delete/replace `domains/lineage/marquez.yml`.
   - Replace Marquez services in `domains/lineage/docker-compose.yml` with DataHub services.
2. Keep repo orchestration conventions unchanged:
   - Continue using `./stack.sh up lineage`.
   - Keep external network behavior and domain isolation style aligned with existing domains.
3. Add required DataHub env variables to `.env.example` (and `.env` as needed for local run).
4. Update lineage domain docs to reflect DataHub endpoints and health checks.

Deliverables:
- Updated `domains/lineage/docker-compose.yml` with DataHub stack.
- Marquez config removed from lineage domain.
- Updated `domains/lineage/README.md`.
- Updated root docs/env references from Marquez to DataHub where runtime instructions are impacted.

Exit Criteria:
- `./stack.sh up lineage` starts DataHub lineage stack successfully.
- `./stack.sh ps lineage` shows healthy lineage services.
- OpenLineage ingestion endpoint is reachable from local workflow.

## Step 2: Replay Known Lineage Payloads (Marquez Failure Case Validation)
Objective: Re-run lineage examples under `domains/lineage/docs/marquez_fanout_lineage_bug_investigation` against DataHub and verify expected fanout lineage behavior.

Scope:
1. Review and reuse existing payload assets and scripts in:
   - `domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads`
   - `domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation`
   - migration helper commands documented in the lineage README and Make targets
2. Post both:
   - Happy-path chain payloads.
   - The fanout case that previously showed edge loss in Marquez.
3. Capture evidence from DataHub API/UI for the embed fanout case (part1 + part2 lineage continuity).
4. Document results in a new DataHub-oriented validation note in the lineage docs folder.

Deliverables:
- Repro commands updated for DataHub endpoint(s).
- Recorded API/UI evidence for fanout lineage correctness.
- A pass/fail statement for "Marquez failed case" under DataHub.
- Readme with the steps on how to reproduce the behaviour

Exit Criteria:
- All payload POSTs succeed for DataHub ingestion.
- Fanout lineage remains connected for both chunk branches (no overwrite/disconnect equivalent).
- Validation note is committed in `domains/lineage/docs/...`.

## Step 3: Downstream Integration, Reviews, and Cleanup
Objective: Complete all non-runtime downstream work after DataHub ingestion correctness is confirmed.

Scope:
1. Application and worker integration review:
   - Migrate config keys from `MARQUEZ_*` to DataHub/lineage-generic variables.
   - Add/adjust lineage emitter wiring in `libs/pipeline-common` and worker stages.
2. Documentation and developer workflow review:
   - Update `README.md`, domain READMEs, and runbooks.
   - Ensure local bootstrap and troubleshooting commands are current.
3. Quality review:
   - Add/expand tests for lineage payload generation and emission paths.
   - Run targeted validation for impacted workers/domains.
4. Final cleanup:
   - Remove deprecated Marquez references not needed for historical docs.

Deliverables:
- Code-level lineage integration aligned with DataHub.
- Updated docs across repo.
- Test coverage for lineage emission paths.
- Cleaned Marquez leftovers (except intentional historical investigation docs).

Exit Criteria:
- End-to-end pipeline emits lineage successfully to DataHub.
- Documentation matches actual runtime and commands.
- Migration branch is ready for final review/merge.

## Notes
- Historical Marquez investigation artifacts remain valuable for regression comparison and should be retained unless explicitly requested otherwise.
- Step 2 is the migration gate: downstream refactors proceed only after DataHub passes the previously failing fanout scenario.
