import streamlit as st
from app import SYSTEM_PROMPT, ask_agent

st.title("AI Kundenservice")
st.caption("KI-gestützter Shopware Kundenservice")

st.set_page_config(page_title="AI Kundenservice", page_icon="💬", layout="centered")
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

        message = ask_agent(user_message, st.session_state.messages)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": message.content}
        )

        with st.chat_message("assistant"):
            st.write(message.content or "Tool-Aufruf erkannt")

if st.button("Neue Unterhaltung"):
    st.session_state.chat_history = []
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()
