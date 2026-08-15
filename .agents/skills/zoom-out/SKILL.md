---
name: zoom-out
description: Go up one abstraction layer and map the surrounding code or research landscape before choosing a narrow path. Use when the user asks to zoom out / give broader context, when Codex is unfamiliar with a code area, or when theory-first needs a broad map of terminology, problem families, source clusters, implementations, and no-go boundaries before selecting a small load-bearing reading set.
---

Go up one layer of abstraction before narrowing again. Use the project's domain glossary vocabulary.

- For code, map the relevant modules, owners, callers, data flow, and boundary contracts.
- For research, map the question family, competing formulations, mechanism-to-observable bridges, landmark source
  clusters, known implementations, theorem/no-go boundaries, and unresolved gaps. Search local RAG/KG/reading notes
  first when available.
- For a literature-closure handoff, return a **landscape map**, not a conclusion: `question family | vocabulary |
  formulations | mechanism/observable bridge | source clusters | local assets | no-go boundaries | gaps`.

The map is discovery, not evidence. Do not mark a literature row closed, choose a scientific claim, or replace
full-text close reading. Hand a research map to `close-literature`, which selects and invokes `deep-read-paper` on
the minimum load-bearing set for either `theory-first` or `theory-fix`.
