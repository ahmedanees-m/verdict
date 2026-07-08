#!/usr/bin/env bash
# Download the raw data sources into data/raw/. Open Targets and the Human
# Protein Atlas are queried live during ingestion and are not downloaded here.
# The Moonen supplementary tables are downloaded from the bioRxiv article page
# and placed in data/raw/moonen/.
set -euo pipefail

mkdir -p data/raw/marson data/raw/depmap data/raw/moonen

echo "Downloading the Zhu 2025 differential-expression object (about 16.8 GB)..."
curl -sSL -C - -o data/raw/marson/GWCD4i.DE_stats.h5ad \
  "https://genome-scale-tcell-perturb-seq.s3.amazonaws.com/marson2025_data/GWCD4i.DE_stats.h5ad"

echo "Downloading the DepMap 26Q1 Chronos gene effect matrix (about 431 MB)..."
curl -sSL -o data/raw/depmap/gene_effect.csv \
  "https://ndownloader.figshare.com/files/62677015"

echo "Done. Place the Moonen supplementary tables (media-*.xlsx) in data/raw/moonen/."
