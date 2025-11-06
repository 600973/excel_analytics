import streamlit as st
import pandas as pd
from modules.chat import show_chat

st.set_page_config(page_title="Чат Аналитика", layout="wide")

tab1, tab2, tab3 = st.tabs(["Аналитика", "Чат", "Настройки"])

with tab1:
    st.header("Аналитика")
    
    # Загрузка файла
    uploaded_file = st.file_uploader("📊 Загрузите Excel файл", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Чтение данных
        df = pd.read_excel(uploaded_file)
        
        # Показываем базовую информацию
        st.subheader("Данные")
        st.dataframe(df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Строк", len(df))
        with col2:
            st.metric("Столбцов", len(df.columns))
        with col3:
            st.metric("Заполненность", f"{df.notna().sum().sum() / (len(df) * len(df.columns)) * 100:.1f}%")
        
        # Статистика
        st.subheader("Статистика")
        st.dataframe(df.describe(), use_container_width=True)

with tab2:
    show_chat()

with tab3:
    st.header("Настройки")