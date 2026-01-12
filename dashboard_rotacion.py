import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="HR Intelligence Dashboard")

@st.cache_data(ttl=600)
def load_consolidado():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    res = supabase.table("consolidado").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Procesamiento y Traducción
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Renunció' if pd.notna(x) else 'Activo')
    df['MonthlyIncome'] = pd.to_numeric(df['MonthlyIncome'], errors='coerce')
    df['Genero'] = df['Gender'].map({'Male': 'Masculino', 'Female': 'Femenino'}).fillna(df['Gender'])
    return df

def render_rotacion_dashboard():
    df_raw = load_consolidado()

    st.title("🚀 Panel Estratégico de Rotación de Personal")
    
    # --- FILTROS SUPERIORES ---
    st.markdown("### 🎛️ Filtros Globales")
    f1, f2 = st.columns(2)
    with f1:
        genero = st.selectbox("Seleccione Género:", ['Todos'] + sorted(df_raw['Genero'].unique().tolist()))
    with f2:
        contrato = st.selectbox("Seleccione Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))

    # Aplicar Filtros
    df = df_raw.copy()
    if genero != 'Todos': df = df[df['Genero'] == genero]
    if contrato != 'Todos': df = df[df['Tipocontrato'] == contrato]

    st.markdown("---")

    # --- TARJETAS DE MÉTRICAS ATRACTIVAS (HTML/CSS) ---
    total = len(df)
    bajas = len(df[df['Estado'] == 'Renunció'])
    tasa = (bajas/total*100) if total > 0 else 0
    ingreso = df['MonthlyIncome'].mean() if not df.empty else 0

    st.markdown(f"""
        <div style="display: flex; justify-content: space-around; gap: 20px; margin-bottom: 30px;">
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 8px solid #007BFF; width: 23%; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #555; margin-bottom: 5px; font-weight: bold;">TOTAL EMPLEADOS</p>
                <h2 style="margin: 0; color: #007BFF;">{total}</h2>
            </div>
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 8px solid #DC3545; width: 23%; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #555; margin-bottom: 5px; font-weight: bold;">TOTAL BAJAS</p>
                <h2 style="margin: 0; color: #DC3545;">{bajas}</h2>
            </div>
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 8px solid #FFC107; width: 23%; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #555; margin-bottom: 5px; font-weight: bold;">TASA DE ROTACIÓN</p>
                <h2 style="margin: 0; color: #FFC107;">{tasa:.1f}%</h2>
            </div>
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 8px solid #28A745; width: 23%; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #555; margin-bottom: 5px; font-weight: bold;">INGRESO PROMEDIO</p>
                <h2 style="margin: 0; color: #28A745;">${ingreso:,.0f}</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- GRÁFICO DE DISPERSIÓN (ANCHO COMPLETO) ---
    st.subheader("🎯 Mapa de Dispersión: Edad vs Salario")
    fig_scat = px.scatter(
        df, x='Age', y='MonthlyIncome', color='Estado',
        hover_data={'Age': True, 'MonthlyIncome': ':$,.0f', 'JobRole': True},
        color_discrete_map={'Renunció': '#DC3545', 'Activo': '#28A745'},
        labels={'Age': 'Edad', 'MonthlyIncome': 'Ingreso Mensual', 'Estado': 'Situación'},
        height=550, template="plotly_white"
    )
    fig_scat.update_traces(marker=dict(size=12, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown("---")

    # --- SEGUNDA FILA: SATISFACCIÓN Y BALANCE VIDA-TRABAJO ---
    st.subheader("📊 Análisis de Clima Laboral en Bajas")
    c1, c2 = st.columns(2)

    with c1:
        st.write("**Bajas por Nivel de Satisfacción Laboral**")
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Cantidad')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Cantidad', color='Cantidad', 
                         color_continuous_scale='Reds', labels={'JobSatisfaction': 'Nivel de Satisfacción (1-4)', 'Cantidad': 'Número de Salidas'})
        st.plotly_chart(fig_sat, use_container_width=True)

    with c2:
        st.write("**Bajas por Equilibrio Vida-Trabajo**")
        df_wb = df[df['Estado'] == 'Renunció'].groupby('WorkLifeBalance').size().reset_index(name='Cantidad')
        fig_wb = px.bar(df_wb, x='WorkLifeBalance', y='Cantidad', color='Cantidad', 
                         color_continuous_scale='Oranges', labels={'WorkLifeBalance': 'Equilibrio Vida-Trabajo (1-4)', 'Cantidad': 'Número de Salidas'})
        st.plotly_chart(fig_wb, use_container_width=True)

    # --- CONCLUSIÓN ---
    st.markdown("---")
    st.info(f"💡 **Interpretación de Datos:** En el segmento de **{contrato}**, los colaboradores con un nivel de satisfacción laboral de **1** representan el mayor foco de atención para RRHH.")

if __name__ == "__main__":
    render_rotacion_dashboard()