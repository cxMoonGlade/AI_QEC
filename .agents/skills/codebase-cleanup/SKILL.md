---
name: codebase-cleanup
description: Clean a codebase down to its current core by deleting obsolete history, compressing module structure, merging duplicate helpers, shortening names, shrinking public entrypoints/config/docs/tests, and verifying with reference scans and tests. Use when the user asks for broad cleanup, current-only cleanup, removing old paths, deleting legacy code/docs, consolidating helpers, shrinking AGENTS.md/CONTEXT.md, or making the repo smaller and easier to navigate.
---

# Codebase Cleanup

Clean the repo toward the current core. Prefer deletion, consolidation, direct
names, and current-only docs. This skill is more aggressive than architecture
review: it is for executing cleanup, not only proposing refactors.

## Defaults

Use these defaults unless the user says otherwise:

- Scope: all current-core surfaces.
- Deletion: delete obsolete code/docs by default after references, behavior,
  and current-contract content are checked.
- Compatibility: migrate callers and remove shims. Preserve compatibility only
  when the user explicitly requires it or current tests/users still need it.
- Docs: current-only, minimal, no historical explanation. History belongs in
  git, not in active docs.
- Verification: reference scans, targeted tests for touched surfaces, then the
  repo's full test suite after cleanup. If the full suite cannot run, report
  the exact blocker and do not present the cleanup as fully verified.

## Cleanup Intake

Ask this short intake only when the user requests broad cleanup but does not
specify the cleanup level. If the user names the level or target, proceed.

1. Cleanup scope?
   - all current-core surfaces
   - code only
   - public surface only
   - docs only
   - git/artifact hygiene only
2. Deletion policy?
   - delete obsolete code/docs by default
   - keep only if still load-bearing
   - archive only if explicitly requested
3. Compatibility policy?
   - migrate callers and remove shims
   - keep narrow shims temporarily
   - preserve public compatibility
4. Extra verification budget?
   - full suite only
   - full suite plus artifact-level run
   - full suite plus selected performance smoke
   - blocked full suite with explicit reason

For AI_QEC-style cleanup, the recommended answer is: all current-core surfaces;
delete obsolete code/docs by default; migrate callers and remove shims; use
reference scans plus targeted tests, then the full test suite before reporting
the cleanup complete.

## Surface Checklist

When scope is "all current-core surfaces", clean every relevant surface:

- Code: modules, packages, helpers, public exports, private helper placement.
- Public surface: console scripts, wrappers, CLI help, package exports, README
  commands, runbook commands.
- Config: active YAML files, config section names, default paths, output names
  when they define current behavior.
- Tests and fixtures: contract tests, fixture names, expected artifact names,
  obsolete diagnostic tests.
- Docs: README, AGENTS.md or AGENT.md, CONTEXT.md, architecture docs, runbooks,
  stage docs touched by the change.
- Generated artifacts and git hygiene: ignored paths, tracked caches, outputs,
  egg-info, pycache, prepared caches.

## Repo Safety Preflight

Run this before editing:

- Identify the repo root.
- Check `git status --short`.
- Report dirty files before editing.
- Never mix cleanup with unrelated local changes.
- If dirty files overlap the cleanup target, inspect them and work with them;
  ask only when the overlap makes safe cleanup ambiguous.
- If dirty files are unrelated, leave them alone.

## Workflow

