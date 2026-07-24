"""
Streamlit Interface for Pokemon TCG Rules Assistant.
"""

import time
import requests
import streamlit as st

st.set_page_config(
    page_title="Pokemon TCG Rules Specialist",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Pokemon TCG Rules Expert Assistant")
st.caption("Official Rulebooks, Tournament Handbooks, Errata & Pokegym Rulings Specialist")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("Backend API URL", value="http://localhost:8000/api/v1")
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

# Main Query Section
user_query = st.text_area(
    "Digite sua dúvida sobre regras, interações ou banimentos no Pokémon TCG:",
    placeholder="Ex: Posso evoluir um Pokémon no primeiro turno usando Rare Candy?",
    height=100
)

if st.button("Buscar Resposta Oficial", type="primary"):
    if not user_query.strip():
        st.warning("Por favor, digite uma pergunta.")
    else:
        with st.spinner("Consultando base de conhecimento oficial do Pokémon TCG..."):
            try:
                response = requests.post(
                    f"{api_url}/query",
                    json={"question": user_query, "top_k": top_k},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()

                    st.markdown("### 💬 Resposta do Juiz Oficial")
                    st.success(data["answer"])

                    # Metadata Metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Tempo de Resposta", f"{data.get('latency_seconds', 0.0):.2f}s")
                    col2.metric("Modelo Utilizado", data.get("model_name", "GPT-4o-mini"))
                    col3.metric("Documentos Consultados", len(data.get("retrieved_chunks", [])))

                    if data.get("rewritten_query"):
                        st.info(f"🔍 **Query Reformulada (Query Rewriting):** `{data['rewritten_query']}`")

                    # Sources & Citations
                    st.markdown("### 📖 Fontes Citadas")
                    for citation in data.get("citations", []):
                        page_num = citation.get('page_number')
                        page_suffix = f" | Pág: {page_num}" if page_num else ""
                        st.markdown(
                            f"- **{citation['document_title']}** ({citation['source']}) | "
                            f"Tipo: `{citation['rule_type']}` {page_suffix}"
                        )

                    # Expandable Chunk Snippets
                    with st.expander("🔍 Ver Trechos de Texto Utilizados (Chunks)"):
                        for idx, chunk in enumerate(data.get("retrieved_chunks", []), start=1):
                            st.markdown(f"**Chunk #{idx}** (Score: `{chunk.get('score', 0.0):.4f}` | Método: `{chunk.get('retrieval_method', 'N/A')}`)")
                            st.code(chunk.get("text", ""), language="markdown")

                    # Feedback Collection
                    st.divider()
                    st.markdown("### 👍 Avalie esta resposta")
                    fb_col1, fb_col2 = st.columns(2)
                    with fb_col1:
                        if st.button("👍 Resposta Precisa"):
                            requests.post(
                                f"{api_url}/feedback",
                                json={
                                    "query": user_query,
                                    "answer": data["answer"],
                                    "rating": 1,
                                    "model_name": data.get("model_name", "GPT-4o-mini"),
                                    "latency_seconds": data.get("latency_seconds", 0.0)
                                }
                            )
                            st.success("Obrigado pelo seu feedback positivo!")
                    with fb_col2:
                        if st.button("👎 Resposta Incorreta / Incompleta"):
                            requests.post(
                                f"{api_url}/feedback",
                                json={
                                    "query": user_query,
                                    "answer": data["answer"],
                                    "rating": -1,
                                    "model_name": data.get("model_name", "GPT-4o-mini"),
                                    "latency_seconds": data.get("latency_seconds", 0.0)
                                }
                            )
                            st.error("Obrigado pelo seu feedback. Registramos a falha para revisão.")

                else:
                    st.error(f"Erro na API backend (Código HTTP {response.status_code}): {response.text}")
            except Exception as exc:
                st.error(f"Falha ao conectar com o serviço backend: {exc}")
