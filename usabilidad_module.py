import streamlit as st
from st_gsheets_connection import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# ==========================================
# PROMPT MAESTRO (Configuración de la IA)
# ==========================================
PROMPT_SISTEMA = """
Actúa como un analista experto en UX y Business Intelligence.
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

class ProcesadorUsabilidad:
    def __init__(self):
        # Configuración robusta de API KEY
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if not api_key:
                st.error("⚠️ No se encontró 'GOOGLE_API_KEY' en los Secrets.")
                self.model = None
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Error al configurar Gemini: {e}")
            self.model = None

        self.mapa_likert = {
            "Muy en desacuerdo": 1, "En desacuerdo": 2,
            "Ni de acuerdo ni en desacuerdo": 3,
            "De acuerdo": 4, "Muy de acuerdo": 5
        }

    def calcular_sus_score(self, df):
        """Calcula el puntaje SUS de 0 a 100"""
        df_copy = df.copy()
        # Convertir textos de la encuesta a números (P1 a P10)
        for i in range(1, 11):
            col = f'P{i}'
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].map(self.mapa_likert).fillna(3)
        
        def formula_sus(row):
            try:
                # Impares (1,3,5,7,9) -> (Valor - 1)
                # Pares (2,4,6,8,10) -> (5 - Valor)
                impares = sum([row[f'P{i}'] - 1 for i in [1, 3, 5, 7, 9]])
                pares = sum([5 - row[f'P{i}'] for i in [2, 4, 6, 8, 10]])
                return (impares + pares) * 2.5
            except:
                return 0.0
        
        return df_copy.apply(formula_sus, axis=1)

    def clasificar_con_gemini(self, observacion):
        """Llamada a la API de Google AI con el Prompt Maestro"""
        if not self.model:
            return "[Error][IA No Configurada]"
        if not observacion or pd.isna(observacion):
            return "[N/A][Sin Observación]"
        
        try:
            prompt_final = f"{PROMPT_SISTEMA}\nComentario a analizar: '{observacion}'"
            response = self.model.generate_content(prompt_final)
            return response.text.strip()
        except Exception:
            return "[Error][Falla en API]"

# ==========================================
# RENDERIZADO (Función Principal del Módulo)
# ==========================================
def render_modulo_usabilidad():
    st.title("📊 Análisis de Usabilidad (SUS)")
    st.info("Este módulo analiza la percepción de los usuarios mediante el estándar SUS y Clasificación con IA.")

    # 1. Conexión a Google Sheets
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read()
    except Exception as e:
        st.error(f"Error al conectar con Sheets: {e}")
        st.info("Asegúrate de tener 'spreadsheet' configurado en [connections.gsheets] de tus secrets.")
        return

    if df is None or df.empty:
        st.warning("No se encontraron datos en la hoja de cálculo.")
        return

    # 2. Inicializar lógica
    procesador = ProcesadorUsabilidad()

    # 3. Filtro por ID de Encuesta (Persistente)
    if 'ID' in df.columns:
        ids_vigentes = df['ID'].unique()
        id_seleccionado = st.sidebar.selectbox("Selecciona ID de Encuesta", ids_vigentes)
        df_filtrado = df[df['ID'] == id_seleccionado].copy()
    else:
        st.error("No se encontró la columna 'ID' en el Excel.")
        return

    # 4. Cálculos Cuantitativos
    df_filtrado['SUS_Score'] = procesador.calcular_sus_score(df_filtrado)
    sus_promedio = df_filtrado['SUS_Score'].mean()

    # 5. Métricas de Cabecera
    c1, c2, c3 = st.columns(3)
    c1.metric("Puntaje SUS Promedio", f"{sus_promedio:.1f}")
    c2.metric("Total de Respuestas", len(df_filtrado))
    
    if sus_promedio > 68:
        c3.success("Estado: Aceptable / Bueno")
    else:
        c3.warning("Estado: Crítico / Requiere Mejora")

    # 6. --- ANÁLISIS CUALITATIVO (IA) ---
    st.divider()
    st.subheader("🤖 Análisis de Feedback con Gemini AI")
    st.write("Clasificación automática basada en sentimientos y categorías UX.")
    
    if st.button("Ejecutar Análisis de Observaciones"):
        if 'OBSERVACION' in df_filtrado.columns:
            with st.spinner("La IA está procesando los comentarios..."):
                # Aplicar IA
                df_filtrado['IA_Raw'] = df_filtrado['OBSERVACION'].apply(procesador.clasificar_con_gemini)
                
                # Extraer etiquetas con Regex
                extracted = df_filtrado['IA_Raw'].str.extract(r'\[(.*?)\]\[(.*?)\]')
                df_filtrado['Sentimiento'] = extracted[0].str.strip()
                df_filtrado['Categoria'] = extracted[1].str.strip()
                
                # Renderizar Gráficos
                ga1, ga2 = st.columns(2)
                with ga1:
                    st.write("**Sentimiento Predominante**")
                    st.bar_chart(df_filtrado['Sentimiento'].value_counts())
                with ga2:
                    st.write("**Principales Categorías**")
                    st.bar_chart(df_filtrado['Categoria'].value_counts())
                
                st.success("Análisis completado.")
        else:
            st.error("La columna 'OBSERVACION' no existe en el archivo de Google Sheets.")

    # 7. Mostrar Tabla de Datos
    st.divider()
    st.subheader("📋 Detalle de Respuestas Filtradas")
    # Mostrar columnas clave
    cols_mostrar = ['ID', 'SUS_Score', 'OBSERVACION']
    if 'Sentimiento' in df_filtrado.columns:
        cols_mostrar += ['Sentimiento', 'Categoria']
    
    st.dataframe(df_filtrado[cols_mostrar], use_container_width=True)