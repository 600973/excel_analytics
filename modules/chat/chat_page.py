# PROJECT_ROOT: modules/chat/chat_page.py
import streamlit as st
import requests


def get_ollama_models():
    """Получить список моделей из Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        return []
    except:
        return []


def send_message_to_ollama(model, messages):
    """Отправить сообщение в Ollama с контекстом"""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False}
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        return "Ошибка ответа"
    except Exception as e:
        return f"Ошибка: {str(e)}"


def show_chat():
    st.title("Чат")

    # Инициализация
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Выбор модели
    models = get_ollama_models()
    if not models:
        st.error("Ollama не запущена")
        return

    selected_model = st.selectbox("Модель", models)

    # Отображение сообщений
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Поле ввода
    user_input = st.chat_input("Сообщение...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("..."):
            response = send_message_to_ollama(selected_model, st.session_state.messages)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()