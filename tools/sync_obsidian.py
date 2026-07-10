#!/usr/bin/env python
"""Sync the QEC knowledge corpus into an Obsidian vault + generate KG entity notes + MOC scaffolds.

ARCHITECTURE (one source of truth). The RAW notes stay authoritative in the repo (+ RAG index); this
vault is a BROWSE / SYNTHESIS *view*. Sync is one-way (repo -> vault). Re-run after adding notes.
  * reading_notes/ memory/ docs/  = GENERATED MIRRORS (edit the source in the repo, then re-run).
  * KG/                           = GENERATED from kg.json (one note per entity; relations as [[links]]).
  * MOC/                          = YOURS (human synthesis). Created once if absent; NEVER overwritten.

Idempotent. No content is modified on mirror (wikilinks stay intact). Run:
    conda run -n aiqec python tools/sync_obsidian.py
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

REPO = Path("/home/cx/Document/AI_QEC/AI_QEC")
VAULT = Path("/mnt/f/obsidian/QEC_simulator")
MEMORY = Path("/mnt/c/Users/cx/.claude/projects/"
              "--wsl-localhost-ubuntu-f-home-cx-Document-AI-QEC-AI-QEC/memory")
KG_JSON = REPO / "outputs/knowledge_graph/kg.json"          # curated 29 KB graph, not kg_full (3 MB)
READING_NOTES = REPO / "docs/papers/reading_notes"
TWIN_DOCS = REPO / "docs/twin_validation"
PAPERS = REPO / "outputs/papers"                            # 138 local PDFs, named <arxiv-id>.pdf

_ARXIV = re.compile(r"(\d{4}\.\d{4,5})")
# inline: an arxiv id that is NOT part of a URL/path (`/…`) and NOT a filename/version suffix (`.md`/`.txt`/`vN`)
_INLINE_ARXIV = re.compile(r"(?<![/\w])(\d{4}\.\d{4,5})(?!\.\w)(?![/\w])")


def _arxiv_year(aid: str) -> str:
    return f"20{aid[:2]}"


def _sync_pdfs(src_dir: Path, dst_dir: Path) -> set[str]:
    """Copy local paper PDFs into the vault (incremental) so notes can link an openable/offline PDF.

    Returns the set of arxiv-ids that have a local PDF. PDFs are immutable (named by arxiv id) -> copy only
    when missing/size-changed, so re-sync stays fast.
    """
    if not src_dir.exists():
        print(f"    [skip] papers dir absent: {src_dir}")
        return set()
    dst_dir.mkdir(parents=True, exist_ok=True)
    ids: set[str] = set()
    n_new = 0
    for pdf in sorted(src_dir.glob("*.pdf")):
        m = _ARXIV.findall(pdf.stem)
        if m:
            ids.add(m[0])
        dst = dst_dir / pdf.name
        if (not dst.exists()) or dst.stat().st_size != pdf.stat().st_size:
            shutil.copy2(pdf, dst)
            n_new += 1
    print(f"    [pdfs] {len(ids)} local PDFs available, {n_new} copied/updated -> {dst_dir}")
    return ids


def _paper_header(own_id: str | None, pdf_ids: set[str]) -> str:
    """A callout at the top of each note: arXiv abs/PDF (always) + local PDF (if present)."""
    if not own_id:
        return ""
    line = f"> 📄 **arXiv** [abs](https://arxiv.org/abs/{own_id}) · [PDF](https://arxiv.org/pdf/{own_id})"
    if own_id in pdf_ids:
        line += f"  ·  📎 **local** [[{own_id}.pdf|PDF]]"
    return line + "\n\n"


def _enrich_reading_notes(src_dir: Path, dst_dir: Path, idx: dict[str, str],
                          pdf_ids: set[str]) -> tuple[int, int]:
    """Mirror reading notes AND linkify: every OTHER in-corpus arxiv-id mentioned in the body -> [[link]].

    Builds the paper<->paper citation graph so the specific papers are connected in the graph view (not
    floating). Also stamps frontmatter (arxiv, year) for Dataview. The repo source stays clean; this is the
    generated vault view.
    """
    if not src_dir.exists():
        print(f"    [skip] source absent: {src_dir}")
        return 0, 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    # arxiv-id -> stem for the WHOLE corpus (idx), plus each note's OWN ids to avoid self-links
    n_notes = n_inline = 0
    for md in sorted(src_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        own = set(_ARXIV.findall(md.stem))
        refs: dict[str, str] = {}                      # stem -> arxiv-id (for the bottom index)
        cnt = [0]

        def _repl(m, _own=own, _idx=idx, _refs=refs, _cnt=cnt):
            aid = m.group(1)
            if aid in _own:                            # never self-link
                return aid
            stem = _idx.get(aid)
            if not stem:                               # not in the corpus -> leave plain
                return aid
            _refs.setdefault(stem, aid)
            _cnt[0] += 1
            return f"[[{stem}|{aid}]]"                 # INLINE clickable citation, in-context

        body = _INLINE_ARXIV.sub(_repl, text)          # linkify every in-text cited arxiv id
        n_inline += cnt[0]
        own_id = next(iter(sorted(own)), None)
        fm = ["---",
              *( [f'arxiv: "{own_id}"', f"year: {_arxiv_year(own_id)}"] if own_id else [] ),
              "tags: [paper, reading-note]", "---", ""]
        head = "" if body.lstrip().startswith("---") else "\n".join(fm)
        link_block = ""
        if refs:
            lines = [f"- [[{stem}]]  `{aid}`" for stem, aid in sorted(refs.items())]
            link_block = "\n\n---\n## 🔗 Cited papers (index)\n" + "\n".join(lines) + "\n"
        paper_hdr = _paper_header(own_id, pdf_ids)
        (dst_dir / md.name).write_text(head + paper_hdr + body + link_block, encoding="utf-8")
        n_notes += 1
    n_links = n_inline
    (dst_dir / "_README.md").write_text(
        "# reading_notes — GENERATED (mirror + auto-linkify)\n\n"
        "> ⚠ Copied from `docs/papers/reading_notes/` and enriched: frontmatter + a `🔗 Linked papers` section\n"
        "> built from arXiv ids cited in each note. **Edit the source in the repo**, then re-run "
        "`tools/sync_obsidian.py`.\n")
    print(f"    [reading_notes] mirrored+linkified {n_notes} notes, {n_links} paper->paper links -> {dst_dir}")
    return n_notes, n_links


def _mirror(src_dir: Path, dst_dir: Path, label: str) -> int:
    if not src_dir.exists():
        print(f"    [skip] source absent: {src_dir}")
        return 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for md in sorted(src_dir.glob("*.md")):
        shutil.copy2(md, dst_dir / md.name)
        n += 1
    (dst_dir / "_README.md").write_text(
        f"# {label} — GENERATED MIRROR\n\n"
        f"> ⚠ These files are a one-way copy of `{src_dir}` in the repo.\n"
        f"> **Edit the source in the repo**, then re-run `tools/sync_obsidian.py`. Edits here are lost on re-sync.\n")
    print(f"    [{label}] mirrored {n} files -> {dst_dir}")
    return n


def _reading_note_index() -> dict[str, str]:
    """arxiv-id -> reading-note stem, for cross-linking KG paper nodes to their 精读 notes."""
    idx: dict[str, str] = {}
    if not READING_NOTES.exists():
        return idx
    for md in READING_NOTES.glob("*.md"):
        for aid in _ARXIV.findall(md.stem):
            idx[aid] = md.stem
    return idx


def _export_kg(kg_json: Path, dst: Path, note_idx: dict[str, str]) -> int:
    if not kg_json.exists():
        print(f"    [skip] KG absent: {kg_json}")
        return 0
    g = json.loads(kg_json.read_text())
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    out: dict[str, list[str]] = {nid: [] for nid in nodes}     # id -> outgoing "relation -> [[target]]"
    for e in g.get("links", []):
        s, t, rel = e.get("source"), e.get("target"), e.get("relation", "related")
        if s in out:
            tgt_name = nodes.get(t, {}).get("name", t)
            out[s].append(f"- **{rel}** → [[{t}|{tgt_name}]]")
    dst.mkdir(parents=True, exist_ok=True)
    for nid, node in nodes.items():
        name = node.get("name", nid).replace('"', "'")
        typ = node.get("type", "entity")
        desc = node.get("description", "")
        aid = next(iter(_ARXIV.findall(desc)), None)
        rn = note_idx.get(aid) if aid else None
        lines = [f"---", f'title: "{name}"', f"type: {typ}", f"kg_id: {nid}", "tags: [kg]", "---", "",
                 f"# {name}", "", f"*{desc}*  ·  `type: {typ}`", ""]
        if rn:
            lines += [f"📄 精读 note: [[{rn}]]", ""]
        rels = out.get(nid, [])
        lines += ["## Relations", *(rels if rels else ["- *(no outgoing relations in the graph)*"]), ""]
        (dst / f"{nid}.md").write_text("\n".join(lines))
    print(f"    [KG] generated {len(nodes)} entity notes (+ {sum(len(v) for v in out.values())} relations) -> {dst}")
    return len(nodes)


MOCS = {
    "_Home.md": """# QEC Simulator — Home (Map of Contents)