1. Establish the current core.
   - Read the repo's current glossary/routing docs first, usually
     `CONTEXT.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, and relevant runbooks.
   - Identify the live commands, packages, configs, tests, and artifact
     contracts. Do not infer the current core from old names alone.
   - Infer current core from live commands, active tests, active configs,
     imports, and current docs together. No single signal is enough.

2. Classify cleanup candidates.
   - Delete: obsolete code, stale docs, unused wrappers, dead configs, old tests.
   - Merge: duplicate helpers, parallel wrappers, repeated artifact loaders.
   - Rename: misleading names, long names, names that encode old concepts.
   - Move: core modules that should sit closer to the responsible package/root.
   - De-track: generated files that should not live in git.

3. Prove whether each candidate is load-bearing.
   - Use `rg` or import scans before deleting or moving.
   - Check callers, tests, configs, docs, console scripts, and fixture paths.
   - For docs, read enough content to classify the document. Low reference
     count is not proof of obsolescence.
   - Treat current implementation maps, role contracts, artifact
     schemas, claim boundaries, glossary material, and active runbook commands
     as load-bearing documentation even when only one doc links to them.
   - If required behavior still exists only in the old path, migrate that
     behavior first.

4. Execute cleanup.
   - Move core modules closer to their owning package/root.
   - Use short, direct names for core objects; prefer one or two human-readable
     words.
   - Merge duplicate helpers into one source of truth.
   - Delete obsolete history instead of explaining it in docs.
   - Remove compatibility shims after callers are migrated, unless explicitly
     preserved.

5. Shrink the public surface.
   - Remove stale console scripts, wrappers, configs, exports, README commands,
     and runbook commands.
   - Active public surface must expose only current entrypoints.
   - If a compatibility entrypoint must stay, keep it narrow and do not let it
     define the current mental model.

6. Update docs minimally.
   - Update only docs that describe the changed current core.
   - Keep AGENTS.md and CONTEXT.md focused on current terms, current package
     routes, and current claim boundaries.
   - Prefer compressing or merging current-contract docs over deleting them.
     If a doc is merged away, prove the destination now preserves the current
     implementation map or contract content before deleting the source.
   - Do not make a document deletable by first removing its only active
     reference. Unlinking and deletion must be justified by the document's
     content being obsolete or fully migrated.
   - Do not add prose about old names, old paths, or why history changed unless
     the user explicitly asks for a migration note.
   - Avoid relative-time wording such as "latest", "old", "new", "legacy",
     "previous", or "temporary" in current docs.

7. Verify.
   - Run targeted `rg` checks for removed names and moved paths.
   - Run import checks or focused tests for moved/merged code.
   - Run the full project test suite after cleanup, even if focused tests pass.
     Focused tests are a localization step; the full suite is the completion
     gate.
   - For artifact-level contracts, run the smallest artifact-producing command
     that proves the current path still works.

8. Report.
   - List what was deleted, merged, renamed, moved, and de-tracked.
   - List what remains only because it is still load-bearing.
   - List next unresolved risks: suspected leftovers, deferred high-risk
     cleanup, skipped tests, compatibility shims, or artifact paths not yet
     verified.
   - Report exact verification commands and whether they passed.

## Hard Rules

- Do not preserve history in active docs. Use git history for history.
- Do not keep archive copies unless the user explicitly asks.
- Do not let active code import archive/deprecated modules.
- Do not leave duplicate helpers with overlapping responsibility.
- Do not leave renamed aliases unless compatibility was explicitly requested.
- Do not rename code without also scanning docs, configs, tests, and public
  entrypoints.
- Do not delete current-contract documentation solely because it has few
  references. Compress it, merge it with proof, or keep it.
- Do not remove a doc's only reference and then treat the doc as unreferenced
  evidence for deletion in the same cleanup pass.
- Do not treat green tests as enough if stale public commands/configs/docs still
  advertise removed paths.
- Do not finish an executed cleanup without running the full project test suite,
  unless it is impossible; when impossible, report the exact blocker and
  remaining risk.
- Do not delete high-risk files, generated outputs, tracked artifact trees, or
  git history without explicit user approval.

## Risk Levels

- Safe: prose cleanup, unused-doc removal, helper consolidation with local
  tests, stale `rg` references, and narrowly scoped deletion of local ignored
  pycache/editor caches.
- Medium: deleting active code after reverse-reference scans, moving modules,
  changing config defaults, renaming fixtures, or deleting broader ignored
  local caches after confirming they are generated and reproducible.
- High: deleting large trees, `git rm --cached` for tracked generated files,
  de-tracking outputs, history rewrite, force push, or deleting anything outside
  the repo. Ask first.
