"""Notion AI Personal Assistant — Streamlit Application"""

import streamlit as st
import uuid
from config import config
from core.agent import NotionAgent
from core.llm_factory import LLMFactory
from utils.storage import ConversationStorage

# ── Page config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Notion AI Assistant",
    page_icon="🤖",
    layout="wide",
)

# ── Session state init ───────────────────────────────────────────────

if "storage" not in st.session_state:
    st.session_state.storage = ConversationStorage()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Settings")

    # LLM provider selection
    available_providers = LLMFactory.list_available_providers()
    enabled_providers = [p for p, ok in available_providers.items() if ok]

    if not enabled_providers:
        st.error("No LLM provider configured. Add an API key to `.env`.")
        st.stop()

    selected_provider = st.selectbox(
        "LLM Provider",
        options=enabled_providers,
        index=0,
    )

    # Model selection
    model_options = {
        "openai": ["gpt-5-nano", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini"],
        "gemini": ["gemini-2.0-flash", "gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"],
        "claude": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
    }

    selected_model = st.selectbox(
        "Model",
        options=model_options.get(selected_provider, []),
    )

    # Temperature
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)

    # API Keys (override .env values in session)
    with st.expander("🔑 API Keys"):
        notion_key = st.text_input(
            "Notion API Key",
            type="password",
            value=config.notion_api_key or "",
        )

        if selected_provider == "openai":
            st.text_input(
                "OpenAI API Key",
                type="password",
                value=config.openai_api_key or "",
                key="openai_key_input",
            )
        elif selected_provider == "gemini":
            st.text_input(
                "Google API Key",
                type="password",
                value=config.google_api_key or "",
                key="google_key_input",
            )
        elif selected_provider == "claude":
            st.text_input(
                "Anthropic API Key",
                type="password",
                value=config.anthropic_api_key or "",
                key="anthropic_key_input",
            )

    st.divider()

    # ── Database management ──────────────────────────────────────────
    st.subheader("📊 Databases")

    if st.button("🔄 Refresh Databases"):
        with st.spinner("Discovering databases…"):
            if "agent" in st.session_state:
                databases = st.session_state.agent.notion_mcp.refresh_databases()
                st.success(f"Found {len(databases)} databases")

    if "agent" in st.session_state:
        available_dbs = st.session_state.agent.notion_mcp.list_available_databases()
        if available_dbs:
            with st.expander(f"Available Databases ({len(available_dbs)})"):
                for db in available_dbs:
                    st.text(f"• {db}")
        else:
            st.info("No databases found. Click Refresh.")

    st.divider()

    # ── Session controls ─────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            if "agent" in st.session_state:
                st.session_state.agent.clear_memory()
            st.rerun()
    with col2:
        if st.button("🆕 New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            if "agent" in st.session_state:
                st.session_state.agent.clear_memory()
            st.rerun()

# ── Main content ─────────────────────────────────────────────────────

st.title("🤖 Notion AI Personal Assistant")
st.caption("Chat with your Notion workspace using natural language")

# ── Initialize agent ─────────────────────────────────────────────────

needs_init = (
    "agent" not in st.session_state
    or st.session_state.get("current_provider") != selected_provider
    or st.session_state.get("current_model") != selected_model
)

if needs_init:
    try:
        with st.spinner("Initializing agent…"):
            st.session_state.agent = NotionAgent(
                llm_provider=selected_provider,
                llm_model=selected_model,
                temperature=temperature,
                notion_api_key=notion_key if notion_key else None,
            )
            st.session_state.current_provider = selected_provider
            st.session_state.current_model = selected_model
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# ── Display chat messages ────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat input ───────────────────────────────────────────────────────

if prompt := st.chat_input("Ask me anything about your Notion workspace…"):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Save to storage
    st.session_state.storage.save_conversation(
        st.session_state.session_id,
        {"role": "user", "content": prompt},
    )

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            response = st.session_state.agent.chat(prompt)
            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.storage.save_conversation(
        st.session_state.session_id,
        {"role": "assistant", "content": response},
    )

# ── Footer ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("*Privacy-first AI assistant — all data processed locally*")
