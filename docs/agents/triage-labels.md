# Triage labels

These workflow states describe what a task needs next. They are not severity or priority labels.

| Canonical role | Local `Status:` value | Meaning |
|---|---|---|
| `needs-triage` | `needs-triage` | A maintainer still needs to evaluate the task. |
| `needs-info` | `needs-info` | Work is waiting for missing information or a decision. |
| `ready-for-agent` | `ready-for-agent` | Scope and acceptance are complete enough for autonomous agent work. |
| `ready-for-human` | `ready-for-human` | The task needs human judgment, authorization, coordination, or operation. |
| `wontfix` | `wontfix` | The task was evaluated and will not be actioned; record the reason. |

When an engineering skill names a canonical role, write the matching value in the issue's `Status:`
line.
