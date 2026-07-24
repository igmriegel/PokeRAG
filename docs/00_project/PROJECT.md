# PROJECT.md - Project Vision & Core Scope

## 1. Executive Summary

The **Pokemon TCG Rules RAG Expert Assistant** is a specialized artificial intelligence system designed to deliver definitive, authoritative, and cited answers to complex questions regarding the Pokemon Trading Card Game (TCG). The system consumes only official rulebooks, tournament handbooks, erratas, ban lists, promo legality status, mega evolution rule changes, and community compendium rulings.

This project is fully designed and implemented as an **Engineering Harness** to maximize scoring according to DataTalks / LLM Zoomcamp rubric criteria and enable autonomous software agent execution.

## 2. Business & Domain Problem

In competitive Pokemon TCG play, precision and evidence are paramount. Matches are governed by intricate interaction rules between card texts, game turn phases, format restrictions, and official errata issued over decades. 

General-purpose LLMs fail in this domain because:
- They lack up-to-date card legality lists (Standard vs Expanded rotation).
- They fabricate non-existent card interactions or apply outdated rules.
- They cannot cite official PDF page numbers or ruling publication dates.

## 3. Official Source Documents

The system relies strictly on the following authoritative sources:
1. **Pokegym Rulings Compendium**: `https://compendium.pokegym.net/all-rulings-by-date/`
2. **Official Rulebook (PDF)**: `https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/cri_rulebook_en.pdf`
3. **Tournament Handbook (PDF)**: `https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-tcg-tournament-handbook-en.pdf`
4. **Alternative Play Handbook (PDF)**: `https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg-alternative-play-handbook-en.pdf`
5. **TCG Errata (PDF)**: `https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg_errata.pdf`
6. **Deck List Guide (PDF)**: `https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-deck-list-85x11.pdf`
7. **Banned Card List (HTML)**: `https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-banned-card-list`
8. **Mega Evolution Rules (HTML)**: `https://www.pokemon.com/us/play-pokemon/about/mega-evolution/mega-evolution-pitch-black-rule-changes-announcement`
9. **Promo Legality Status (HTML)**: `https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-promo-card-legality-status`

## 4. In Scope vs Out of Scope

| Category | In Scope | Out of Scope |
| :--- | :--- | :--- |
| **Data Ingestion** | Automated scraping & PDF extraction of specified official links | Unofficial forum discussions, Reddit posts, YouTube videos |
| **Retrieval** | Dense, BM25, Hybrid RRF, Cross-Encoder Reranking, Query Rewriting | Vector-only naive search |
| **LLM Output** | Cites page numbers, ruling dates, zero hallucination guardrails | Ungrounded creative explanations, price evaluations |
| **UI & Feedback** | Streamlit UI with ratings (+1 / -1) and source chunk inspectability | Native mobile iOS/Android applications |
| **Monitoring** | Prometheus metrics + 6-panel Grafana dashboard | Third-party paid SaaS monitoring (Datadog/NewRelic) |
