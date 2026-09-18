"""
Assistant IA — AM TRANSIT / Contrôle de gestion
================================================

Application Streamlit : chatbot alimenté par l'API Claude (Anthropic), capable
d'exploiter une bibliothèque de documents (Excel, CSV, PDF) liés au contrôle
de gestion — grand livre, balances, budgets, factures, etc.

Lancement local :
    streamlit run app.py

Déploiement : voir README.md (Streamlit Community Cloud recommandé).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

import backend

# --------------------------------------------------------------------------
# Configuration de la page
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Assistant AM TRANSIT",
    page_icon="📊",
    layout="wide",
)

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

SYSTEM_PROMPT = """Tu es l'assistant de contrôle de gestion de Mamadi Keita, Contrôleur de Gestion \
chez AM TRANSIT SAS (Groupe SONOCO), une entreprise de transport et logistique basée à Conakry, \
Guinée. L'entreprise travaille sous le référentiel SYSCOHADA Révisé 2018, utilise Sage 100 \
Comptabilité Premium et GESCOM, et sa devise est le Franc Guinéen (GNF).

Tu as accès à une bibliothèque de documents (grands livres, balances, budgets, factures, PDF...) \
via des outils :
- list_documents : liste les documents disponibles et leur structure (colonnes, feuilles).
- query_dataframe : exécute une expression pandas sur un document tabulaire (Excel/CSV) pour \
répondre précisément à une question chiffrée (sommes, filtres, regroupements...).
- read_document_text : extrait le texte d'un document PDF.

