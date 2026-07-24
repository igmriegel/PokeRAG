# Dependency policy

The project now carries separate pinned profiles for:

- `requirements.runtime.txt` — production/runtime services
- `requirements.dev.txt` — developer and CI tooling
- `requirements.eval.txt` — evaluation and benchmarking

Rules:

1. Runtime images install only `requirements.runtime.txt`.
2. Developer environments install the project editable plus `requirements.dev.txt`.
3. Evaluation jobs install `requirements.eval.txt` only when running benchmark suites.
4. A dependency change must update the relevant profile lock and include a short risk note.
5. Security review should prefer an audited replacement or an explicit exception over a silent upgrade.

The canonical safety checks for dependency updates are:

- `pip-audit` against the resolved runtime graph
- SBOM generation for release artifacts
- deterministic local install from the pinned profile files
