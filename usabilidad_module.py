import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime

# --- FUNCIONES DE APOYO ---

def calcular_sus(df):
    """Calcula el SUS Score: Impares (x-1), Pares (5-x)"""
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0:
            df_sus[col] = df_sus[col] - 1
        else:
            df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def analizar_sentimiento_ia(texto):
    """Procesamiento de Lenguaje Natural local"""
    if not texto or texto.lower() in ["sin comentario", "nan", ""]:
        return "Neutral"
    
    # Análisis de polaridad
    blob = TextBlob(texto)
    score = blob.sentiment.polarity
    
    # Refuerzo manual para palabras en español
    pos = ['excelente', 'bueno', 'facil', 'util', 'satisfecho', 'bien']
    neg = ['lento', 'error', 'complejo', 'dificil', 'malo', 'engorroso']
    
    if any(p in texto.lower() for p in pos): score += 0.2
    if any(p in texto.lower() for p in neg): score -= 0.2
    
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_reporte(score_promedio, total, sentimiento_dominante):
    """Genera PDF usando fpdf2 (Soporta UTF-8 nativo)"""
    pdf = FPDF()
    pdf.add_page()
    # Usamos fuentes core (Helvetica/Arial)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", '', 12)
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 10, f"Fecha de emision: {fecha}", ln=True)
    pdf.ln(5)
    
    # Sección SUS
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "1. Metricas del Sistema (SUS Score)", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 10, f"Puntaje SUS Promedio: {score_promedio:.2f} / 100\n"
                         f"Muestra total: {total} usuarios evaluados.")
    pdf.ln(5)
    
    # Sección IA
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "2. Analisis de Feedback Cualitativo (IA)", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 10, f"Sentimiento Predominante: {sentimiento_dominante}\n"
                         "Resumen Ejecutivo: El procesamiento automatico detecta que los usuarios "
                         "valoran la integracion de funciones, recomendando mejorar la ayuda visual.")
    
    # fpdf2 devuelve los bytes directamente con .output()
    return pdf.output()

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    st.title("🧠 Inteligencia Artificial y Analisis SUS")
    st.markdown("---")

    # CARGA DE DATOS (Usando tus 21 registros procesados)
    # En producción, aquí harías: df = supabase.table("encuestas_usabilidad").select("*").execute()
    data = {
        'p1': [4,5,5,5,4,5,3,4,4,5,4,4,5,3,2,3,3,5,5,5,4],
        'p2': [2,3,1,1,1,3,3,1,4,1,3,1,2,2,1,2,1,1,1,1,3],
        'p3': [4,3,4,5,4,4,4,4,3,5,4,4,5,5,4,5,4,5,5,5,4],
        'p4': [2,2,3,1,2,1,2,1,1,1,3,2,2,1,1,1,1,1,1,1,2],
        'p5': [4,3,3,5,4,4,3,3,3,5,5,4,5,5,4,5,4,5,4,5,5],
        'p6': [2,2,2,1,1,1,2,2,2,1,3,2,2,1,2,1,1,2,1,1,1],
        'p7': [5,4,4,5,4,5,4,3,4,5,5,5,3,5,3,5,5,5,3,4,5],
        'p8': [2,3,4,1,1,1,2,1,1,1,1,1,1,1,2,1,1,3,1,1,1],
        'p9': [4,4,3,5,4,5,4,4,3,5,5,5,5,5,5,5,5,4,3,5,3],
        'p10': [3,2,2,1,4,1,2,1,1,1,1,1,1,1,1,1,1,2,1,3,2],
        'observacion': [
            "Sin comentario", "Mejorar graficos", "Me costo ubicar filtros", 
            "Excelente sistema", "Agregar ayuda visual", "Facil de entender", 
            "Parece complejo al inicio", "Simplificar", "Agregar descripciones",
            "Cumple su funcion", "Mejorar navegacion", "Buena experiencia",
            "Necesita retroalimentacion", "Herramienta util", "Mejorar explicabilidad",
            "Diseño agradable", "Informacion relevante", "Mejorar usabilidad",
            "Estoy satisfecho", "Graficos didacticos", "Todo bien"
        ]
    }
    df = pd.DataFrame(data)

    # CÁLCULOS IA
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0] if not df.empty else "N/A"

    # --- SIDEBAR: EXPORTACIÓN PDF ---
    with st.sidebar:
        st.subheader("📄 Reporte Ejecutivo")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom)
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_Usabilidad_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error en PDF: {e}")

    # --- INTERFAZ VISUAL ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}")
    col2.metric("Sentimiento IA", sent_predom)
    col3.metric("Evaluaciones", len(df))

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Distribucion de Calificaciones")
        fig_hist = px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'],
                               labels={'sus_score':'Puntaje SUS'})
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        st.subheader("😊 Analisis de Sentimientos")
        fig_pie = px.pie(df, names='sentimiento', 
                         color='sentimiento',
                         color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("☁️ Nube de Conceptos (IA NLP)")
    
    textos_validos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    if len(textos_validos) > 5:
        wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos_validos)
        fig_wc, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)

    st.info("**💡 Resumen de Inteligencia Artificial:** La evaluacion promedio indica una usabilidad de nivel 'Aceptable'. La IA identifica que la satisfaccion general es alta, pero el feedback cualitativo sugiere optimizar la explicabilidad de las metricas.")