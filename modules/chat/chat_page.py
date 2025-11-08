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


def unload_model(model):
    """Явная выгрузка модели из памяти"""
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "keep_alive": 0}
        )
    except:
        pass  # Игнорируем ошибки выгрузки


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
    if "current_model" not in st.session_state:
        st.session_state.current_model = None

    # Выбор модели
    models = get_ollama_models()
    if not models:
        st.error("Ollama не запущена")
        return

    selected_model = st.selectbox("Модель", models)
    
    # Отслеживание переключения модели
    if st.session_state.current_model and st.session_state.current_model != selected_model:
        # Выгружаем старую модель
        with st.spinner(f"⏳ Выгрузка {st.session_state.current_model}..."):
            unload_model(st.session_state.current_model)
        st.info(f"✅ Модель переключена: {st.session_state.current_model} → {selected_model}")
    
    # Обновляем текущую модель
    st.session_state.current_model = selected_model

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