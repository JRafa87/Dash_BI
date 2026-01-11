import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# ==========================================
# PROMPT MAESTRO (Configuración Global)
# ==========================================
PROMPT_SISTEMA = """
Actúa como un analista experto en UX y Business Intelligence.
Clasifica el feedback basándote en estos ejemplos:

EJEMPLOS:
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
Analiza el comentario y responde ÚNICAMENTE: [Sentimiento][Categoría]
"""

class ProcesadorUsabilidad:
    def __init__(self):
        # Configuración de API KEY
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.mapa_likert = {
            "Muy en desacuerdo": 1, "En desacuerdo": 2,
            "Ni de acuerdo ni en desacuerdo": 3,
            "De acuerdo": 4, "Muy de acuerdo": 5
        }

    def calcular_sus_score(self, df):
        df_copy = df.copy()
        # Mapear de texto a número (P1 a P10)
        for i in range(1, 11):
            col = f'P{i}'
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].map(self.mapa_likert).fillna(3) # 3 por defecto si hay error
        
        def formula_sus(row):
            impares = sum([row[f'P{i}'] - 1 for i in [1, 3, 5, 7, 9]])
            pares = sum([5 - row[f'P{i}'] for i in [2, 4, 6, 8, 10]])
            return (impares + pares) * 2.5
        
        return df_copy.apply(formula_sus, axis=1)

    def clasificar_ia(self, texto):
        if not texto or pd.isna(texto): return "[N/A][Sin Observación]"
        try:
            response = self.model.generate_content(f"{PROMPT_SISTEMA}\nFeedback: '{texto}'")
            return response.text
        except:
            return "[Error][IA]"

# ==========================================
# FUNCIÓN DE RENDERIZADO (Para la App Principal)
# ==========================================
def render_modulo_usabilidad():
    """Esta es la función que llamas desde main.py"""
    st.subheader("📊 Módulo de Análisis SUS y Feedback")

    # 1. Conexión a datos
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read()
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return

    # 2. Inicializar lógica
    procesador = ProcesadorUsabilidad()

    # 3. Filtro por ID (Persistencia de selección)
    ids_vigentes = df['ID'].unique()
    id_seleccionado = st.sidebar.selectbox("Filtro: ID de Encuesta", ids_vigentes)
    
    df_filtrado = df[df['ID'] == id_seleccionado].copy()

    # 4. Cálculos
    df_filtrado['SUS_Score'] = procesador.calcular_sus_score(df_filtrado)
    sus_avg = df_filtrado['SUS_Score'].mean()

    # 5. Visualización de Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("SUS Score Promedio", f"{sus_avg:.1f}")
    m2.metric("Respuestas", len(df_filtrado))
    m3.info("Meta de usabilidad: > 68.0")

    # 6. Sección de IA
    st.write("---")
    if st.button("🚀 Analizar Comentarios con Gemini"):
        with st.spinner("Clasificando feedback según tus 20 ejemplos..."):
            df_filtrado['IA_Result'] = df_filtrado['OBSERVACION'].apply(procesador.clasificar_ia)
            df_filtrado[['Sentimiento', 'Categoria']] = df_filtrado['IA_Result'].str.extract(r'\[(.*?)\]\[(.*?)\]')
            
            # Gráficos
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Sentimiento**")
                st.bar_chart(df_filtrado['Sentimiento'].value_counts())
            with c2:
                st.write("**Categorías**")
                st.bar_chart(df_filtrado['Categoria'].value_counts())

    # 7. Tabla Detallada
    st.write("**Detalle de datos filtrados:**")
    st.dataframe(df_filtrado[['ID', 'SUS_Score', 'OBSERVACION']])