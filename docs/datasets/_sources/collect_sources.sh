#!/usr/bin/env bash
# One-shot collector: copy dataset READMEs + one metadata.json sample per dataset
# into docs/datasets/_sources/ and capture directory listings. CC-BY sources
# (Zenodo 13273331 family); cached here like docs/papers/ caches PDFs.
set -eu
cd "$(dirname "$0")"
D=/home/cx/Document

cp "$D/google_72Q_repetition_code_d29/README/README_repetition.md" .
cp "$D/google_72Q_surface_code_d3_d5_set1/google_72Q_surface_code_d3_d5_set1/README/README_surface_d3d5s1.md" .
cp "$D/google_72Q_surface_code_d3_d5_set2/google_72Q_surface_code_d3_d5_set2/README/README_surface_d3d5s2.md" .
cp "$D/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7/README/README_surface_d3d5d7.md" .

for ds in google_72Q_repetition_code_d29 google_72Q_surface_code_d3_d5_set1 \
          google_72Q_surface_code_d3_d5_set2 google_105Q_surface_code_d3_d5_d7; do
  m=$(find "$D/$ds" -name metadata.json 2>/dev/null | head -1)
  if [ -n "$m" ]; then
    cp "$m" "./$ds.metadata.sample.json"
    echo "$ds metadata sample from: $m"
  else
    echo "$ds: NO metadata.json found"
  fi
done

{
  for ds in google_72Q_repetition_code_d29 google_72Q_surface_code_d3_d5_set1 \
            google_72Q_surface_code_d3_d5_set2 google_105Q_surface_code_d3_d5_d7; do
    echo "=== $ds ==="
    ls "$D/$ds/"
    echo "--- directories to depth 2 (first 20) ---"
    find "$D/$ds" -maxdepth 2 -type d | head -20
    echo "--- first sample_00 dir contents ---"
    s=$(find "$D/$ds" -maxdepth 3 -type d -name 'sample_00' | head -1)
    if [ -n "$s" ]; then ls -la "$s"; else echo "(no sample_00 at depth<=3)"; fi
    echo
  done
} > directory_listings.txt

ls -la .
