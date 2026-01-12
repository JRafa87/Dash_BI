import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Portal de Analítica de Talento")

@st.cache_data(ttl=600)
def load_consolidado():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    res = supabase.table("consolidado").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Procesamiento y Traducciones Totales
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Renunció' if pd.notna(x) else 'Activo')
    df['MonthlyIncome'] = pd.notna(df['MonthlyIncome']) # Asegurar que es numérico
    df['MonthlyIncome'] = pd.to_numeric(df['MonthlyIncome'], errors='coerce')
    df['Genero'] = df['Gender'].map({'Male': 'Masculino', 'Female': 'Femenino'}).fillna(df['Gender'])
    df['HorasExtra'] = df['OverTime'].map({'Yes': 'Sí', 'No': 'No'}).fillna(df['OverTime'])
    
    # Traducir Departamentos si vienen en inglés
    traduccion_dept = {
        'Sales': 'Ventas',
        'Research & Development': 'I+D',
        'Human Resources': 'Recursos Humanos'
    }
    df['Departamento'] = df['Department'].replace(traduccion_dept)
    return df

def render_rotacion_dashboard():
    df_raw = load_consolidado()

    # Título Centrado y Estilizado
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Reporte Estratégico de Capital Humano</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4B5563;'>Análisis ejecutivo sobre la retención y el comportamiento del personal</p>", unsafe_allow_html=True)
    
    # --- FILTROS SUPERIORES ---
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        genero_sel = st.selectbox("🎯 Filtrar por Género:", ['Todos'] + sorted(df_raw['Genero'].unique().tolist()))
    with f2:
        contrato_sel = st.selectbox("📄 Filtrar por Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))

    # Aplicar Filtros
    df = df_raw.copy()
    if genero_sel != 'Todos': df = df[df['Genero'] == genero_sel]
    if contrato_sel != 'Todos': df = df[df['Tipocontrato'] == contrato_sel]

    st.markdown("---")

    # --- KPIs CON COLOR Y DISEÑO AJUSTADO ---
    total = len(df)
    bajas = len(df[df['Estado'] == 'Renunció'])
    tasa = (bajas/total*100) if total > 0 else 0
    ingreso = df['MonthlyIncome'].mean() if not df.empty else 0

    st.markdown(f"""
        <div style="display: flex; justify-content: space-around; gap: 15px; margin-bottom: 25px;">
            <div style="flex: 1; background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%); padding: 12px; border-radius: 10px; border-bottom: 4px solid #0284C7; text-align: center;">
                <span style="font-size: 12px; color: #0369A1; font-weight: bold; display: block;">PLANTILLA TOTAL</span>
                <span style="font-size: 26px; color: #0C4A6E; font-weight: bold;">{total}</span>
            </div>
            <div style="flex: 1; background: linear-gradient(135deg, #FFFBED 0%, #FEF3C7 100%); padding: 12px; border-radius: 10px; border-bottom: 4px solid #D97706; text-align: center;">
                <span style="font-size: 12px; color: #92400E; font-weight: bold; display: block;">PERSONAL ACTIVO</span>
                <span style="font-size: 26px; color: #78350F; font-weight: bold;">{total - bajas}</span>
            </div>
            <div style="flex: 1; background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); padding: 12px; border-radius: 10px; border-bottom: 4px solid #DC2626; text-align: center;">
                <span style="font-size: 12px; color: #991B1B; font-weight: bold; display: block;">ROTACIÓN (BAJAS)</span>
                <span style="font-size: 26px; color: #B91C1C; font-weight: bold;">{tasa:.1f}%</span>
            </div>
            <div style="flex: 1; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); padding: 12px; border-radius: 10px; border-bottom: 4px solid #16A34A; text-align: center;">
                <span style="font-size: 12px; color: #166534; font-weight: bold; display: block;">SALARIO PROMEDIO</span>
                <span style="font-size: 26px; color: #14532D; font-weight: bold;">${ingreso:,.0f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 1. DISPERSIÓN: STORYTELLING SOBRE EL PERFIL ---
    st.markdown("<h3 style='text-align: center;'>Relación de Edad y Compensación</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>Analizamos si existe una correlación entre el nivel salarial y la fuga de talento según la etapa de vida del empleado.</p>", unsafe_allow_html=True)
    fig_scat = px.scatter(
        df, x='Age', y='MonthlyIncome', color='Estado',
        hover_data={'Age': True, 'MonthlyIncome': ':$,.0f', 'JobRole': True},
        color_discrete_map={'Renunció': '#EF4444', 'Activo': '#10B981'},
        labels={'Age': 'Edad del Colaborador', 'MonthlyIncome': 'Ingreso Mensual', 'Estado': 'Situación Actual'},
        height=450, template="plotly_white"
    )
    st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown("---")

    # --- 2. FACTORES PSICOLÓGICOS Y BALANCE ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h3 style='text-align: center;'>Impacto de la Satisfacción</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Distribución de bajas según el nivel de felicidad reportado (1 al 4).</p>", unsafe_allow_html=True)
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Cantidad')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Cantidad', color_discrete_sequence=['#F87171'])
        fig_sat.update_layout(coloraxis_showscale=False, xaxis_title="Nivel de Satisfacción", yaxis_title="Número de Bajas")
        st.plotly_chart(fig_sat, use_container_width=True)

    with c2:
        st.markdown("<h3 style='text-align: center;'>Equilibrio Vida-Trabajo</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>¿Es el tiempo personal un factor crítico para las renuncias en este grupo?</p>", unsafe_allow_html=True)
        df_wb = df[df['Estado'] == 'Renunció'].groupby('WorkLifeBalance').size().reset_index(name='Cantidad')
        fig_wb = px.bar(df_wb, x='WorkLifeBalance', y='Cantidad', color_discrete_sequence=['#FBBF24'])
        fig_wb.update_layout(coloraxis_showscale=False, xaxis_title="Nivel de Balance", yaxis_title="Número de Bajas")
        st.plotly_chart(fig_wb, use_container_width=True)

    st.markdown("---")

    # --- 3. CARGA LABORAL Y DEPARTAMENTOS ---
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<h3 style='text-align: center;'>Tasa de Fuga por Departamento</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Porcentaje comparativo de renuncias según el área organizacional.</p>", unsafe_allow_html=True)
        dept_churn = df.groupby('Departamento')['Estado'].value_counts(normalize=True).unstack().fillna(0)
        if 'Renunció' in dept_churn.columns:
            fig_dept = px.bar(dept_churn, x=dept_churn.index, y='Renunció', color_discrete_sequence=['#FB923C'])
            fig_dept.update_layout(yaxis_tickformat='.0%', yaxis_title="% de Salidas", xaxis_title="Área")
            st.plotly_chart(fig_dept, use_container_width=True)

    with c4:
        st.markdown("<h3 style='text-align: center;'>Prevalencia de Horas Extra</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>¿Qué porcentaje de los que se fueron trabajaban más de lo debido?</p>", unsafe_allow_html=True)
        df_ren = df[df['Estado'] == 'Renunció']
        fig_over = px.pie(df_ren, names='HorasExtra', hole=0.6, color_discrete_sequence=['#EF4444', '#60A5FA'])
        st.plotly_chart(fig_over, use_container_width=True)

    # --- 4. ANTIGÜEDAD (MODO OVERLAY) ---
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Ciclo de Permanencia en la Organización</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>Comparativa de antigüedad entre empleados activos y aquellos que decidieron retirarse.</p>", unsafe_allow_html=True)
    fig_hist = px.histogram(
        df, x="YearsAtCompany", color="Estado", barmode="overlay",
        color_discrete_map={'Renunció': '#EF4444', 'Activo': '#10B981'},
        labels={'YearsAtCompany': 'Años de Antigüedad', 'count': 'Total de Personas'},
        height=400, template="plotly_white"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- CONCLUSIONES FINALES ---
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Interpretación Ejecutiva</h2>", unsafe_allow_html=True)
    
    # Lógica para storytelling automático
    try:
        peor_area = df.groupby('Departamento')['Estado'].value_counts(normalize=True).unstack().fillna(0)['Renunció'].idxmax()
    except:
        peor_area = "Información insuficiente"
    
    st.info(f"""
    📢 **Resumen del Análisis:** Bajo el filtro de **{contrato_sel}**, observamos una rotación del **{tasa:.1f}%**. 
    
    El área de **{peor_area}** presenta la mayor tasa de deserción relativa. Se recomienda prestar especial atención al gráfico de Horas Extra, ya que el desgaste es un factor que coincide con los niveles bajos de satisfacción reportados.
    """)

if __name__ == "__main__":
    render_rotacion_dashboard()