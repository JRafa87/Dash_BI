import streamlit as st
import google.generativeai as genai
import pandas as pd
from supabase import create_client, Client
from fpdf import FPDF
import datetime

# ==========================================
# PROMPT MAESTRO (Configuración de la IA)
# ==========================================
PROMPT_SISTEMA = """
Actúa como un analista experto en UX (User Experience) y Business Intelligence.
Tu tarea es clasificar el feedback de los usuarios basándote en los siguientes ejemplos:

EJEMPLOS DE REFERENCIA (Few-Shot):
1. 'La experiencia fue buena' -> [Positivo][Satisfacción]
2. 'Estoy satisfecho con el dashboard' -> [Positivo][Satisfacción]
3. 'El diseño es agradable pero falta agregar mas estaditicos llamativos' -> [Neutral][Visualización]
4. 'Seria bueno agregar mas ayuda visual o mensaje explicativo de que trata' -> [Neutral][Explicabilidad]
5. 'Creo q se puede mejorar los graficos para una explicacion mas detallada' -> [Neutral][Visualización]
6. 'Todo bien' -> [Positivo][Satisfacción]
7. 'Cumple su funcion de analizar bien la rotacion de personal' -> [Positivo][Utilidad]
8. 'No tuve incovenientes excelente' -> [Positivo][Satisfacción]
9. 'Podria simplificarse para hacer mas interactivo' -> [Neutral][Usabilidad]
10. 'El sistema es bueno pero necesita una retroalimentacion' -> [Neutral][Explicabilidad]
11. 'Es una herramienta util para tomar decisiones' -> [Positivo][Utilidad]
12. 'Al principio parece complejo pero con el uso es facil' -> [Positivo][Curva de Aprendizaje]
13. 'Muestra informacion relevante y facilita el analisis de datos' -> [Positivo][Utilidad]
14. 'Me costos ubicar los filtros' -> [Negativo][Navegación]
15. 'Podria mejorar su explicabilidad' -> [Neutral][Explicabilidad]
16. 'Facil de entender' -> [Positivo][Usabilidad]
17. 'Puede mejorar su usabilidad' -> [Neutral][Usabilidad]
18. 'Los graficos y colores son didacticos' -> [Positivo][Visualización]
19. 'Se podeian agregar descripciones para cada metricas' -> [Neutral][Explicabilidad]
20. 'Algunas seccilnes podrian mejorar para una mejor navegacion' -> [Neutral][Navegación]

INSTRUCCIÓN:
Analiza el comentario del usuario y responde ÚNICAMENTE en el formato: [Sentimiento][Categoría]
"""

# ==========================================
# CLASE DE PROCESAMIENTO
# ==========================================
class ProcesadorUsabilidad:
    def __init__(self):
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                st.error("⚠️ No se encontró 'GOOGLE_API_KEY' en los Secrets.")
                self.model = None
        except Exception as e:
            st.error(f"Error al configurar Gemini: {e}")
            self.model = None

    def calcular_sus_score(self, df):
        """Calcula el puntaje SUS de 0 a 100 según el estándar"""
        def formula_sus(row):
            try:
                # Preguntas Positivas (1,3,5,7,9): (Valor - 1)
                # Preguntas Negativas (2,4,6,8,10): (5 - Valor)
                impares = (row['p1']-1) + (row['p3']-1) + (row['p5']-1) + (row['p7']-1) + (row['p9']-1)
                pares = (5-row['p2']) + (5-row['p4']) + (5-row['p6']) + (5-row['p8']) + (5-row['p10'])
                return (impares + pares) * 2.5
            except:
                return 0.0
        return df.apply(formula_sus, axis=1)

    def clasificar_con_gemini(self, observacion):
        if not self.model or not observacion or pd.isna(observacion):
            return "[N/A][Sin Datos]"
        try:
            prompt_final = f"{PROMPT_SISTEMA}\nComentario a analizar: '{observacion}'"
            response = self.model.generate_content(prompt_final)
            return response.text.strip()
        except:
            return "[Error][Falla API]"

