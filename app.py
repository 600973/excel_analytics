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
            "Выберите датасет для анализа:",
            options=list(st.session_state.datasets.keys())
        )
        
        df = st.session_state.datasets[selected_dataset]
        
        # Редактор формул
        st.subheader("📝 Редактор формул")
        
        # Настройка ширины колонок
        sidebar_width = st.slider("Ширина боковой панели", 1, 5, 2, help="Регулируйте ширину правой панели")
        col1, col2 = st.columns([5-sidebar_width, sidebar_width])
        
        with col1:
            # Область для формулы
            st.write("**Напишите Python код:**")
            
            # Примеры быстрого доступа
            st.caption("Переменная `df` содержит выбранный датасет. Используйте pandas, numpy, matplotlib, plotly.")
            
            formula = st.text_area(
                "Формула:",
                value="# Пример: сумма по столбцу\nresult = df['Код Физ.Лица'].sum()\nprint(f'Сумма: {result}')",
                height=200,
                help="Используйте df для доступа к данным"
            )
            
            # Кнопка выполнения
            if st.button("▶️ Выполнить", type="primary"):
                try:
                    # Создаём безопасное окружение для выполнения
                    import matplotlib.pyplot as plt
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    # Локальное пространство имён
                    local_vars = {
                        'df': df.copy(),
                        'pd': pd,
                        'np': np,
                        'plt': plt,
                        'px': px,
                        'go': go,
                        'st': st
                    }
                    
                    # Выполнение кода
                    exec(formula, local_vars)
                    
                    # Если есть result - показываем
                    if 'result' in local_vars:
                        st.success("✅ Выполнено успешно!")
                        st.write("**Результат:**")
                        
                        result = local_vars['result']
                        
                        # Определяем тип результата
                        if isinstance(result, (int, float)):
                            st.metric("Значение", f"{result:,.2f}")
                        elif isinstance(result, pd.DataFrame):
                            st.dataframe(result, use_container_width=True)
                        elif isinstance(result, pd.Series):
                            st.dataframe(result.to_frame(), use_container_width=True)
                        else:
                            st.write(result)
                    
                except Exception as e:
                    st.error(f"❌ Ошибка выполнения: {e}")
        
        with col2:
            # Список столбцов (сворачиваемый)
            with st.expander("📊 Столбцы датасета", expanded=True):
                st.caption("Кликните чтобы скопировать")
                
                for col in df.columns:
                    col_type = str(df[col].dtype)
                    if st.button(f"📌 {col}", key=f"col_{col}", use_container_width=True):
                        st.code(f"df['{col}']", language="python")
            
            # Быстрые шаблоны (сворачиваемый)
            with st.expander("⚡ Шаблоны", expanded=False):
                templates = {
                    "Сумма": f"result = df['СТОЛБЕЦ'].sum()",
                    "Среднее": f"result = df['СТОЛБЕЦ'].mean()",
                    "Группировка": f"result = df.groupby('СТОЛБЕЦ')['ЗНАЧЕНИЕ'].sum()",
                    "График (линия)": f"fig = px.line(df, x='СТОЛБЕЦ_X', y='СТОЛБЕЦ_Y')\nst.plotly_chart(fig)",
                    "График (столбцы)": f"fig = px.bar(df, x='СТОЛБЕЦ_X', y='СТОЛБЕЦ_Y')\nst.plotly_chart(fig)",
                    "Фильтр": f"result = df[df['СТОЛБЕЦ'] > ЗНАЧЕНИЕ]"
                }
                
                for name, code in templates.items():
                    if st.button(name, key=f"tmpl_{name}", use_container_width=True):
                        st.code(code, language="python")
        
        st.divider()
        
        # Просмотр данных
        st.subheader(f"📋 Данные: {selected_dataset}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📂 Загрузите файлы на вкладке 'Данные'")

with tab3:
    show_chat()

with tab4:
    st.header("Настройки")