Top-level index of the knowledge vault. This vault is a **browse / synthesis view** over the repo corpus
(source of truth stays in the repo + RAG). Folders `reading_notes/`, `memory/`, `docs/`, `KG/` are generated;
edit MOCs here freely.

## Maps of Content
- [[notion3-arc]] — the closed notion-3 quantum-memory arc (K → revival → protocol boundary)
- [[simulator-gates]] — the 8-gate CoupledCycleTeacher contract + status
- [[nonmarkovianity-witnesses]] — the classical/quantum memory witness landscape

## Corpus
- `reading_notes/` — 精读 notes (mirror; also the RAG corpus)
- `memory/` — distilled project facts (mirror; the `[[project-…]]` graph)
- `docs/` — preregs, closures, synthesis (mirror)
- `KG/` — entity/relation notes (generated from `kg.json`; open **Graph view** to browse)

## Keep fresh
Add a note in the repo → `conda run -n aiqec python tools/sync_obsidian.py` → `--build --force` the RAG.
""",
    "notion3-arc.md": """# MOC — notion-3 quantum-memory arc (CLOSED)

**Verdict:** notion-3 (genuine quantum non-classicality / quantum memory) is a **principled protocol boundary**
for passive QEC — not a failure. Genuine quantum memory is an *active-channel* property; the passive
fixed-stabilizer syndrome record is Pauli-twirled and carries at most **notion-2 classical multi-time memory**.

