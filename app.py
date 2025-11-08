# PROJECT_ROOT: app.py
import streamlit as st
import pandas as pd
import numpy as np
from modules.chat import show_chat

st.set_page_config(page_title="Чат Аналитика", layout="wide")

# Инициализация хранилища данных
if 'datasets' not in st.session_state:
    st.session_state.datasets = {}
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}

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
                        if name in st.session_state.column_types:
                            del st.session_state.column_types[name]
                        st.rerun()
                
                # Настройка типов данных
                if name not in st.session_state.column_types:
                    st.session_state.column_types[name] = {}
                    for col_name in df.columns:
                        current_type = str(df[col_name].dtype)
                        if 'object' in current_type:
                            st.session_state.column_types[name][col_name] = 'string'
                        elif 'int' in current_type:
                            st.session_state.column_types[name][col_name] = 'integer'
                        elif 'float' in current_type:
                            st.session_state.column_types[name][col_name] = 'float'
                        else:
                            st.session_state.column_types[name][col_name] = 'string'
                
                # HTML стиль для выпадающих списков над таблицей
                st.markdown("""
                <style>
                    .type-selector-container {
                        display: flex;
                        gap: 10px;
                        overflow-x: auto;
                        margin-bottom: 5px;
                    }
                    .type-selector {
                        min-width: 150px;
                        flex-shrink: 0;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Создаём выпадающие списки, которые прокручиваются вместе
                type_cols = st.columns(len(df.columns))
                for idx, col_name in enumerate(df.columns):
                    with type_cols[idx]:
                        selected_type = st.selectbox(
                            f"📋 {col_name[:15]}...",
                            options=['string', 'integer', 'float', 'datetime', 'boolean'],
                            index=['string', 'integer', 'float', 'datetime', 'boolean'].index(
                                st.session_state.column_types[name].get(col_name, 'string')
                            ),
                            key=f"type_{name}_{col_name}",
                            label_visibility="visible"
                        )
                        st.session_state.column_types[name][col_name] = selected_type
                
                # Таблица с данными
                st.dataframe(df.head(10), use_container_width=True)

with tab2:
    st.header("Аналитика")
    
    if len(st.session_state.datasets) > 0:
        # Выбор датасета
        selected_dataset = st.selectbox(
            "Выберите датасет:",
            options=list(st.session_state.datasets.keys())
        )
        
        df = st.session_state.datasets[selected_dataset]
        
        # Редактор формул
        st.subheader("📝 Код")
        
        formula = st.text_area(
            "Python:",
            value="# df - ваш датасет\nresult = df['Столбец'].sum()",
            height=300
        )
        
        if st.button("▶️ Выполнить", type="primary"):
            try:
                import matplotlib.pyplot as plt
                import plotly.express as px
                import plotly.graph_objects as go
                
                local_vars = {
                    'df': df.copy(),
                    'pd': pd,
                    'np': np,
                    'plt': plt,
                    'px': px,
                    'go': go,
                    'st': st
                }
                
                exec(formula, local_vars)
                
                if 'result' in local_vars:
                    st.success("✅ Готово")
                    result = local_vars['result']
                    
                    if isinstance(result, (int, float)):
                        st.metric("Результат", f"{result:,.2f}")
                    elif isinstance(result, pd.DataFrame):
                        st.dataframe(result, use_container_width=True)
                    elif isinstance(result, pd.Series):
                        st.dataframe(result.to_frame(), use_container_width=True)
                    else:
                        st.write(result)
                
            except Exception as e:
                st.error(f"❌ {e}")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📂 Загрузите файлы")

with tab3:
    show_chat()

with tab4:
    st.header("Настройки")