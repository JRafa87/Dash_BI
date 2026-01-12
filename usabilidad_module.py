import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
import io
from PIL import Image

# --- FUNCIONES DE APOYO ---

def calcular_sus(df):
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0: df_sus[col] = df_sus[col] - 1
        else: df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def analizar_sentimiento_ia(texto):
    if not texto or texto.lower() in ["sin comentario", "nan", ""]: return "Neutral"
    blob = TextBlob(texto)
    score = blob.sentiment.polarity
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_espejo(promedio_sus, total, sent_predom, fig_hist, fig_pie, fig_wc):
    """Genera un PDF con las gráficas incluidas para que sea igual a la pantalla"""
    pdf = FPDF()
    pdf.add_page()
    
    # Título del PDF
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # Métricas
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Puntaje SUS Promedio: {promedio_sus:.2f} | Muestra: {total} | Sentimiento: {sent_predom}", ln=True, align='C')
    pdf.ln(10)

    # --- Gráfica 1: Histograma ---
    img_hist = fig_hist.to_image(format="png", width=700, height=400)
    pdf.image(io.BytesIO(img_hist), x=15, w=180)
    pdf.ln(5)

    # --- Gráfica 2: Pie Chart ---
    img_pie = fig_pie.to_image(format="png", width=700, height=400)
    pdf.image(io.BytesIO(img_pie), x=45, w=120)
    
    # --- Nube de Palabras ---
    if fig_wc:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos (NLP)", ln=True, align='C')
        # Guardar nube de palabras temporalmente
        img_buf = io.BytesIO()
        fig_wc.savefig(img_buf, format='png', bbox_inches='tight')
        pdf.image(img_buf, x=15, w=180)

    # Devolver bytes del PDF
    return pdf.output(dest='S')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # 1. TÍTULO CENTRADO
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos
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
        'observacion': ["Excelente", "Mejorar graficos", "Filtros complejos", "Muy util", "Graficos didacticos", "Todo bien", "Facil", "Rapido", "Satisfecho", "Interfaz limpia", "Buen diseño", "Ok", "Cumple", "Bien", "Recomendado", "Genial", "Eficaz", "Ayuda visual", "Navegacion", "Informativo", "Sencillo"]
    }
    df = pd.DataFrame(data)

    # Cálculos
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # Generar Figuras para pantalla y PDF
    fig_hist = px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'], title="Distribucion SUS")
    fig_pie = px.pie(df, names='sentimiento', color='sentimiento', title="Analisis de Sentimiento",
                     color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})
    
    textos_validos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    wc = WordCloud(width=800, height=400, background_color="white", colormap='Greens').generate(textos_validos)
    fig_wc, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")

    # --- SIDEBAR: DESCARGA ---
    with st.sidebar:
        st.subheader("📄 Exportar")
        try:
            # Generar los bytes del PDF enviando las figuras actuales
            pdf_bytes = generar_pdf_espejo(promedio_sus, len(df), sent_predom, fig_hist, fig_pie, fig_wc)
            st.download_button(
                label="📥 Descargar PDF Completo",
                data=pdf_bytes,
                file_name=f"Reporte_Usabilidad_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")

    # --- RENDERIZADO DASHBOARD ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}")
    col2.metric("Sentimiento IA", sent_predom)
    col3.metric("Evaluaciones", len(df))

    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_hist, use_container_width=True)
    c2.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("☁️ Nube de Conceptos (IA NLP)")
    st.pyplot(fig_wc)

    st.info("**💡 Resumen:** La usabilidad se mantiene en niveles óptimos.")