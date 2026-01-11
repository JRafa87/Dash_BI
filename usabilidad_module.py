import streamlit as st
import google.generativeai as genai
import pandas as pd
from supabase import create_client, Client

# ==========================================
# PROMPT MAESTRO (Configuración de la IA)
# ==========================================
PROMPT_SISTEMA = """
Actúa como un analista experto en UX y Business Intelligence.
Tu tarea es clasificar el feedback de los usuarios basándote en los siguientes ejemplos:

EJEMPLOS DE REFERENCIA:
1. 'La experiencia fue buena' -> [Positivo][Satisfacción]
... (se mantienen tus 20 ejemplos) ...
20. 'Algunas seccilnes podrian mejorar para una mejor navegacion' -> [Neutral][Navegación]

INSTRUCCIÓN:
Analiza el comentario del usuario y responde ÚNICAMENTE en el formato: [Sentimiento][Categoría]
"""

class ProcesadorUsabilidad:
    def __init__(self):
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                st.error("⚠️ Falta GOOGLE_API_KEY en Secrets.")
                self.model = None
        except Exception as e:
            st.error(f"Error IA: {e}")
            self.model = None

    def calcular_sus_score(self, df):
        """Calcula el puntaje SUS (0-100) usando columnas p1...p10"""
        def formula_sus(row):
            try:
                # Impares (p1, p3, p5, p7, p9) -> Valor - 1
                impares = (row['p1']-1) + (row['p3']-1) + (row['p5']-1) + (row['p7']-1) + (row['p9']-1)
                # Pares (p2, p4, p6, p8, p10) -> 5 - Valor
                pares = (5-row['p2']) + (5-row['p4']) + (5-row['p6']) + (5-row['p8']) + (5-row['p10'])
                return (impares + pares) * 2.5
            except:
                return 0.0
        return df.apply(formula_sus, axis=1)

    def clasificar_con_gemini(self, observacion):
        if not self.model or not observacion or pd.isna(observacion):
            return "[N/A][Sin Observación]"
        try:
            response = self.model.generate_content(f"{PROMPT_SISTEMA}\nFeedback: '{observacion}'")
            return response.text.strip()
        except:
            return "[Error][Falla en API]"

def render_modulo_usabilidad():
    st.title("📊 Análisis de Usabilidad (SUS)")
    st.info("Datos obtenidos desde Supabase analizados con Gemini AI.")

    # 1. Conexión a Supabase
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        
        # Consultar la tabla
        response = supabase.table("encuestas_usabilidad").select("*").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    if df.empty:
        st.warning("No hay datos en la tabla 'encuestas_usabilidad'.")
        return

    procesador = ProcesadorUsabilidad()

    # 2. Filtro por ID de Encuesta
    if 'id_encuesta' in df.columns:
        ids_vigentes = df['id_encuesta'].unique()
        id_seleccionado = st.sidebar.selectbox("Selecciona ID de Encuesta", ids_vigentes)
        df_filtrado = df[df['id_encuesta'] == id_seleccionado].copy()
    else:
        st.error("Columna 'id_encuesta' no encontrada.")
        return

    # 3. Cálculos
    df_filtrado['SUS_Score'] = procesador.calcular_sus_score(df_filtrado)
    sus_promedio = df_filtrado['SUS_Score'].mean()

    # 4. Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("SUS Score Promedio", f"{sus_promedio:.1f}")
    m2.metric("Respuestas", len(df_filtrado))
    if sus_promedio >= 68:
        m3.success("Estado: Aceptable")
    else:
        m3.warning("Estado: Crítico")

    # 5. Análisis IA
    st.divider()
    if st.button("🚀 Ejecutar Análisis Cualitativo (IA)"):
        if 'observacion' in df_filtrado.columns:
            with st.spinner("Clasificando feedback..."):
                df_filtrado['IA_Raw'] = df_filtrado['observacion'].apply(procesador.clasificar_con_gemini)
                extracted = df_filtrado['IA_Raw'].str.extract(r'\[(.*?)\]\[(.*?)\]')
                df_filtrado['Sentimiento'] = extracted[0]
                df_filtrado['Categoria'] = extracted[1]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Sentimiento**")
                    st.bar_chart(df_filtrado['Sentimiento'].value_counts())
                with c2:
                    st.write("**Categoría**")
                    st.bar_chart(df_filtrado['Categoria'].value_counts())
        else:
            st.error("No existe la columna 'observacion'.")

    # 6. Tabla Final
    st.write("### Detalle de Datos")
    cols = ['id_encuesta', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'SUS_Score', 'observacion']
    if 'Sentimiento' in df_filtrado.columns:
        cols += ['Sentimiento', 'Categoria']
    
    st.dataframe(df_filtrado[cols], use_container_width=True)