## The narrative (each claim → its kill/closure)
1. **K / K_X / K_Z** proposed as a quantum witness → **forgeable** (basis-symmetric incoherent AD). See [[project-jointparity-K-sign-blind-sx1]], [[project-notion3-relaxation-dualaxis-Kz-forgeable]].
2. **Negativity/concurrence revival** (Control 3b) → **RETRACTED** — it is an RHP *non-Markovianity* detector, forged by classical RTN (Control 0b); backflow witnesses *memory, not quantumness* ([[phase_diagrams_information_backflow_2601.18822]]).
3. **Bäcker C♯<C** (Control 3, single-qubit) → **survives** but is an *active-tomography* quantity, sufficient-not-necessary. [[backer_entropic_witness_quantum_memory_2501.17660]]
4. **Flag #1 — expressed on the passive record?** → **UNCLOSABLE**: every witness needs active interventions. [[giarmatzi_witnessing_quantum_memory_process_tensor_1811.03722]], [[taranto_hierarchy_multitime_classical_memory_2307.11905]]

## The closure (two literature-nailed premises)
- **(A) active-intervention requirement** — quantum memory can't be passively observed (Giarmatzi / process-tensor).
- **(B) syndrome Pauli-twirl washout** — extraction erases coherent + non-unital structure ([[project-cpdiv-notion-hierarchy-passive-record]]; QMCtwin; Kattemolle; Wagner passive-syndrome→Pauli-only).
- **⇒ (C)** passive record = notion-2 classical only. Doc: [[notion3_protocol_boundary_closure]].

## Deferred (trigger-gated, NOT dropped)
Dynamic / feed-forward QEC (adaptive syndrome, non-Markovian feedback) *does* provide interventions →
notion-3 accessible in principle = the **twin / active-characterization** project. Not the simulator.
""",
    "simulator-gates.md": """# MOC — Simulator (CoupledCycleTeacher) 8-gate contract

Source: [[project-qec-coupling-simulator-contract]]. The simulator = a **faithful forward generator**;
validity = record vs independent oracles + anti-toy discriminability from a matched Markov/CP-div null.

| Gate | What | Status |
|---|---|---|
| G0 | anti-toy pre-build (imprint > shot noise) | ❌ FAIL (registered STOP; ζ×γφ sub-detectable) |
| G1 | schedule-faithfulness (real XZZX) | ⬜ OPEN |
| G2 | joint-L (Axis-1 coupling) | ✅ PASS/certified |
| G3 | RHP-onset / observable wedge | 🟡 partial (source layer) |
| G4 | source imprint on **records** (earned-line) | ❌ CAPPED (mild 1/f no record-level ΔLER) |
| G5 | baseline-fairness | ⬜ OPEN |
| G6 | coupling-ablation on records | 🟡 reframed → faithfulness report |
| G7 | isolation (scramble/cheat-twin) | ⬜ OPEN |
| G8 | durability | ⬜ OPEN |