# ==========================================
# FUNCIÓN GENERADORA DE PDF
# ==========================================
def generar_pdf_reporte(df, score_medio, id_encuesta):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Reporte de Usabilidad - {id_encuesta}", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Fecha de reporte: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="R")
    pdf.ln(10)

    # Métricas Principales
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 10, "1. Resumen de Puntaje SUS", ln=True, fill=True, border=1)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 10, f"SUS Score Promedio: {score_medio:.2f}", border=1)
    pdf.cell(95, 10, f"Total respuestas: {len(df)}", border=1, ln=True)
    
    # Interpretación
    estado = "Excelente" if score_medio >= 80 else "Aceptable" if score_medio >= 68 else "Crítico"
    pdf.cell(190, 10, f"Interpretación del Sistema: {estado}", border=1, ln=True)
    pdf.ln(10)

    # Detalle de Comentarios
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "2. Detalle de Feedback y Análisis IA", ln=True, fill=True, border=1)
    pdf.set_font("Arial", "", 9)
    
    for i, row in df.iterrows():
        usuario = str(row['usuario'])[:30]
        obs = str(row['observacion'])[:80] if row['observacion'] else "Sin comentario"
        ia = row.get('IA_Raw', 'No analizado')
        
        texto = f"User: {usuario} | SUS: {row['SUS_Score']} | IA: {ia}\nObs: {obs}"
        pdf.multi_cell(190, 8, texto, border=1)
        pdf.ln(2)

    return pdf.output(dest="S").encode("latin-1", errors="replace")

# ==========================================
# RENDERIZADO DEL MÓDULO
# ==========================================
def render_modulo_usabilidad():
    st.title("📊 Análisis Maestro de Usabilidad")
    
    # 1. Conexión a Supabase
    try:
        supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        response = supabase.table("encuestas_usabilidad").select("*").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return

    if df.empty:
        st.warning("No hay datos registrados aún.")
        return

    procesador = ProcesadorUsabilidad()

    # 2. Filtrado
    id_encuesta = st.sidebar.selectbox("Filtrar por Encuesta", df['id_encuesta'].unique())
    df_filtrado = df[df['id_encuesta'] == id_encuesta].copy()

    # 3. Cálculos
    df_filtrado['SUS_Score'] = procesador.calcular_sus_score(df_filtrado)
    promedio = df_filtrado['SUS_Score'].mean()

    # 4. KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Puntaje SUS", f"{promedio:.1f}")
    c2.metric("N° Encuestados", len(df_filtrado))
    if promedio >= 68: c3.success("Estado: Óptimo")
    else: c3.error("Estado: Crítico")

    # 5. Análisis IA
    st.divider()
    if st.button("🚀 Ejecutar Clasificación Gemini AI sobre Feedback"):
        with st.spinner("La IA está analizando los comentarios..."):
            df_filtrado['IA_Raw'] = df_filtrado['observacion'].apply(procesador.clasificar_con_gemini)
            
            # Gráficos rápidos
            extracted = df_filtrado['IA_Raw'].str.extract(r'\[(.*?)\]\[(.*?)\]')
            df_filtrado['Sentimiento'] = extracted[0]
            df_filtrado['Categoria'] = extracted[1]
            
            g1, g2 = st.columns(2)
            with g1:
                st.write("**Sentimientos**")
                st.bar_chart(df_filtrado['Sentimiento'].value_counts())
            with g2:
                st.write("**Categorías UX**")
                st.bar_chart(df_filtrado['Categoria'].value_counts())

    # 6. Exportación y Tabla
    st.divider()
    
    pdf_data = generar_pdf_reporte(df_filtrado, promedio, id_encuesta)
    st.download_button(
        label="📥 Descargar Reporte en PDF",
        data=pdf_data,
        file_name=f"Reporte_SUS_{id_encuesta}.pdf",
        mime="application/pdf"
    )

    st.subheader("Registros Completos")
    st.dataframe(df_filtrado, use_container_width=True)