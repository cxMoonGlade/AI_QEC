# Issue tracker: Local Markdown

Issues and PRDs for this repository live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`.
- The PRD is `.scratch/<feature-slug>/PRD.md`.
- Implementation issues are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`.
- Triage state is a `Status:` line near the top of each issue file; the allowed values are defined
  in `docs/agents/triage-labels.md`.
- Comments and decision history append under a `## Comments` heading.

## Skill operations

When a skill says to publish to the issue tracker, create the corresponding file under
`.scratch/<feature-slug>/`. When it says to fetch a ticket, read the referenced local Markdown file.
