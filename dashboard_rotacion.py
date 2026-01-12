import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="HR Analytics Pro")

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

    st.title("🏹 Inteligencia de Datos: Análisis de Rotación Integral")
    
    # --- FILTROS SUPERIORES ---
    st.markdown("### 🎛️ Filtros Globales")
    f1, f2 = st.columns(2)
    with f1:
        genero_sel = st.selectbox("Seleccione Género:", ['Todos'] + sorted(df_raw['Genero'].unique().tolist()))
    with f2:
        contrato_sel = st.selectbox("Seleccione Tipo de Contrato:", ['Todos'] + sorted(df_raw['Tipocontrato'].dropna().unique().tolist()))

    # Aplicar Filtros
    df = df_raw.copy()
    if genero_sel != 'Todos': df = df[df['Genero'] == genero_sel]
    if contrato_sel != 'Todos': df = df[df['Tipocontrato'] == contrato_sel]

    st.markdown("---")

    # --- KPIs CON DISEÑO PREMIUM ---
    total = len(df)
    bajas = len(df[df['Estado'] == 'Renunció'])
    tasa = (bajas/total*100) if total > 0 else 0
    ingreso = df['MonthlyIncome'].mean() if not df.empty else 0

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px;">
            <div style="flex: 1; background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 6px solid #007BFF; text-align: center;">
                <p style="margin: 0; font-size: 13px; color: #666; font-weight: bold;">TOTAL EMPLEADOS</p>
                <h2 style="margin: 5px 0; color: #333;">{total}</h2>
            </div>
            <div style="flex: 1; background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 6px solid #DC3545; text-align: center;">
                <p style="margin: 0; font-size: 13px; color: #666; font-weight: bold;">BAJAS</p>
                <h2 style="margin: 5px 0; color: #DC3545;">{bajas}</h2>
            </div>
            <div style="flex: 1; background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 6px solid #FFC107; text-align: center;">
                <p style="margin: 0; font-size: 13px; color: #666; font-weight: bold;">TASA FUGA</p>
                <h2 style="margin: 5px 0; color: #333;">{tasa:.1f}%</h2>
            </div>
            <div style="flex: 1; background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 6px solid #28A745; text-align: center;">
                <p style="margin: 0; font-size: 13px; color: #666; font-weight: bold;">SUELDO PROM.</p>
                <h2 style="margin: 5px 0; color: #333;">${ingreso:,.0f}</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- NIVEL 1: DISPERSIÓN (ANCHO COMPLETO) ---
    st.subheader("🎯 Mapa de Dispersión: Edad vs Salario")
    fig_scat = px.scatter(
        df, x='Age', y='MonthlyIncome', color='Estado',
        hover_data={'Age': True, 'MonthlyIncome': ':$,.0f', 'JobRole': True},
        color_discrete_map={'Renunció': '#DC3545', 'Activo': '#28A745'},
        labels={'Age': 'Edad', 'MonthlyIncome': 'Sueldo ($)', 'Estado': 'Estado'},
        height=450, template="plotly_white"
    )
    st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown("---")

    # --- NIVEL 2: SATISFACCIÓN Y EQUILIBRIO (LADO A LADO) ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Fugas por Satisfacción Laboral")
        df_sat = df[df['Estado'] == 'Renunció'].groupby('JobSatisfaction').size().reset_index(name='Bajas')
        fig_sat = px.bar(df_sat, x='JobSatisfaction', y='Bajas', color='Bajas', color_continuous_scale='Reds')
        st.plotly_chart(fig_sat, use_container_width=True)

    with c2:
        st.subheader("⚖️ Fugas por Equilibrio Vida-Trabajo")
        df_wb = df[df['Estado'] == 'Renunció'].groupby('WorkLifeBalance').size().reset_index(name='Bajas')
        fig_wb = px.bar(df_wb, x='WorkLifeBalance', y='Bajas', color='Bajas', color_continuous_scale='YlOrRd')
        st.plotly_chart(fig_wb, use_container_width=True)

    st.markdown("---")

    # --- NIVEL 3: ÁREAS Y HORAS EXTRA (LADO A LADO) ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("🏢 Tasa de Deserción por Área")
        dept_churn = df.groupby('Department')['Estado'].value_counts(normalize=True).unstack().fillna(0)
        if 'Renunció' in dept_churn.columns:
            fig_dept = px.bar(dept_churn, x=dept_churn.index, y='Renunció', color_discrete_sequence=['#FF7043'])
            fig_dept.update_layout(yaxis_tickformat='.0%')
            st.plotly_chart(fig_dept, use_container_width=True)

    with c4:
        st.subheader("🍩 Impacto de Horas Extra (Bajas)")
        df_ren = df[df['Estado'] == 'Renunció']
        fig_over = px.pie(df_ren, names='HorasExtra', hole=0.5, color_discrete_sequence=['#D32F2F', '#90CAF9'])
        st.plotly_chart(fig_over, use_container_width=True)

    st.markdown("---")

    # --- NIVEL 4: ANTIGÜEDAD (ANCHO COMPLETO) ---
    st.subheader("⏳ Permanencia en la Compañía: Distribución de Años")
    fig_hist = px.histogram(df, x="YearsAtCompany", color="Estado", barmode="group",
                           color_discrete_map={'Renunció': '#DC3545', 'Activo': '#28A745'},
                           labels={'YearsAtCompany': 'Años en la Empresa', 'count': 'Empleados'},
                           height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- NIVEL 5: RESUMEN EJECUTIVO ---
    st.markdown("---")
    st.header("📝 Resumen Ejecutivo e Insights")
    with st.expander("Ver Conclusiones del Análisis", expanded=True):
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if tasa > 15:
                st.error(f"**Alerta Crítica:** La rotación ({tasa:.1f}%) supera el límite permitido.")
            else:
                st.success(f"**Estado Saludable:** La rotación ({tasa:.1f}%) está bajo control.")
            
            if not df_ren.empty:
                peor_dept = df.groupby('Department')['Estado'].value_counts(normalize=True).unstack().fillna(0)['Renunció'].idxmax()
                st.write(f"**Punto de Fuga:** El departamento de **{peor_dept}** requiere intervención inmediata.")
        
        with col_res2:
            st.subheader("💡 Recomendaciones Estratégicas")
            if not df_ren.empty:
                if len(df_ren[df_ren['HorasExtra'] == 'Sí']) > (len(df_ren) / 2):
                    st.warning("⚠️ Reducir la carga horaria: Las Horas Extra son la principal causa de renuncia.")
                if len(df_ren[df_ren['JobSatisfaction'] <= 2]) > 0:
                    st.info("ℹ️ Mejorar el clima: La satisfacción reportada es baja en los que se retiran.")

if __name__ == "__main__":
    render_rotacion_dashboard()