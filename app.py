import streamlit as st
import pandas as pd
from modules.chat import show_chat

st.set_page_config(page_title="Чат Аналитика", layout="wide")

# Инициализация хранилища данных
if 'datasets' not in st.session_state:
    st.session_state.datasets = {}

tab1, tab2, tab3, tab4 = st.tabs(["Данные", "Аналитика", "Чат", "Настройки"])

with tab1:
    st.header("Данные")
    
    # Загрузка файлов
    uploaded_files = st.file_uploader(
        "📊 Загрузите Excel файлы", 
        type=['xlsx', 'xls'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.datasets:
                df = pd.read_excel(file)
                st.session_state.datasets[file.name] = df
        
        st.success(f"✅ Загружено файлов: {len(st.session_state.datasets)}")
    
    # Показываем загруженные датасеты
    if st.session_state.datasets:
        st.subheader("📂 Загруженные датасеты")
        
        for name, df in st.session_state.datasets.items():
            with st.expander(f"📄 {name}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Строк", len(df))
                with col2:
                    st.metric("Столбцов", len(df.columns))
                with col3:
                    if st.button("❌ Удалить", key=f"del_{name}"):
                        del st.session_state.datasets[name]
                        st.rerun()
                
                st.dataframe(df.head(10), use_container_width=True)

with tab2:
    st.header("Аналитика")
    
    if len(st.session_state.datasets) > 0:
        # Выбор датасета
        selected_dataset = st.selectbox(
            "Выберите датасет для анализа:",
            options=list(st.session_state.datasets.keys())
        )
        
        df = st.session_state.datasets[selected_dataset]
        
        st.subheader(f"Анализ: {selected_dataset}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📂 Загрузите файлы на вкладке 'Данные'")

with tab3:
    show_chat()

with tab4:
    st.header("Настройки")