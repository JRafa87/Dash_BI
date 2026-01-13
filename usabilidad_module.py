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
import tempfile
import os

# --- FUNCIONES DE APOYO ---
def calcular_sus(df):
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0:
            df_sus[col] = df_sus[col] - 1
        else:
            df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def analizar_sentimiento_ia(texto):
    if not texto or texto.lower() in ["sin comentario", "nan", ""]:
        return "Neutral"
    blob = TextBlob(texto)
    score = blob.sentiment.polarity
    return "Positivo" if score > 0.1 else "Negativo" if score < -0.1 else "Neutral"

def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO: USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento IA", 1, 0, 'C', True)
    pdf.cell(70, 10, "Muestra Total", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, f"{sentimiento_dominante}", 1, 0, 'C')
    pdf.cell(70, 15, f"{total} usuarios", 1, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis Visual de Metricas", ln=True)
    y_pos = pdf.get_y()
    
    # Inserción de imágenes desde rutas temporales
    pdf.image(path_hist, x=10, y=y_pos, w=90)
    pdf.image(path_pie, x=105, y=y_pos, w=90)
    
    if path_wc:
        pdf.set_y(y_pos + 75)
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos (Temas Relevantes)", ln=True)
        pdf.image(path_wc, x=15, w=180)

    return pdf.output(dest='S').encode('latin-1')

def render_modulo_usabilidad():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
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
        'observacion': ["Excelente"] * 21
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p>Puntaje SUS</p><h1>{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p>Sentimiento IA</p><h1>{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p>Usuarios</p><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

    # Gráficos e Imágenes Temporales
    g1, g2 = st.columns(2)
    
    # 1. Histograma
    with g1:
        st.subheader("📊 Distribución SUS")
        fig_h, ax_h = plt.subplots(figsize=(5, 4))
        ax_h.hist(df['sus_score'], bins=10, color='#1E3C72', edgecolor='white')
        st.pyplot(fig_h)
        
        tmp_h = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig_h.savefig(tmp_h.name, format='png')
        path_hist = tmp_h.name
        plt.close(fig_h)

    # 2. Pie Chart
    with g2:
        st.subheader("😊 Clima de Opinión")
        fig_p, ax_p = plt.subplots(figsize=(5, 4))
        counts = df['sentimiento'].value_counts()
        ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#2e7d32", "#ffa000", "#d32f2f"])
        st.pyplot(fig_p)
        
        tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig_p.savefig(tmp_p.name, format='png')
        path_pie = tmp_p.name
        plt.close(fig_p)

    # 3. Nube de Palabras
    st.subheader("☁️ Temas Relevantes")
    textos = " ".join(df['observacion'])
    wc = WordCloud(width=800, height=400, background_color="white").generate(textos)
    fig_w, ax_w = plt.subplots()
    ax_w.imshow(wc)
    ax_w.axis("off")
    st.pyplot(fig_w)
    
    tmp_w = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_w.savefig(tmp_w.name, format='png')
    path_wc = tmp_w.name
    plt.close(fig_w)

    # Botón en Sidebar
    with st.sidebar:
        st.subheader("Acciones")
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc)
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_bytes,
            file_name="Reporte_SUS.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    render_modulo_usabilidad()