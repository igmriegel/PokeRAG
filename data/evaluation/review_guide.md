# Benchmark Review Guide

## Reviewer checklist

1. Confirm each question maps to at least one valid document ID.
2. Confirm the expected source matches the canonical corpus source.
3. Confirm the reference answer is grounded in the current corpus version.
4. Mark ambiguous or duplicate examples for adjudication.
5. Record the reviewer and review timestamp in the manifest.

## Required review metadata

- reviewer 1
- reviewer 2
- adjudicator
- review status
- corpus hash
- benchmark hash

## Split policy

- Benchmark examples must be tagged as `train`, `dev`, or `test` before any new release.
- No leakage is allowed between splits.
- Published evaluation reports must state the split and corpus hashes used.

