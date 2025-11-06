import streamlit as st
import requests
import uuid


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
    if "chats" not in st.session_state:
        st.session_state.chats = {}
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.chats[st.session_state.current_chat_id] = {
            "title": "Новый чат",
            "messages": []
        }

    # Sidebar - список чатов
    with st.sidebar:
        st.subheader("Чаты")

        if st.button("➕ Новый чат", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.current_chat_id = new_id
            st.session_state.chats[new_id] = {"title": "Новый чат", "messages": []}
            st.rerun()

        st.divider()

        for chat_id, chat_data in st.session_state.chats.items():
            if st.button(
                    chat_data["title"],
                    key=chat_id,
                    use_container_width=True,
                    type="primary" if chat_id == st.session_state.current_chat_id else "secondary"
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()

    # Выбор модели
    models = get_ollama_models()
    if not models:
        st.error("Не удалось получить список моделей. Проверьте, что Ollama запущена на http://localhost:11434")
        return

    selected_model = st.selectbox("Модель", models)

    # Текущий чат
    current_chat = st.session_state.chats[st.session_state.current_chat_id]

    # Отображение сообщений
    chat_container = st.container(height=400)
    with chat_container:
        for msg in current_chat["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Поле ввода
    user_input = st.chat_input("Введите сообщение...")

    if user_input:
        # Добавить сообщение пользователя
        current_chat["messages"].append({"role": "user", "content": user_input})

        # Обновить название чата (первое сообщение)
        if current_chat["title"] == "Новый чат":
            current_chat["title"] = user_input[:30] + "..." if len(user_input) > 30 else user_input

        # Получить ответ
        with st.spinner("Думаю..."):
            response = send_message_to_ollama(selected_model, current_chat["messages"])

        # Добавить ответ ассистента
        current_chat["messages"].append({"role": "assistant", "content": response})

        st.rerun()