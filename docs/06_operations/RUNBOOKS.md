# Operational Runbooks

This document collects the minimum repeatable procedures for the final production
qualification sprint.

## Owners

| Area | Owner | Escalation |
| :--- | :--- | :--- |
| API / backend | Backend | Tech Lead |
| Retrieval / LLM | ML | Tech Lead |
| Infrastructure | DevOps / Infra | Platform |
| Security | Security | Tech Lead + Security |
| Product UX | Frontend | Product |

## 1. Query failure or backend unavailable

Symptoms:
- UI shows backend connection errors.
- `/api/v1/query` returns 503/500.

Safe checks:
```bash
make run-api
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
```

Mitigation:
1. Confirm Postgres and Qdrant are reachable.
2. Confirm `OPENAI_API_KEY` is configured in production only.
3. Inspect structured logs for `trace_id` and `error_id`.

## 2. SLO or provider cost breach

Symptoms:
- Prometheus alerts `PokemonRAGHighLatencyP95` or `PokemonRAGHighProviderSpend`.

Safe checks:
```bash
curl -s http://localhost:9090/api/v1/alerts
curl -s http://localhost:8000/metrics | rg "pokemon_rag_(query_latency_seconds|provider_cost_usd_total)"
```

Mitigation:
1. Reduce traffic or disable expensive model stages.
2. Review query rewriting and reranking settings.
3. Compare the live panel against the latest release note.

## 3. Feedback write failure

Symptoms:
- UI feedback button reports a persistence error.
- Postgres reports unique constraint or connectivity errors.

Safe checks:
```bash
python -m pytest tests/unit/test_feedback_store.py
```

Mitigation:
1. Confirm the query id exists and the comment is under 1000 characters.
2. Check the `user_feedback` table and service credentials.
3. Re-run the feedback submission after database recovery.

## 4. Rollback

If the release is unstable:
1. Revert to the last approved image digest.
2. Re-run migrations only if the schema changed forward-compatible.
3. Confirm `/ready` and the smoke query/feedback journey.
