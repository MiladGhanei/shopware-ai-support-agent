import streamlit as st
from app import SYSTEM_PROMPT, ask_agent
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Kundenservice", page_icon="💬", layout="centered")

st.title("AI Kundenservice")
st.caption("KI-gestützter Shopware Kundenservice")

with st.sidebar:
    st.header("Settings")

    st.caption(
        "Configure the LLM and Shopware connection. "
        "Values from your local .env file are loaded automatically."
    )

    with st.form("settings_form"):
        openrouter_api_key = st.text_input(
            "OpenRouter API Key",
            value=os.getenv("OPENROUTER_API_KEY", ""),
            type="password",
        )

        shopware_url = st.text_input(
            "Shopware URL",
            value=os.getenv("SHOPWARE_URL", ""),
            placeholder="https://shop.example.com",
        )

        shopware_access_id = st.text_input(
            "Shopware Access ID",
            value=os.getenv("SHOPWARE_ACCESS_ID", ""),
            type="password",
        )

        shopware_secret = st.text_input(
            "Shopware Secret Access Key",
            value=os.getenv("SHOPWARE_SECRET_ACCESS_KEY", ""),
            type="password",
        )

        apply_settings = st.form_submit_button(
            "Apply Settings", use_container_width=True
        )

    if apply_settings:
        st.session_state["settings"] = {
            "openrouter_api_key": openrouter_api_key,
            "shopware_url": shopware_url,
            "shopware_access_id": shopware_access_id,
            "shopware_secret": shopware_secret,
        }

    st.divider()

    if all([openrouter_api_key, shopware_url, shopware_access_id, shopware_secret]):
        st.success("Configuration ready")
    else:
        st.warning("Please complete the configuration above.")

settings = st.session_state.get(
    "settings",
    {
        "openrouter_api_key": openrouter_api_key,
        "shopware_url": shopware_url,
        "shopware_access_id": shopware_access_id,
        "shopware_secret": shopware_secret,
    },
)

st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stMainBlockContainer {
    max-width: 760px;
    padding-top: 3rem;
    }

    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)

user_message = st.chat_input("Nachricht schreiben...")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if not st.session_state.chat_history:
    st.info(
        "👋 Hallo! Ich helfe Ihnen bei Fragen zu Ihrer Bestellung. "
        "Halten Sie bitte Ihre Bestellnummer und die Postleitzahl "
        "Ihrer Lieferadresse bereit."
    )

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for chat_message in st.session_state.chat_history:
    with st.chat_message(chat_message["role"]):
        st.write(chat_message["content"])

if user_message:
    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        with st.chat_message("user"):
            st.write(user_message)

        if not settings["openrouter_api_key"]:
            st.error("Please enter your OpenRouter API key in Settings.")
            st.stop()

        if not settings["shopware_url"]:
            st.error("Please enter your Shopware URL in Settings.")
            st.stop()

        if not settings["shopware_access_id"]:
            st.error("Please enter your Shopware Access ID in Settings.")
            st.stop()

        if not settings["shopware_secret"]:
            st.error("Please enter your Shopware Secret Access Key in Settings.")
            st.stop()

        message = ask_agent(
            user_message,
            st.session_state.messages,
            settings["openrouter_api_key"],
            settings["shopware_url"],
            settings["shopware_access_id"],
            settings["shopware_secret"],
        )

        if isinstance(message, dict) and message.get("error") == "llm_rate_limit":
            st.error(
                "The AI service has reached its current request limit. "
                "Please try again later."
            )
            st.stop()

        st.session_state.chat_history.append(
            {"role": "assistant", "content": message.content}
        )

        with st.chat_message("assistant"):
            st.write(message.content or "Tool-Aufruf erkannt")

if st.button("Neue Unterhaltung"):
    st.session_state.chat_history = []
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()
