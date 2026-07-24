# LLM Module (`llm/`)

This directory contains LLM interaction and prompt management code:
- `client.py`: Client interface wrapping LLM calls (e.g. OpenAI GPT-4o-mini).
- `prompts.py`: Strictly constrained system prompt templates enforcing rulebook-only citations and judge persona.
- `rag_chain.py`: Full end-to-end RAG chain execution.
