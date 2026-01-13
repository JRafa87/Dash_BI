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

def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, fig_hist, fig_pie, fig_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. TÍTULO
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO: IA Y USABILIDAD", ln=True, align='C')
    pdf.ln(5)

    # 2. KPIs (Tarjetas)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento IA", 1, 0, 'C', True)
    pdf.cell(70, 10, "Evaluaciones", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, f"{sentimiento_dominante}", 1, 0, 'C')
    pdf.cell(70, 15, f"{total}", 1, 1, 'C')
    pdf.ln(10)

    # 3. GRÁFICOS (Capturando las imágenes de Plotly)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Graficos de Analisis", ln=True)
    
    # Convertir Histogram a Imagen
    img_hist = fig_hist.to_image(format="png")
    pdf.image(io.BytesIO(img_hist), x=10, y=pdf.get_y(), w=90)
    
    # Convertir Pie a Imagen
    img_pie = fig_pie.to_image(format="png")
    pdf.image(io.BytesIO(img_pie), x=105, y=pdf.get_y(), w=90)
    
    pdf.ln(65) # Espacio para las imágenes

    # 4. NUBE DE PALABRAS
    if fig_wc:
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos (IA)", ln=True)
        # Guardar el gráfico de Matplotlib (nube) en un buffer
        buf = io.BytesIO()
        fig_wc.savefig(buf, format='png', bbox_inches='tight')
        pdf.image(buf, x=30, w=150)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ STREAMLIT ---

def render_modulo_usabilidad():
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)

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
        'observacion': ["Sin comentario", "Mejorar graficos", "Excelente sistema", "Facil de entender", "Simplificar", "Buena experiencia", "Todo bien", "Estoy satisfecho"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Puntaje SUS", f"{promedio_sus:.1f}")
    c2.metric("Sentimiento IA", sent_predom)
    c3.metric("Evaluaciones", len(df))

    # --- GRÁFICOS (Los guardamos en variables para el PDF) ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_hist = px.histogram(df, x="sus_score", title="Distribución SUS", color_discrete_sequence=['#2E7D32'])
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col_g2:
        fig_pie = px.pie(df, names='sentimiento', title="Sentimiento", color='sentimiento',
                         color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- NUBE DE PALABRAS ---
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    if len(textos) > 5:
        wc = WordCloud(width=800, height=300, background_color="white").generate(textos)
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)

    # --- BOTÓN DE DESCARGA EN SIDEBAR ---
    with st.sidebar:
        st.subheader("📄 Exportar")
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, fig_hist, fig_pie, fig_wc)
        st.download_button("📥 Descargar Reporte Completo", pdf_bytes, "Reporte.pdf", "application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()