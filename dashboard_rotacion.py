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
    
    # --- PROCESAMIENTO CORRECTO (CORREGIDO) ---
    df['Estado'] = df['FechaSalida'].apply(lambda x: 'Renunció' if pd.notna(x) else 'Activo')
    # Convertir a numérico sin crear booleanos
    df['MonthlyIncome'] = pd.to_numeric(df['MonthlyIncome'], errors='coerce')
    df['Genero'] = df['Gender'].map({'Male': 'Masculino', 'Female': 'Femenino'}).fillna(df['Gender'])
    df['HorasExtra'] = df['OverTime'].map({'Yes': 'Sí', 'No': 'No'}).fillna(df['OverTime'])
    
    traduccion_dept = {
        'Sales': 'Ventas',
        'Research & Development': 'I+D',
        'Human Resources': 'Recursos Humanos'
    }
    df['Departamento'] = df['Department'].replace(traduccion_dept)
    return df

def render_rotacion_dashboard():
    df_raw = load_consolidado()

    # Título Principal Centrado
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Reporte Estratégico de Capital Humano</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4B5563;'>Análisis ejecutivo sobre la retención y el comportamiento del personal</p>", unsafe_allow_html=True)
    
    # --- FILTROS SUPERIORES ---
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        genero_sel = st.selectbox("🎯 Filtrar por Género:", ['Todos'] + sorted(df_raw['Genero'].unique().tolist()))
    with f2:
        contrato_sel = st.selectbox("📄 Filtrar por Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))

    df = df_raw.copy()
    if genero_sel != 'Todos': df = df[df['Genero'] == genero_sel]
    if contrato_sel != 'Todos': df = df[df['Tipocontrato'] == contrato_sel]

    st.markdown("---")

    # --- KPIs AJUSTADOS ---
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

    # --- 1. GRÁFICO DE DISPERSIÓN (CENTRADITO Y CORREGIDO) ---
    st.markdown("<h3 style='text-align: center;'>Mapa de Talento: Edad vs Salario</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>Relación entre compensación y edad. Los puntos rojos indican fugas potenciales por competitividad.</p>", unsafe_allow_html=True)
    
    fig_scat = px.scatter(
        df, x='Age', y='MonthlyIncome', color='Estado',
        hover_data={'Age': True, 'MonthlyIncome': ':$,.0f', 'JobRole': True},
        color_discrete_map={'Renunció': '#EF5350', 'Activo': '#26A69A'},
        labels={'Age': 'Edad', 'MonthlyIncome': 'Sueldo Mensual', 'Estado': 'Estado'},
        height=500, template="plotly_white"
    )
    fig_scat.update_traces(marker=dict(size=10, opacity=0.7, line=dict(width=1, color='White')))
    st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown("---")

    # --- 2. BIENESTAR Y BALANCE ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h3 style='text-align: center;'>Impacto de la Satisfacción</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Niveles de felicidad reportados por quienes decidieron dejar la empresa.</p>", unsafe_allow_html=True)
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Cantidad')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Cantidad', color_discrete_sequence=['#F87171'])
        fig_sat.update_layout(xaxis_title="Satisfacción (1-4)", yaxis_title="Bajas")
        st.plotly_chart(fig_sat, use_container_width=True)

    with c2:
        st.markdown("<h3 style='text-align: center;'>Equilibrio Vida-Trabajo</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Análisis de cómo la conciliación personal afecta la retención.</p>", unsafe_allow_html=True)
        df_wb = df[df['Estado'] == 'Renunció'].groupby('WorkLifeBalance').size().reset_index(name='Cantidad')
        fig_wb = px.bar(df_wb, x='WorkLifeBalance', y='Cantidad', color_discrete_sequence=['#FBBF24'])
        fig_wb.update_layout(xaxis_title="Balance (1-4)", yaxis_title="Bajas")
        st.plotly_chart(fig_wb, use_container_width=True)

    st.markdown("---")

    # --- 3. ÁREAS Y CARGA LABORAL ---
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<h3 style='text-align: center;'>Tasa de Fuga por Área</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Identificación de departamentos con mayor riesgo de rotación.</p>", unsafe_allow_html=True)
        dept_churn = df.groupby('Departamento')['Estado'].value_counts(normalize=True).unstack().fillna(0)
        if 'Renunció' in dept_churn.columns:
            fig_dept = px.bar(dept_churn, x=dept_churn.index, y='Renunció', color_discrete_sequence=['#FB923C'])
            fig_dept.update_layout(yaxis_tickformat='.0%', yaxis_title="% Salidas")
            st.plotly_chart(fig_dept, use_container_width=True)

    with c4:
        st.markdown("<h3 style='text-align: center;'>Frecuencia de Horas Extra</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px;'>Peso de la carga laboral en el personal que renunció.</p>", unsafe_allow_html=True)
        df_ren = df[df['Estado'] == 'Renunció']
        fig_over = px.pie(df_ren, names='HorasExtra', hole=0.6, color_discrete_sequence=['#EF4444', '#60A5FA'])
        st.plotly_chart(fig_over, use_container_width=True)

    # --- 4. ANTIGÜEDAD OVERLAY ---
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Ciclo de Permanencia en la Organización</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>Comparativa de antigüedad: ¿Perdemos talento nuevo o institucional?</p>", unsafe_allow_html=True)
    fig_hist = px.histogram(
        df, x="YearsAtCompany", color="Estado", barmode="overlay",
        color_discrete_map={'Renunció': '#EF4444', 'Activo': '#10B981'},
        labels={'YearsAtCompany': 'Años en Empresa'},
        height=400, template="plotly_white"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- CONCLUSIÓN ---
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Interpretación Ejecutiva</h2>", unsafe_allow_html=True)
    
    try:
        peor_area = df.groupby('Departamento')['Estado'].value_counts(normalize=True).unstack().fillna(0)['Renunció'].idxmax()
    except:
        peor_area = "No disponible"

    st.info(f"""
    📢 **Resumen:** Con los filtros actuales, la tasa de rotación es del **{tasa:.1f}%**. 
    El área de **{peor_area}** requiere atención. Se observa que la falta de balance vida-trabajo y las horas extra son factores determinantes en las salidas registradas.
    """)

if __name__ == "__main__":
    render_rotacion_dashboard()