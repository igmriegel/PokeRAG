"""
Streamlit web UI for the Pokemon TCG RAG service.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("POKERAG_API_URL", "http://localhost:8000/api/v1")


def build_query_payload(question: str, top_k: int) -> dict[str, Any]:
    return {"question": question, "top_k": top_k}


def build_feedback_payload(
    query: str,
    answer: str,
    rating: int,
    model_name: str,
    latency_seconds: float,
    comment: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": query,
        "answer": answer,
        "rating": rating,
        "model_name": model_name,
        "latency_seconds": latency_seconds,
    }
    if comment:
        payload["comment"] = comment
    return payload


def render_answer(response: dict[str, Any]) -> dict[str, Any]:
    """Summarize the response for display and testing."""
    citations = response.get("citations", [])
    chunks = response.get("retrieved_chunks", [])
    metrics = {
        "latency_seconds": float(response.get("latency_seconds", 0.0)),
        "model_name": response.get("model_name", "unknown"),
        "retrieved_count": len(chunks),
    }
    return {
        "answer": response.get("answer", ""),
        "rewritten_query": response.get("rewritten_query"),
        "citations": citations,
        "chunks": chunks,
        "metrics": metrics,
    }


def fetch_answer(api_url: str, question: str, top_k: int, post: Callable[..., Any] = requests.post) -> dict[str, Any]:
    response = post(f"{api_url}/query", json=build_query_payload(question, top_k), timeout=30)
    response.raise_for_status()
    return response.json()


def send_feedback(
    api_url: str,
    query: str,
    answer: str,
    rating: int,
    model_name: str,
    latency_seconds: float,
    comment: str | None = None,
    post: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    response = post(
        f"{api_url}/feedback",
        json=build_feedback_payload(query, answer, rating, model_name, latency_seconds, comment),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="Pokemon TCG Rules Specialist", page_icon="⚡", layout="wide")
    st.title("⚡ Pokemon TCG Rules Expert Assistant")
    st.caption("Official Rulebooks, Tournament Handbooks, Errata & Pokegym Rulings Specialist")

    with st.sidebar:
        st.header("⚙️ Configuration")
        api_url = st.text_input("Backend API URL", value=DEFAULT_API_URL)
        top_k = st.slider("Top K Retrieved Chunks", min_value=1, max_value=10, value=5)
        st.divider()
        st.markdown("### 📚 Official Data Sources")
        st.markdown("- Official Rulebook (PDF)")
        st.markdown("- Tournament Handbook (PDF)")
        st.markdown("- Alternative Play Handbook (PDF)")
        st.markdown("- TCG Errata (PDF)")
        st.markdown("- Banned Card List (HTML)")
        st.markdown("- Mega Rules & Promo Legality (HTML)")
        st.markdown("- Pokegym Compendium Rulings (Web)")

    user_query = st.text_area(
        "Digite sua dúvida sobre regras, interações ou banimentos no Pokémon TCG:",
        placeholder="Ex: Posso evoluir um Pokémon no meu primeiro turno usando Rare Candy?",
        height=100,
    )

    if st.button("Buscar Resposta Oficial", type="primary"):
        if not user_query.strip():
            st.warning("Por favor, digite uma pergunta.")
            return

        with st.spinner("Consultando base de conhecimento oficial do Pokémon TCG..."):
            try:
                response = fetch_answer(api_url, user_query, top_k)
                summary = render_answer(response)

                st.markdown("### 💬 Resposta do Juiz Oficial")
                st.success(summary["answer"])

                col1, col2, col3 = st.columns(3)
                col1.metric("Tempo de Resposta", f"{summary['metrics']['latency_seconds']:.2f}s")
                col2.metric("Modelo Utilizado", summary["metrics"]["model_name"])
                col3.metric("Documentos Consultados", summary["metrics"]["retrieved_count"])

                if summary.get("rewritten_query"):
                    st.info(f"🔍 **Query Reformulada (Query Rewriting):** `{summary['rewritten_query']}`")

                st.markdown("### 📖 Fontes Citadas")
                for citation in summary["citations"]:
                    page_num = citation.get("page_number")
                    page_suffix = f" | Pág: {page_num}" if page_num else ""
                    st.markdown(
                        f"- **{citation['document_title']}** ({citation['source']}) | "
                        f"Tipo: `{citation['rule_type']}` {page_suffix}"
                    )

                with st.expander("🔍 Ver Trechos de Texto Utilizados (Chunks)"):
                    for idx, chunk in enumerate(summary["chunks"], start=1):
                        st.markdown(
                            f"**Chunk #{idx}** (Score: `{chunk.get('score', 0.0):.4f}` | "
                            f"Método: `{chunk.get('retrieval_method', 'N/A')}`)"
                        )
                        st.code(chunk.get("text", ""), language="markdown")

                st.divider()
                st.markdown("### 👍 Avalie esta resposta")
                fb_col1, fb_col2 = st.columns(2)
                with fb_col1:
                    if st.button("👍 Resposta Precisa"):
                        send_feedback(
                            api_url=api_url,
                            query=user_query,
                            answer=summary["answer"],
                            rating=1,
                            model_name=summary["metrics"]["model_name"],
                            latency_seconds=summary["metrics"]["latency_seconds"],
                        )
                        st.success("Obrigado pelo seu feedback positivo!")
                with fb_col2:
                    if st.button("👎 Resposta Incorreta / Incompleta"):
                        send_feedback(
                            api_url=api_url,
                            query=user_query,
                            answer=summary["answer"],
                            rating=-1,
                            model_name=summary["metrics"]["model_name"],
                            latency_seconds=summary["metrics"]["latency_seconds"],
                        )
                        st.error("Obrigado pelo seu feedback. Registramos a falha para revisão.")
            except Exception as exc:  # pragma: no cover - UI boundary
                st.error(f"Falha ao conectar com o serviço backend: {exc}")


if __name__ == "__main__":
    main()
