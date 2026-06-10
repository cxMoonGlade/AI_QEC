# docs/datasets — reading notes for the local Google QEC hardware datasets

One note per release (full README read + one real `metadata.json` + captured directory
listings). All four are stim-native (`.stim`/`.dem`/`.b8`), CC-BY, Zenodo 13273331 family
(per ADR 0007; the shipped READMEs carry no DOIs themselves). Roles follow the ADR 0007
rung ladder: R2-lite-a (rep-code windows, now) → R2-lite-b (surface d3 windows) →
C = R3 (d5/d7 surface twin on the post-ADR-0008 carrier). All hardware work inherits the
R2-lite claim restrictions: no `do()`, no mechanism attribution, shipped priors/decoder
outputs evaluator/baseline-only.

| Note | Local path (`/home/cx/Document/…`) | Zenodo source | Scale | Role (ADR 0007) |
|---|---|---|---|---|
| [google_72Q_repetition_code_d29.md](google_72Q_repetition_code_d29.md) | `google_72Q_repetition_code_d29/` | 13273331 family (CC-BY) | d=29 rep code, 57q chain on the 72Q device; 2 bases × 100 sequential samples × 10⁵ shots × 1000 cycles = 2×10⁷ shots | **R2-lite-a, now** — 11–15q sliding windows fit `forward/exact`; M1–M5 |
| [google_72Q_surface_code_d3_d5_set1.md](google_72Q_surface_code_d3_d5_set1.md) | `google_72Q_surface_code_d3_d5_set1/google_72Q_surface_code_d3_d5_set1/` | 13273331 family (CC-BY) | XZZX surface code, five d3 (17q) + one d5 (49q) patches; ~21 samples (listing-inferred), last 16 sequential over 15 h | **R2-lite-b** (d3 windows; window-closure map = deliverable); d5 → destination; fresh-calibration control arm |
| [google_72Q_surface_code_d3_d5_set2.md](google_72Q_surface_code_d3_d5_set2.md) | `google_72Q_surface_code_d3_d5_set2/google_72Q_surface_code_d3_d5_set2/` | 13273331 family (CC-BY) | same patches as set1; ~35 samples (listing-inferred), **deliberately mixed calibration freshness** | **R2-lite-b + drift testbed** (H4-adjacent, R2-lite-scoped); only release shipping pij + uninformative prior baselines |
| [google_105Q_surface_code_d3_d5_d7.md](google_105Q_surface_code_d3_d5_d7.md) | `google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7/` | 13273331 family (CC-BY) | XZZX surface code on the 105Q (Willow) device: 9× d3 (17q), 4× d5 (49q), 1× d7 (97q); no sample tier | **Destination (C = R3)** — d5/d7 twin behind the ADR 0008 carrier; Λ/ε_d ladder; d3 windows for spatial closure audits |

`_sources/` holds the cached CC-BY originals: the four shipped READMEs, one real
`metadata.json` per release, the captured directory listings
(`directory_listings.txt`), and the collector script — cached the way `docs/papers/`
caches PDFs. The READMEs' images (`layout.png`, `patches.png`, `logicals.png`) were
not cached.
