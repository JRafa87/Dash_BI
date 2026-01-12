import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import date

# ==============================================================================
# 1. CARGA Y PROCESAMIENTO
# ==============================================================================

@st.cache_data(ttl=3600)
def load_data_bi():
    # Conexión directa a Supabase (usando tus secretos)
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    response = supabase.table("consolidado").select("*").execute()
    df = pd.DataFrame(response.data)
    
    # Procesamiento
    df['FechaIngreso'] = pd.to_datetime(df['FechaIngreso'], errors='coerce')
    df['FechaSalida'] = pd.to_datetime(df['FechaSalida'], errors='coerce')
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Fuga' if pd.notna(x) else 'Activo')
    
    return df

def render_rotacion_dashboard():
    df_raw = load_data_bi()
    
    # --- FILTROS (Mantenemos tus originales) ---
    st.sidebar.header("🔍 Filtros de Visualización")
    
    genero_list = ['Todos'] + sorted(df_raw['Gender'].unique().tolist())
    genero_sel = st.sidebar.selectbox("Filtrar por Género:", genero_list)
    
    contrato_list = ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist())
    contrato_sel = st.sidebar.selectbox("Filtrar por Tipo de Contrato:", contrato_list)

    # Aplicar Filtros
    df = df_raw.copy()
    if genero_sel != 'Todos': df = df[df['Gender'] == genero_sel]
    if contrato_sel != 'Todos': df = df[df['Tipocontrato'] == contrato_sel]

    # --- MÉTRICAS PRINCIPALES ---
    st.title("🚀 People Analytics Strategy")
    st.markdown(f"Análisis filtrado por: **{genero_sel}** | **{contrato_sel}**")
    
    k1, k2, k3, k4 = st.columns(4)
    total = len(df)
    bajas = len(df[df['Estado'] == 'Fuga'])
    k1.metric("Headcount", total)
    k2.metric("Bajas", bajas)
    k3.metric("Tasa Fuga", f"{(bajas/total*100):.1f}%" if total > 0 else "0%")
    k4.metric("Sueldo Prom.", f"${df['MonthlyIncome'].mean():,.0f}")

    st.markdown("---")

    # --- EL GRÁFICO DE DISPERSIÓN (TU REQUISITO) ---
    st.subheader("🎯 Mapa de Talento: Edad vs Ingreso")
    
    # Lo mantenemos y lo hacemos interactivo
    fig_scat = px.scatter(
        df, 
        x='Age', 
        y='MonthlyIncome', 
        color='Estado',
        size='TotalWorkingYears',    # El tamaño indica los años de experiencia total
        symbol='OverTime',           # El símbolo indica si hace horas extra (Yes=Círculo, No=X)
        hover_name='JobRole', 
        color_discrete_map={'Fuga': '#EF5350', 'Activo': '#2ECC71'},
        labels={'Age': 'Edad del Colaborador', 'MonthlyIncome': 'Ingreso Mensual ($)'},
        template="plotly_white",
        height=600
    )
    
    # Mejoramos el diseño del gráfico de dispersión
    fig_scat.update_layout(
        legend_title_text='Estatus',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='LightGray')
    )
    st.plotly_chart(fig_scat, use_container_width=True)

    # --- SECCIÓN WAO: COMPARATIVA DE SATISFACCIÓN ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🏢 Fuga por Departamento")
        df_dept = df[df['Estado'] == 'Fuga']['Department'].value_counts().reset_index()
        fig_dept = px.bar(df_dept, x='count', y='Department', orientation='h', 
                          color='count', color_continuous_scale='Reds')
        st.plotly_chart(fig_dept, use_container_width=True)

    with c2:
        st.subheader("🎭 Perfil de Satisfacción (Fugas)")
        # Gráfico radial para ver qué sienten los que se van
        if not df[df['Estado'] == 'Fuga'].empty:
            df_f = df[df['Estado'] == 'Fuga']
            radar_data = pd.DataFrame(dict(
                r=[df_f['JobSatisfaction'].mean(), df_f['EnvironmentSatisfaction'].mean(), 
                   df_f['RelationshipSatisfaction'].mean(), df_f['WorkLifeBalance'].mean()],
                theta=['Trabajo', 'Entorno', 'Relaciones', 'Balance Vida']
            ))
            fig_radar = px.line_polar(radar_data, r='r', theta='theta', line_close=True, range_r=[0,4])
            fig_radar.update_traces(fill='toself', line_color='#EF5350')
            st.plotly_chart(fig_radar, use_container_width=True)

    # --- INSIGHTS AUTOMÁTICOS ---
    st.success(f"**Insight Estratégico:** Bajo el contrato **{contrato_sel}**, el principal motivo de fuga detectado es un nivel de satisfacción de **{df[df['Estado'] == 'Fuga']['JobSatisfaction'].mean():.1f}/4.0**.")

if __name__ == "__main__":
    render_rotacion_dashboard()