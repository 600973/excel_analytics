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
if 'filter_reset_counter' not in st.session_state:
    st.session_state.filter_reset_counter = 0

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
        
        # Инициализация
        if 'filters' not in st.session_state:
            st.session_state.filters = {}
        if 'show_filters' not in st.session_state:
            st.session_state.show_filters = False
        
        # Кнопка показать/скрыть фильтры
        show_filters = st.checkbox("🔍 Показать фильтры", value=st.session_state.show_filters)
        st.session_state.show_filters = show_filters
        
        if show_filters:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader("📄 Фильтры")
                
                for col in df.columns:
                    # Проверяем, применён ли фильтр (единая логика для всех типов)
                    col_dtype = str(df[col].dtype)
                    is_date = 'datetime' in col_dtype or 'Дата' in col
                    
                    # Получаем текущий фильтр
                    current_filter = st.session_state.filters.get(col, [])
                    is_filtered = bool(current_filter)
                    
                    # Строка с названием и кнопкой сброса
                    exp_col, btn_col = st.columns([5, 1])
                    
                    with exp_col:
                        # Название фильтра с индикатором
                        expander_label = f"🔴 {col}" if is_filtered else col
                        expander_open = st.expander(expander_label)
                    
                    with btn_col:
                        # Кнопка сброса на той же строке
                        if is_filtered:
                            if st.button("❌", key=f"clear_{col}", use_container_width=True):
                                st.session_state.filters[col] = []
                                st.session_state.filter_reset_counter += 1
                                st.rerun()
                    
                    with expander_open:
                        # Используем уже определённые переменные col_dtype и is_date
                        
                        if is_date:
                            # Календарь для дат
                            st.caption("📅 Выберите диапазон дат")
                            
                            min_date = pd.to_datetime(df[col].dropna().min(), dayfirst=True, errors='coerce')
                            max_date = pd.to_datetime(df[col].dropna().max(), dayfirst=True, errors='coerce')
                            
                            # Значение по умолчанию: пустое (None) или из фильтра
                            default_value = ()
                            if current_filter and len(current_filter) == 2:
                                default_value = tuple(current_filter)
                            
                            # date_input с уникальным ключом, который меняется при сбросе
                            date_range = st.date_input(
                                "Период:",
                                value=default_value,
                                min_value=min_date,
                                max_value=max_date,
                                key=f"date_{col}_{st.session_state.filter_reset_counter}"
                            )
                            
                            # Сохраняем диапазон дат ТОЛЬКО если выбрано 2 даты
                            if len(date_range) == 2:
                                new_range = list(date_range)
                                if new_range != st.session_state.filters.get(col, []):
                                    st.session_state.filters[col] = new_range
                                    st.rerun()
                            elif len(date_range) == 0 and current_filter:
                                # Если очистили даты - сбрасываем фильтр
                                st.session_state.filters[col] = []
                                st.rerun()
                            
                        else:
                            # Обычный multiselect для остальных
                            unique_values = sorted(df[col].dropna().unique().tolist())
                            
                            # Кнопки выбрать/снять всё
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("✅ Всё", key=f"all_{col}", use_container_width=True):
                                    st.session_state.filters[col] = unique_values
                                    st.rerun()
                            with col_btn2:
                                if st.button("❌ Снять", key=f"none_{col}", use_container_width=True):
                                    st.session_state.filters[col] = []
                                    st.session_state.filter_reset_counter += 1
                                    st.rerun()
                            
                            # Поиск
                            search = st.text_input("🔍 Поиск:", key=f"search_{col}", placeholder="Введите для поиска...")
                            
                            # Фильтруем значения по поиску
                            if search:
                                filtered_values = [v for v in unique_values if search.lower() in str(v).lower()]
                            else:
                                filtered_values = unique_values
                            
                            # Multiselect с уникальным ключом, который меняется при сбросе
                            selected_values = st.multiselect(
                                f"Значения ({len(filtered_values)}):",
                                options=filtered_values,
                                default=[v for v in st.session_state.filters.get(col, []) if v in filtered_values],
                                key=f"filter_{col}_{st.session_state.filter_reset_counter}"
                            )
                            
                            # Обновляем фильтр ТОЛЬКО если изменилось
                            if selected_values != st.session_state.filters.get(col, []):
                                st.session_state.filters[col] = selected_values
                                st.rerun()
                
                if st.button("🔄 Сбросить все фильтры", use_container_width=True, type="primary"):
                    # Очищаем все фильтры
                    for col in df.columns:
                        st.session_state.filters[col] = []
                    st.session_state.filter_reset_counter += 1
                    st.rerun()
        
        # Применение фильтров (после обновления)
        df_filtered = df.copy()
        for col, values in st.session_state.filters.items():
            if values and col in df_filtered.columns:
                # Проверяем тип фильтра
                col_dtype = str(df[col].dtype)
                is_date = 'datetime' in col_dtype or 'Дата' in col
                
                if is_date and len(values) == 2:
                    # Фильтр по диапазону дат
                    start_date, end_date = values
                    df_filtered = df_filtered[
                        (pd.to_datetime(df_filtered[col], dayfirst=True, errors='coerce') >= pd.Timestamp(start_date)) &
                        (pd.to_datetime(df_filtered[col], dayfirst=True, errors='coerce') <= pd.Timestamp(end_date))
                    ]
                else:
                    # Обычный фильтр по значениям
                    df_filtered = df_filtered[df_filtered[col].isin(values)]
        
        if show_filters:
            with col2:
                if len(df_filtered) < len(df):
                    st.info(f"📊 {len(df_filtered)} из {len(df)} строк")
                
                st.subheader("📝 Код")
                formula = st.text_area("Python:", value="# df - датасет\nresult = df['Столбец'].sum()", height=300)
                
                if st.button("▶️ Выполнить", type="primary"):
                    try:
                        import matplotlib.pyplot as plt
                        import plotly.express as px
                        import plotly.graph_objects as go
                        
                        exec(formula, {'df': df_filtered.copy(), 'pd': pd, 'np': np, 'plt': plt, 'px': px, 'go': go, 'st': st})
                        
                        if 'result' in locals():
                            st.success("✅ Готово")
                            result = locals()['result']
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
                st.dataframe(df_filtered, use_container_width=True)
        else:
            if len(df_filtered) < len(df):
                st.info(f"📊 {len(df_filtered)} из {len(df)} строк")
            
            st.subheader("📝 Код")
            formula = st.text_area("Python:", value="# df - датасет\nresult = df['Столбец'].sum()", height=300)
            
            if st.button("▶️ Выполнить", type="primary"):
                try:
                    import matplotlib.pyplot as plt
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    local_vars = {'df': df_filtered.copy(), 'pd': pd, 'np': np, 'plt': plt, 'px': px, 'go': go, 'st': st}
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
            st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("📂 Загрузите файлы")

with tab3:
    show_chat()

with tab4:
    st.header("Настройки")