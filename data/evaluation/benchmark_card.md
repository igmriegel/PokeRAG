# Benchmark Dataset Card

## Dataset

- Name: Pokemon TCG RAG Benchmark 100
- Version: `2026-07-24`
- Source corpus manifest: `data/chunks/corpus_manifest.json`
- Benchmark hash: `56b400fa058a9d6466c29bbb9abe01286d72d0b7ce5690fd7e78ba9cb913d87b`

## Purpose

This benchmark exercises retrieval and answer quality against 100 source-resolvable
Pokemon TCG questions covering the bundled demo corpus.

## Coverage

- 100 questions
- 9 source categories
- One canonical answer and one or more ground-truth document IDs per case

## Review policy

- Questions must resolve to the versioned corpus hash above.
- Duplicate question IDs are not allowed.
- Any future expansion must preserve train/dev/test split metadata.
- Reviewer notes and adjudication are tracked alongside this card.

## Limitations

- The benchmark is tied to the bundled demo corpus.
- It is not a public leaderboard and should not be compared across unreviewed corpus changes.

