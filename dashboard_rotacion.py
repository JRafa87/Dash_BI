import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Reporte Ejecutivo de Talento")

@st.cache_data(ttl=600)
def load_consolidado():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    res = supabase.table("consolidado").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Procesamiento y Traducciones
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Renunció' if pd.notna(x) else 'Activo')
    df['MonthlyIncome'] = pd.to_numeric(df['MonthlyIncome'], errors='coerce')
    df['Genero'] = df['Gender'].map({'Male': 'Masculino', 'Female': 'Femenino'}).fillna(df['Gender'])
    df['HorasExtra'] = df['OverTime'].map({'Yes': 'Sí', 'No': 'No'}).fillna(df['OverTime'])
    return df

def render_rotacion_dashboard():
    df_raw = load_consolidado()

    st.title("Análisis Estratégico de Capital Humano")
    st.markdown("_Exploración de los factores que impulsan la retención y rotación de nuestra fuerza laboral._")
    
    # --- FILTROS SUPERIORES ---
    f1, f2 = st.columns(2)
    with f1:
        genero_sel = st.selectbox("Filtro por Género:", ['Todos'] + sorted(df_raw['Genero'].unique().tolist()))
    with f2:
        contrato_sel = st.selectbox("Filtro por Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))

    # Aplicar Filtros
    df = df_raw.copy()
    if genero_sel != 'Todos': df = df[df['Genero'] == genero_sel]
    if contrato_sel != 'Todos': df = df[df['Tipocontrato'] == contrato_sel]

    st.markdown("---")

    # --- KPIs COMPACTOS ---
    total = len(df)
    bajas = len(df[df['Estado'] == 'Renunció'])
    tasa = (bajas/total*100) if total > 0 else 0
    ingreso = df['MonthlyIncome'].mean() if not df.empty else 0

    st.markdown(f"""
        <div style="display: flex; justify-content: space-around; gap: 10px; margin-bottom: 20px;">
            <div style="flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; text-align: center;">
                <span style="font-size: 12px; color: #666; font-weight: bold; display: block;">HEADCOUNT</span>
                <span style="font-size: 24px; color: #333; font-weight: bold;">{total}</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; text-align: center;">
                <span style="font-size: 12px; color: #666; font-weight: bold; display: block;">BAJAS</span>
                <span style="font-size: 24px; color: #dc3545; font-weight: bold;">{bajas}</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; text-align: center;">
                <span style="font-size: 12px; color: #666; font-weight: bold; display: block;">% ROTACIÓN</span>
                <span style="font-size: 24px; color: #333; font-weight: bold;">{tasa:.1f}%</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; text-align: center;">
                <span style="font-size: 12px; color: #666; font-weight: bold; display: block;">SALARIO PROM.</span>
                <span style="font-size: 24px; color: #333; font-weight: bold;">${ingreso:,.0f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- STORYTELLING: EL PERFIL DEL TALENTO ---
    st.markdown("### Mapa de Talento: Edad vs Salario")
    st.caption("Visualice cómo se distribuyen los empleados. Los puntos rojos indican áreas donde la competitividad salarial o la edad pueden estar influyendo en la decisión de salida.")
    fig_scat = px.scatter(
        df, x='Age', y='MonthlyIncome', color='Estado',
        hover_data={'Age': True, 'MonthlyIncome': ':$,.0f', 'JobRole': True},
        color_discrete_map={'Renunció': '#EF5350', 'Activo': '#26A69A'},
        labels={'Age': 'Edad', 'MonthlyIncome': 'Sueldo Mensual', 'Estado': 'Estado'},
        height=450, template="plotly_white"
    )
    fig_scat.update_layout(showlegend=True)
    st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown("---")

    # --- STORYTELLING: MOTIVACIÓN Y BALANCE ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Fugas por Nivel de Satisfacción")
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Bajas')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Bajas', color_discrete_sequence=['#EF5350'])
        fig_sat.update_layout(coloraxis_showscale=False) # Quita la barra de color lateral
        st.plotly_chart(fig_sat, use_container_width=True)

    with col2:
        st.markdown("### Fugas por Equilibrio Vida-Trabajo")
        df_wb = df[df['Estado'] == 'Renunció'].groupby('WorkLifeBalance').size().reset_index(name='Bajas')
        fig_wb = px.bar(df_wb, x='WorkLifeBalance', y='Bajas', color_discrete_sequence=['#FFB74D'])
        fig_wb.update_layout(coloraxis_showscale=False) # Quita la barra de color lateral
        st.plotly_chart(fig_wb, use_container_width=True)

    st.markdown("---")

    # --- STORYTELLING: ESTRUCTURA Y CARGA ---
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### Tasa de Deserción por Área")
        dept_churn = df.groupby('Department')['Estado'].value_counts(normalize=True).unstack().fillna(0)
        if 'Renunció' in dept_churn.columns:
            fig_dept = px.bar(dept_churn, x=dept_churn.index, y='Renunció', color_discrete_sequence=['#FF7043'])
            fig_dept.update_layout(yaxis_tickformat='.0%', coloraxis_showscale=False)
            st.plotly_chart(fig_dept, use_container_width=True)

    with col4:
        st.markdown("### Impacto de Horas Extra en Bajas")
        df_ren = df[df['Estado'] == 'Renunció']
        fig_over = px.pie(df_ren, names='HorasExtra', hole=0.5, color_discrete_sequence=['#EF5350', '#90CAF9'])
        st.plotly_chart(fig_over, use_container_width=True)

    # --- STORYTELLING: EL CICLO DE VIDA ---
    st.markdown("---")
    st.markdown("### Permanencia en la Compañía")
    st.caption("Este gráfico de superposición (overlay) permite identificar si las renuncias ocurren principalmente en los primeros años (curva de aprendizaje) o en etapas más avanzadas.")
    fig_hist = px.histogram(
        df, x="YearsAtCompany", color="Estado", barmode="overlay",
        color_discrete_map={'Renunció': '#EF5350', 'Activo': '#26A69A'},
        labels={'YearsAtCompany': 'Años en la Empresa'},
        height=400, template="plotly_white"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- RESUMEN EJECUTIVO FINAL ---
    st.markdown("---")
    st.subheader("Resumen Ejecutivo")
    
    # Lógica de conclusión basada en datos
    top_dept = df.groupby('Department')['Estado'].value_counts(normalize=True).unstack().fillna(0)['Renunció'].idxmax()
    impacto_he = "alto" if len(df_ren[df_ren['HorasExtra'] == 'Sí']) > len(df_ren)/2 else "moderado"
    
    st.info(f"""
    **Conclusión Estratégica:** Actualmente, el segmento bajo el contrato de **{contrato_sel}** muestra que el departamento de **{top_dept}** es el foco principal de atención. 
    Se observa un impacto **{impacto_he}** de las horas extra en la rotación. La mayor densidad de bajas se concentra en empleados con niveles de satisfacción por debajo del promedio.
    """)

if __name__ == "__main__":
    render_rotacion_dashboard()