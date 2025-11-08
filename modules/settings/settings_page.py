# PROJECT_ROOT: modules/settings/settings_page.py
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


def show_settings():
    st.title("Настройки")

    # Инициализация настроек
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "model": None,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 128,
            "repeat_penalty": 1.1
        }

    st.subheader("Модель")

    # Получить список моделей
    models = get_ollama_models()
    if not models:
        st.error("Не удалось получить список моделей. Проверьте, что Ollama запущена на http://localhost:11434")
        return

    # Выбор модели
    current_model = st.session_state.settings["model"]
    model_index = models.index(current_model) if current_model in models else 0

    selected_model = st.selectbox(
        "Выберите модель",
        models,
        index=model_index
    )
    st.session_state.settings["model"] = selected_model

    st.divider()
    st.subheader("Параметры модели")

    # Temperature
    st.session_state.settings["temperature"] = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.settings["temperature"],
        step=0.1,
        help="Контролирует случайность ответов. Меньше = более предсказуемо"
    )

    # Top P
    st.session_state.settings["top_p"] = st.slider(
        "Top P",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.settings["top_p"],
        step=0.1,
        help="Nucleus sampling - рассматривает токены с суммарной вероятностью top_p"
    )

    # Top K
    st.session_state.settings["top_k"] = st.slider(
        "Top K",
        min_value=1,
        max_value=100,
        value=st.session_state.settings["top_k"],
        help="Рассматривает только top_k наиболее вероятных токенов"
    )

    # Max tokens
    st.session_state.settings["num_predict"] = st.slider(
        "Max tokens",
        min_value=1,
        max_value=2048,
        value=st.session_state.settings["num_predict"],
        help="Максимальное количество токенов в ответе"
    )

    # Repeat penalty
    st.session_state.settings["repeat_penalty"] = st.slider(
        "Repeat penalty",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.settings["repeat_penalty"],
        step=0.1,
        help="Штраф за повторение. Больше = меньше повторов"
    )

    st.divider()

    # Кнопка сброса
    if st.button("Сбросить настройки"):
        st.session_state.settings = {
            "model": models[0] if models else None,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 128,
            "repeat_penalty": 1.1
        }
        st.rerun()

    st.success("✓ Настройки сохранены")