**Where value lives:** faithful forward infrastructure + G2 joint-L coupling; robust contribution at the
**source/channel layer**, not record-level. See [[project-coupling-nonmarkovian-is-the-contribution]],
[[project-coupled-cycle-teacher-build-state]].

**Mainline pivot (#15):** corrected multi-time notion-2 legitimacy test @ realistic source. Prereg:
[[corrected_multitime_observable_prereg]]. Guardrails: right observable (multi-time CMI/G², not 2-point TV) +
effect-size go/no-go @ realistic source (1/f must separate from slow-RTN at feasible k).
""",
    "nonmarkovianity-witnesses.md": """# MOC — non-Markovianity & memory witnesses

The map that resolved the notion-3 arc: what each witness actually certifies, and why the passive record
can't carry the quantum ones.

## Classicality / Kolmogorov
- [[milz_when_nonmarkovian_process_classical_1907.05807]] — process-tensor classicality (Kolmogorov / NDGD).
- [[budini_dni_violation_hallmark_2301.02500]] — DNI/Kolmogorov witness; needs **pointer-basis (adaptive)** measurement.
- [[maity_kolmogorov_classicality_signatures_2601.01122]] — viol ∝ coherence; =0 pointer, manufactured off-basis (⇒ K forgeable).
- [[smirne_coherence_nonclassicality_markov_1709.05267]] — coherence⟺non-classicality **only Markovian**; fails non-Markovian.

## Quantum memory (need active interventions)
- [[giarmatzi_witnessing_quantum_memory_process_tensor_1811.03722]] — quantum memory = process-tensor entanglement; needs interventions.
- [[taranto_hierarchy_multitime_classical_memory_2307.11905]] — strict hierarchy M ⊊ CDC ⊊ CM ⊊ SEP ⊊ QM.
- [[backer_entropic_witness_quantum_memory_2501.17660]] — E♯<E witness (the *bound*, not bare revival).

## Backflow ≠ quantumness
- [[phase_diagrams_information_backflow_2601.18822]] — backflow witnesses **memory, not quantumness per se** (classical kernels give the same).
- [[fanchini_independent_common_nonmarkovianity_1301.3146]] — collective NM is super-additive (independent AD can't capture).

## The QEC-protocol boundary
- Passive syndrome Pauli-twirls out coherent + non-unital structure ⇒ notion-2 only.
- See [[notion3_protocol_boundary_closure]] and [[project-cpdiv-notion-hierarchy-passive-record]].
""",
}


def _scaffold_mocs(dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    created = 0
    for name, body in MOCS.items():
        p = dst / name
        if p.exists():
            print(f"    [MOC] keep (exists, human-owned): {name}")
            continue
        p.write_text(body)
        created += 1
    print(f"    [MOC] scaffolded {created} new (existing left untouched)")
    return created


def main() -> int:
    print("=" * 88)
    print(f"Obsidian sync  repo -> {VAULT}")
    print("=" * 88)
    assert VAULT.parent.exists(), f"vault parent not accessible: {VAULT.parent} (is F: mounted?)"
    VAULT.mkdir(parents=True, exist_ok=True)

    pdf_ids = _sync_pdfs(PAPERS, VAULT / "pdfs")
    _enrich_reading_notes(READING_NOTES, VAULT / "reading_notes", _reading_note_index(), pdf_ids)
    _mirror(MEMORY, VAULT / "memory", "memory")
    _mirror(TWIN_DOCS, VAULT / "docs", "docs")
    _export_kg(KG_JSON, VAULT / "KG", _reading_note_index())
    _scaffold_mocs(VAULT / "MOC")

    (VAULT / "README.md").write_text(
        "# QEC Simulator knowledge vault\n\n"
        "Browse/synthesis **view** over the repo corpus (source of truth = repo + RAG). "
        "Start at [[_Home]].\n\n"
        "- `reading_notes/` `memory/` `docs/` `KG/` — **generated** (re-run `tools/sync_obsidian.py`).\n"
        "- `MOC/` — **yours** (human synthesis; never overwritten).\n\n"
        "Open **Graph view** to browse the KG; use the MOCs to navigate the arcs.\n")
    print("\n[done] vault synced. Open F:\\obsidian\\QEC_simulator in Obsidian; start at MOC/_Home.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