Consignes :
- Commence toujours par appeler list_documents si tu n'es pas sûr de ce qui est disponible.
- Utilise query_dataframe pour tout calcul précis plutôt que d'estimer — ne jamais inventer de chiffres.
- Réponds en français, de façon claire et professionnelle, avec les montants en GNF formatés \
(séparateurs de milliers).
- Si aucune donnée ne permet de répondre, dis-le clairement plutôt que de deviner.
"""

TOOLS = [
    {
        "name": "list_documents",
        "description": "Liste tous les documents disponibles dans la bibliothèque, avec leur type et leur structure (feuilles/colonnes pour les fichiers tabulaires).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "query_dataframe",
        "description": "Exécute une expression pandas en lecture seule sur un document Excel/CSV de la bibliothèque et retourne le résultat. L'expression a accès à la variable `df` (DataFrame) et `pd`.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nom exact du fichier dans la bibliothèque"},
                "sheet": {"type": "string", "description": "Nom de la feuille Excel (optionnel, sinon la première feuille)"},
                "expression": {"type": "string", "description": "Expression pandas, ex: df.groupby('N° compte général')[['Débit','Crédit']].sum()"},
            },
            "required": ["filename", "expression"],
        },
    },
    {
        "name": "read_document_text",
        "description": "Extrait le texte d'un document PDF de la bibliothèque.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nom exact du fichier PDF dans la bibliothèque"},
            },
            "required": ["filename"],
        },
    },
]


def run_tool(name: str, tool_input: dict) -> str:
    if name == "list_documents":
        return str(backend.list_documents())
    if name == "query_dataframe":
        return backend.query_dataframe(
            filename=tool_input["filename"],
            expression=tool_input["expression"],
            sheet=tool_input.get("sheet"),
        )
    if name == "read_document_text":
        return backend.read_document_text(filename=tool_input["filename"])
    return f"Outil inconnu : {name}"


# --------------------------------------------------------------------------
# Clé API
# --------------------------------------------------------------------------

def get_api_key() -> str | None:
    key = st.session_state.get("api_key")
    if key:
        return key
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")  # type: ignore[union-attr]
        if key:
            return key
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
# État de session
# --------------------------------------------------------------------------

if "conversation_id" not in st.session_state:
    convs = backend.list_conversations()
    if convs:
        st.session_state.conversation_id = convs[0]["id"]
    else:
        st.session_state.conversation_id = backend.create_conversation("Nouvelle conversation")

if "messages" not in st.session_state:
    # Reconstruit un historique simple (texte) à partir de la DB pour la conversation active
    st.session_state.messages = [
        {"role": m["role"], "content": m["content"]}
        for m in backend.get_messages(st.session_state.conversation_id)
    ]

# --------------------------------------------------------------------------
# Barre latérale
# --------------------------------------------------------------------------

with st.sidebar:
    st.title("📊 Assistant AM TRANSIT")

    with st.expander("🔑 Clé API Anthropic", expanded=get_api_key() is None):
        key_input = st.text_input(
            "Clé API (sk-ant-...)",
            type="password",
            value=st.session_state.get("api_key", ""),
            help="Créez une clé gratuite sur console.anthropic.com puis collez-la ici.",
        )
        if key_input:
            st.session_state.api_key = key_input
        model_input = st.text_input(
            "Modèle",
            value=st.session_state.get("model", DEFAULT_MODEL),
            help="Identifiant du modèle Claude. Voir docs.claude.com/en/docs/about-claude/models pour la liste à jour.",
        )
        st.session_state.model = model_input

    st.divider()
    st.subheader("💬 Conversations")

    if st.button("➕ Nouvelle conversation", use_container_width=True):
        st.session_state.conversation_id = backend.create_conversation("Nouvelle conversation")
        st.session_state.messages = []
        st.rerun()

    convs = backend.list_conversations()
    for conv in convs:
        label = conv["title"] or "Sans titre"
        is_active = conv["id"] == st.session_state.conversation_id
        cols = st.columns([5, 1])
        if cols[0].button(("➡️ " if is_active else "") + label, key=f"conv_{conv['id']}", use_container_width=True):
            st.session_state.conversation_id = conv["id"]
            st.session_state.messages = [
                {"role": m["role"], "content": m["content"]}
                for m in backend.get_messages(conv["id"])
            ]
            st.rerun()
        if cols[1].button("🗑️", key=f"del_{conv['id']}"):
            backend.delete_conversation(conv["id"])
            if conv["id"] == st.session_state.conversation_id:
                remaining = backend.list_conversations()
                if remaining:
                    st.session_state.conversation_id = remaining[0]["id"]
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in backend.get_messages(remaining[0]["id"])
                    ]
                else:
                    st.session_state.conversation_id = backend.create_conversation("Nouvelle conversation")
                    st.session_state.messages = []
            st.rerun()

    st.divider()
    st.subheader("📁 Bibliothèque de documents")
    st.caption("Ces documents restent disponibles pour toutes vos conversations (grand livre, balances, budgets, factures, PDF...).")

    uploaded_files = st.file_uploader(
        "Ajouter des documents",
        type=["xlsx", "xls", "csv", "pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for f in uploaded_files:
            try:
                backend.save_uploaded_file(f.name, f.getvalue())
            except ValueError as exc:
                st.error(str(exc))
        st.success(f"{len(uploaded_files)} document(s) ajouté(s) à la bibliothèque.")

    docs = backend.list_documents()
    if not docs:
        st.info("Aucun document dans la bibliothèque pour l'instant.")
    else:
        for doc in docs:
            cols = st.columns([5, 1])
            cols[0].write(f"📄 {doc['filename']} ({doc['size_kb']} Ko)")
            if cols[1].button("🗑️", key=f"rmdoc_{doc['filename']}"):
                backend.remove_document(doc["filename"])
                st.rerun()

    st.divider()
    st.subheader("⬇️ Export de la conversation")
    exp_cols = st.columns(2)
    if exp_cols[0].button("Excel", use_container_width=True):
        with tempfile.TemporaryDirectory() as tmp:
            path = backend.export_conversation_xlsx(st.session_state.conversation_id, Path(tmp) / "conversation.xlsx")
            st.download_button(
                "Télécharger le .xlsx",
                data=path.read_bytes(),
                file_name="conversation_am_transit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    if exp_cols[1].button("PDF", use_container_width=True):
        with tempfile.TemporaryDirectory() as tmp:
            path = backend.export_conversation_pdf(st.session_state.conversation_id, Path(tmp) / "conversation.pdf")
            st.download_button(
                "Télécharger le .pdf",
                data=path.read_bytes(),
                file_name="conversation_am_transit.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# --------------------------------------------------------------------------
# Zone de chat principale
# --------------------------------------------------------------------------

st.header("Assistant de contrôle de gestion")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Posez votre question (ex: Quel est le solde du compte 401110 ?)")

if user_prompt:
    api_key = get_api_key()
    if not api_key:
        st.error("Veuillez d'abord renseigner votre clé API Anthropic dans la barre latérale.")
        st.stop()

    try:
        import anthropic
    except ImportError:
        st.error("Le package `anthropic` n'est pas installé. Ajoutez-le à requirements.txt.")
        st.stop()

    client = anthropic.Anthropic(api_key=api_key)

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    backend.add_message(st.session_state.conversation_id, "user", user_prompt)
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Historique envoyé à Claude pour cette conversation (texte simple ; le tool-use se fait
    # dans une boucle locale ci-dessous et n'est pas repersisté bloc par bloc).
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_Réflexion en cours..._")

        final_text = ""
        try:
            for _ in range(8):  # limite d'itérations d'appels d'outils
                response = client.messages.create(
                    model=st.session_state.get("model", DEFAULT_MODEL),
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=api_messages,
                )

                if response.stop_reason != "tool_use":
                    final_text = "".join(
                        block.text for block in response.content if block.type == "text"
                    )
                    break

                # Ajoute le tour de l'assistant (avec les tool_use) à l'historique local
                api_messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result_text = run_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text,
                            }
                        )
                api_messages.append({"role": "user", "content": tool_results})
            else:
                final_text = "Désolé, je n'ai pas pu terminer cette demande (trop d'étapes)."

        except Exception as exc:  # noqa: BLE001
            final_text = f"Erreur lors de l'appel à l'API Claude : {exc}"

        placeholder.markdown(final_text)

    st.session_state.messages.append({"role": "assistant", "content": final_text})
    backend.add_message(st.session_state.conversation_id, "assistant", final_text)

    # Titre automatique de la conversation à partir de la première question
    convs = backend.list_conversations()
    current = next((c for c in convs if c["id"] == st.session_state.conversation_id), None)
    if current and current["title"] == "Nouvelle conversation":
        backend.rename_conversation(st.session_state.conversation_id, user_prompt[:60])
