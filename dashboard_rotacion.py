import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="People Analytics Hub")

@st.cache_data(ttl=600)
def load_consolidado():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    res = supabase.table("consolidado").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Procesamiento rápido
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Renunció' if pd.notna(x) else 'Activo')
    df['MonthlyIncome'] = pd.to_numeric(df['MonthlyIncome'], errors='coerce')
    return df

def render_rotacion_dashboard():
    df_raw = load_consolidado()

    st.title("🚀 Inteligencia de Datos: Análisis de Rotación")
    
    # --- FILTROS EN LA PARTE SUPERIOR ---
    with st.container():
        f1, f2, f3 = st.columns(3)
        with f1:
            genero = st.selectbox("Género:", ['Todos'] + sorted(df_raw['Gender'].unique().tolist()))
        with f2:
            contrato = st.selectbox("Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))
        with f3:
            depto = st.selectbox("Departamento:", ['Todos'] + sorted(df_raw['Department'].unique().tolist()))

    # Aplicar Filtros
    df = df_raw.copy()
    if genero != 'Todos': df = df[df['Gender'] == genero]
    if contrato != 'Todos': df = df[df['Tipocontrato'] == contrato]
    if depto != 'Todos': df = df[df['Department'] == depto]

    st.markdown("---")

    # --- MÉTRICAS CLAVE (KPIs) ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Headcount", len(df))
    m2.metric("Bajas", len(df[df['Estado'] == 'Renunció']))
    m3.metric("Tasa Fuga", f"{(len(df[df['Estado'] == 'Renunció'])/len(df)*100):.1f}%" if len(df)>0 else "0%")
    m4.metric("Ingreso Prom.", f"${df['MonthlyIncome'].mean():,.0f}")

    # --- FILA 1: DISPERSIÓN Y SATISFACCIÓN ---
    st.markdown("### 🔍 Factores Determinantes de Salida")
    c1, c2 = st.columns([2, 1])

    with c1:
        # Gráfico de Dispersión más limpio
        st.write("**Relación Edad vs Salario (Estado de Empleado)**")
        fig_scat = px.scatter(
            df, x='Age', y='MonthlyIncome', color='Estado',
            hover_data=['JobRole', 'YearsAtCompany'],
            color_discrete_map={'Renunció': '#EF5350', 'Activo': '#26A69A'},
            opacity=0.6, height=450,
            labels={'Age': 'Edad', 'MonthlyIncome': 'Sueldo ($)'}
        )
        st.plotly_chart(fig_scat, use_container_width=True)

    with c2:
        # Gráfico de Barras: Satisfacción Laboral vs Salidas
        st.write("**Fugas por Nivel de Satisfacción**")
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Bajas')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Bajas', color='Bajas', 
                         color_continuous_scale='Reds', labels={'JobSatisfaction': 'Nivel de Satisfacción (1-4)'})
        st.plotly_chart(fig_sat, use_container_width=True)

    # --- FILA 2: DEPARTAMENTO Y OVERTIME ---
    st.markdown("---")
    st.markdown("### 🏢 Análisis Organizacional")
    c3, c4 = st.columns(2)

    with c3:
        # Porcentaje de Fuga por Departamento
        st.write("**Tasa de Deserción por Área**")
        dept_churn = df.groupby('Department')['Estado'].value_counts(normalize=True).unstack().fillna(0)
        if 'Renunció' in dept_churn.columns:
            fig_dept = px.bar(dept_churn, x=dept_churn.index, y='Renunció', 
                              title="Probabilidad de Fuga por Departamento",
                              labels={'Renunció': '% Fuga'}, color_discrete_sequence=['#FF7043'])
            fig_dept.update_layout(yaxis_tickformat='.0%')
            st.plotly_chart(fig_dept, use_container_width=True)

    with c4:
        # Impacto de Horas Extra
        st.write("**Impacto de Horas Extra (OverTime)**")
        fig_over = px.pie(df[df['Estado'] == 'Renunció'], names='OverTime', 
                          title="¿Hacían horas extra los que se fueron?",
                          color_discrete_sequence=['#D32F2F', '#90CAF9'])
        st.plotly_chart(fig_over, use_container_width=True)

    # --- FILA 3: ANTIGÜEDAD ---
    st.markdown("---")
    st.subheader("⏳ Permanencia en la Compañía")
    fig_hist = px.histogram(df, x="YearsAtCompany", color="Estado", barmode="overlay",
                           title="Distribución de Años en la Empresa (Activos vs Bajas)",
                           color_discrete_map={'Renunció': '#EF5350', 'Activo': '#26A69A'},
                           labels={'YearsAtCompany': 'Años'})
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- CONCLUSIÓN ---
    st.info(f"💡 **Interpretación:** En el filtro de **{contrato}**, el departamento de **{df[df['Estado'] == 'Renunció']['Department'].mode()[0] if not df[df['Estado'] == 'Renunció'].empty else 'N/A'}** muestra la mayor vulnerabilidad.")

if __name__ == "__main__":
    render_rotacion_dashboard()