---
name: collaborative-workspace
description: >
  Establish and maintain a good shared working environment for a human developer/researcher
  and an LLM coding agent. Use when the user asks to improve the collaboration setup,
  working rhythm, workspace hygiene, agent-human workflow, pairing mode, research/dev
  session ergonomics, says "\env", "make this environment good for us", "work well together",
  "collaboration norms", "协作环境", "一起工作", or similar requests. Also use at the
  start of broad multi-step development or research sessions when the user wants an
  explicit operating agreement before coding.
---

# Collaborative Workspace

Create a workspace where the human keeps agency and scientific intent, while the agent
keeps context, execution, and verification moving. Treat the goal as practical
collaboration, not etiquette theater.

## Operating Loop

1. Anchor the session.
   - Read project-local guidance first: `AGENTS.md`, `CLAUDE.md`, README, and the specific docs or source files relevant to the task.
   - Check `git status --short` before editing. Treat existing changes as the user's work unless proven otherwise.
   - Identify hard constraints early: environment name, data paths, GPU/CUDA expectations, privacy, large-file locations, and non-negotiable research guardrails.

2. Make the human's intent explicit enough to act.
   - Restate the working objective in one or two sentences when the task is broad.
   - Ask only for decisions that materially affect direction, risk, cost, or interpretation.
   - Prefer a reasonable default when local context makes the answer clear.

3. Keep the workspace humane while working.
   - Share concise progress updates during long work: what is being inspected, what was learned, and what is next.
   - Surface blockers early with the smallest useful explanation and a proposed next move.
   - Do not flood the user with raw logs unless they asked for them; summarize the signal and keep command details reproducible.

4. Protect reproducibility and trust.
   - Use explicit commands, seeds, data roots, shot windows, artifact paths, and environment variables in research workflows.
   - Separate observation, inference, and claim. Say what a run proves, what it suggests, and what remains untested.
   - Avoid promoting diagnostic, optimized-prior, test-selected, or fixture-only evidence into claim evidence.

5. Finish with a clean handoff.
   - Run the narrowest meaningful validation available for the change.
   - Report changed files, commands run, tests or runs attempted, and any residual risk.
   - If the session created durable project knowledge or completed a milestone, use the local cleanup/documentation skill when its trigger phrases apply.

## Future-Stage Rule

Do not hardcode collaboration behavior to the project's current named stages. Names such
as S0, S1, S2, S3, S4, X, Z, or global-routing branches are examples of the current
research map, not the boundary of this skill.

When future versions, stages, branches, protocols, datasets, or claim paths appear:

- Discover the active stage map from the repo: current docs, plans, logs, experiment entrypoints, artifact folders, and recent code.
- Preserve the same collaboration principles for future branches: clear intent, explicit evidence boundaries, reproducible commands, clean handoff, and human-readable workspace state.
- Treat stage-specific conclusions as dated, artifact-backed facts. Do not generalize an old stage's result to a new stage unless the new artifact or docs say so.
- Keep docs and agent guidance extensible: write "current", "as of <date>", "this branch", or "this artifact" when a statement may be superseded.
- If a future stage changes claim criteria, split definitions, routing gates, hardware expectations, or public conclusions, pause for human confirmation before enshrining it.

## Workspace Checks

Use these checks selectively; do not turn every task into ceremony.

- Project shape: `rg --files`, targeted README/docs reads, and skill discovery only when relevant.
- Dirty tree: `git status --short`, then inspect only files relevant to the task before touching them.
- Python environment: prefer the shared project environment when documented, such as `conda run -n aiqec python -m ...`.
- Large data: keep external datasets outside the repo and pass paths through documented flags or environment variables.
- GPU work: verify CUDA availability before treating GPU execution as claim-path evidence.
- Dev servers: start one only when the user needs an interactive app or the repo workflow requires it; give the URL and avoid orphaned sessions before finalizing.

## Editing Norms

- Make the smallest coherent change that solves the request.
- Follow existing project patterns before inventing new abstractions.
- Preserve unrelated user edits, even when they are in files near the change.
- Prefer structured parsers and local helper APIs over brittle string manipulation.
- Update contracts and docs when runtime behavior, public outputs, report keys, commands, or promotion logic changes.

## Communication Norms

- Use short, plain updates while working.
- Be decisive once enough context exists.
- Name uncertainty without dramatizing it.
- Give the user useful handles: file paths, command names, artifact names, and exact dates when timing matters.
- Keep final summaries high signal: outcome, important files, validation, and next risk.

## Research Integrity For This Repository

For the QEC digital twin project, preserve these defaults unless the user explicitly changes the experiment design:

- Detector-event-level claims are not measurement-level or decoder-distillation claims.
- Clean generated priors, optimized-provided priors, fixtures, diagnostics, and claim-eligible branches must be labeled distinctly.
- Held-out real-shot windows are preferred for model claims.
- CUDA/PyTorch paths are preferred for claim-path neural/scoring work; CPU/NumPy paths are acceptable for small tests and debugging.
- Branch conclusions should be phrased as artifact-backed decisions, not universal QEC conclusions.
- Large Google samples should stay outside the repository, with `--max-real-shots` explicit.

## When To Escalate Or Pause

Pause for the user before:

- Taking destructive actions, deleting artifacts, or reverting unowned changes.
- Spending substantial compute time or reading full large samples when a bounded pilot would answer the immediate question.
- Changing scientific claim criteria, split definitions, routing gates, or public-facing conclusions.

Otherwise, keep moving: inspect, implement, validate, and hand back a workspace that is easier for both human and agent to continue from.
