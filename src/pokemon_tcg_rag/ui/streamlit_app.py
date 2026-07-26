"""
Streamlit web UI for the Pokemon TCG RAG service.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, cast
from urllib.parse import urlparse

import requests
import streamlit as st

DEFAULT_API_URL = "http://localhost:8000/api/v1"


class BackendAPIError(RuntimeError):
    """Backend error with an HTTP status safe to present in the UI."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        super().__init__(detail)


def get_backend_api_url() -> str:
    """Return the trusted backend URL configured by deployment, not by end users."""
    api_url = os.getenv("POKERAG_API_URL", DEFAULT_API_URL).strip()
    parsed = urlparse(api_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("POKERAG_API_URL must use http or https")
    if not parsed.netloc:
        raise ValueError("POKERAG_API_URL must include a host")
    if parsed.username or parsed.password:
        raise ValueError("POKERAG_API_URL must not include credentials")
    return api_url.rstrip("/")


def build_query_payload(question: str, top_k: int) -> dict[str, Any]:
    return {"question": question, "top_k": top_k}


def build_feedback_payload(
    query_id: str,
    query: str,
    answer: str,
    rating: int,
    model_name: str,
    latency_seconds: float,
    comment: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query_id": query_id,
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
        "query_id": response.get("query_id"),
        "answer": response.get("answer", ""),
        "rewritten_query": response.get("rewritten_query"),
        "citations": citations,
        "chunks": chunks,
        "metrics": metrics,
    }


def build_history_entry(question: str, summary: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded, session-only history entry."""
    citations = [
        citation.get("document_title", "Unknown")
        for citation in summary.get("citations", [])
        if isinstance(citation, dict)
    ]
    return {
        "question": question.strip(),
        "answer": summary.get("answer", ""),
        "query_id": summary.get("query_id"),
        "model_name": summary.get("metrics", {}).get("model_name", "unknown"),
        "citations": citations,
    }


def _is_safe_citation_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.username or parsed.password:
        return False
    return bool(parsed.netloc)


def _render_citation_reference(citation: dict[str, Any]) -> None:
    title = citation.get("document_title", "Unknown")
    source = citation.get("source", "unknown")
    rule_type = citation.get("rule_type", "unknown")
    page_num = citation.get("page_number")
    page_suffix = f" | Pág: {page_num}" if page_num else ""
    source_url = citation.get("source_url")
    st.markdown(f"- **{title}** ({source}) | Tipo: `{rule_type}`{page_suffix}")
    if isinstance(source_url, str) and _is_safe_citation_url(source_url):
        st.link_button("Abrir fonte oficial", source_url)


def fetch_answer(
    api_url: str, question: str, top_k: int, post: Callable[..., Any] = requests.post
) -> dict[str, Any]:
    response = post(
        f"{api_url}/query",
        json=build_query_payload(question, top_k),
        timeout=120.0,
        allow_redirects=False,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = f"Backend request failed with HTTP {response.status_code}"
        try:
            payload = response.json()
            if isinstance(payload, dict) and isinstance(payload.get("detail"), str):
                detail = payload["detail"]
        except (TypeError, ValueError):
            pass
        raise BackendAPIError(response.status_code, detail) from exc
    return cast(dict[str, Any], response.json())


def send_feedback(
    api_url: str,
    query_id: str,
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
        json=build_feedback_payload(
            query_id, query, answer, rating, model_name, latency_seconds, comment
        ),
        timeout=30,
        allow_redirects=False,
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


def main() -> None:
    st.set_page_config(
        page_title="Pokemon TCG Rules Specialist", page_icon="⚡", layout="wide"
    )
    st.title("⚡ Pokemon TCG Rules Expert Assistant")
    st.caption(
        "Official Rulebooks, Tournament Handbooks, Errata & Pokegym Rulings Specialist"
    )

    st.session_state.setdefault("last_response", None)
    st.session_state.setdefault("last_summary", None)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_error", None)

    api_url = get_backend_api_url()
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.caption("Backend API URL configurado pela implantação")
        st.code(api_url, language="text")
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
        history: list[dict[str, Any]] = st.session_state.get("history", [])
        if history:
            st.divider()
            st.markdown("### 🕘 Histórico da sessão")
            for item in history[:5]:
                st.markdown(
                    f"**{item['question']}**  \n"
                    f"Modelo: `{item['model_name']}` | Citations: {len(item['citations'])}"
                )

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
                st.session_state["last_response"] = response
                st.session_state["last_summary"] = summary
                st.session_state["last_error"] = None
                history = cast(
                    list[dict[str, Any]], st.session_state.get("history", [])
                )
                history.insert(0, build_history_entry(user_query, summary))
                st.session_state["history"] = history[:10]
            except BackendAPIError as exc:  # pragma: no cover - UI boundary
                st.session_state["last_error"] = str(exc)
                st.error(f"O backend não conseguiu concluir a consulta: {exc}")
                if exc.status_code == 503 and "quota" in str(exc).lower():
                    st.info(
                        "A chave foi aceita, mas a conta da API OpenAI está sem créditos "
                        "ou atingiu o limite de uso. Revise o faturamento da organização."
                    )
                else:
                    st.info(
                        "Verifique a disponibilidade da API, do Qdrant e do Postgres, "
                        "além da configuração de autenticação."
                    )
            except Exception as exc:  # pragma: no cover - UI boundary
                st.session_state["last_error"] = str(exc)
                st.error(f"Falha ao conectar com o serviço backend: {exc}")
                st.info("Verifique se a API está rodando e acessível pela interface.")

    last_summary: dict[str, Any] | None = st.session_state.get("last_summary")
    if last_summary:
        st.markdown("### 💬 Resposta do Juiz Oficial")
        if last_summary["answer"] == "I don't know.":
            st.warning(last_summary["answer"])
        else:
            st.success(last_summary["answer"])

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Tempo de Resposta", f"{last_summary['metrics']['latency_seconds']:.2f}s"
        )
        col2.metric("Modelo Utilizado", last_summary["metrics"]["model_name"])
        col3.metric(
            "Documentos Consultados", last_summary["metrics"]["retrieved_count"]
        )

        if last_summary.get("rewritten_query"):
            st.info(
                f"🔍 **Query Reformulada (Query Rewriting):** `{last_summary['rewritten_query']}`"
            )

        st.markdown("### 📖 Fontes Citadas")
        for citation in last_summary["citations"]:
            _render_citation_reference(citation)

        with st.expander("🔍 Ver Trechos de Texto Utilizados (Chunks)"):
            for idx, chunk in enumerate(last_summary["chunks"], start=1):
                st.markdown(
                    f"**Chunk #{idx}** (Score: `{chunk.get('score', 0.0):.4f}` | "
                    f"Método: `{chunk.get('retrieval_method', 'N/A')}`)"
                )
                st.code(chunk.get("text", ""), language="markdown")

        st.divider()
        st.markdown("### 👍 Avalie esta resposta")
        comment = st.text_area(
            "Comentário opcional", max_chars=1000, key="feedback_comment"
        )
        fb_col1, fb_col2 = st.columns(2)
        with fb_col1:
            if st.button("👍 Resposta Precisa"):
                send_feedback(
                    api_url=api_url,
                    query_id=last_summary["query_id"],
                    query=user_query,
                    answer=last_summary["answer"],
                    rating=1,
                    model_name=last_summary["metrics"]["model_name"],
                    latency_seconds=last_summary["metrics"]["latency_seconds"],
                    comment=comment or None,
                )
                st.success("Obrigado pelo seu feedback positivo!")
        with fb_col2:
            if st.button("👎 Resposta Incorreta / Incompleta"):
                send_feedback(
                    api_url=api_url,
                    query_id=last_summary["query_id"],
                    query=user_query,
                    answer=last_summary["answer"],
                    rating=-1,
                    model_name=last_summary["metrics"]["model_name"],
                    latency_seconds=last_summary["metrics"]["latency_seconds"],
                    comment=comment or None,
                )
                st.error(
                    "Obrigado pelo seu feedback. Registramos a falha para revisão."
                )

    elif st.session_state.get("last_error"):
        st.warning(
            "Nenhuma resposta pode ser exibida porque a última tentativa falhou."
        )


if __name__ == "__main__":
    main()
