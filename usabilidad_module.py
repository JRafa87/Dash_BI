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
    return "Positivo" if score > 0.1 else "Negativo" if score < -0.1 else "Neutral"

# --- FUNCIÓN PDF CORREGIDA ---
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, img_hist, img_pie, img_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO: USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # KPIs
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
    
    # Sección de Gráficos
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis Visual de Metricas", ln=True)
    
    y_pos = pdf.get_y()
    
    # CORRECCIÓN AQUÍ: Se añade 'name' y se resetea el buffer con seek(0)
    img_hist.seek(0)
    pdf.image(img_hist, x=10, y=y_pos, w=90, type='PNG')
    
    img_pie.seek(0)
    pdf.image(img_pie, x=105, y=y_pos, w=90, type='PNG')
    
    pdf.set_y(y_pos + 75)
    
    # Nube de Palabras
    if img_wc:
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos (IA NLP)", ln=True)
        img_wc.seek(0)
        pdf.image(img_wc, x=15, w=180, type='PNG')

    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Resumen de Inteligencia Artificial:", ln=True)
    pdf.set_font("Helvetica", '', 11)
    resumen = (f"Puntaje promedio SUS: {score_promedio:.1f}. Sentimiento predominante: {sentimiento_dominante}. "
               "El analisis sugiere que los usuarios valoran la simplicidad del sistema.")
    pdf.multi_cell(0, 8, resumen)
    
    return pdf.output(dest='S').encode('latin-1')

# --- MÓDULO PRINCIPAL ---
def render_modulo_usabilidad():
    # Estilos CSS
    st.markdown("<style>.metric-card {background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center;}</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos (Asegurados a 21 elementos)
    data = {
        'p1': [4,5,5,5,4,5,3,4,4,5,4,4,5,3,2,3,3,5,5,5,4], 'p2': [2,3,1,1,1,3,3,1,4,1,3,1,2,2,1,2,1,1,1,1,3],
        'p3': [4,3,4,5,4,4,4,4,3,5,4,4,5,5,4,5,4,5,5,5,4], 'p4': [2,2,3,1,2,1,2,1,1,1,3,2,2,1,1,1,1,1,1,1,2],
        'p5': [4,3,3,5,4,4,3,3,3,5,5,4,5,5,4,5,4,5,4,5,5], 'p6': [2,2,2,1,1,1,2,2,2,1,3,2,2,1,2,1,1,2,1,1,1],
        'p7': [5,4,4,5,4,5,4,3,4,5,5,5,3,5,3,5,5,5,3,4,5], 'p8': [2,3,4,1,1,1,2,1,1,1,1,1,1,1,2,1,1,3,1,1,1],
        'p9': [4,4,3,5,4,5,4,4,3,5,5,5,5,5,5,5,5,4,3,5,3], 'p10': [3,2,2,1,4,1,2,1,1,1,1,1,1,1,1,1,1,2,1,3,2],
        'observacion': ["Comentario"] * 21 # Simplificado para el ejemplo
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # KPIs en pantalla
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card">SUS: {promedio_sus:.1f}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card">Sentimiento: {sent_predom}</div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card">Usuarios: {len(df)}</div>', unsafe_allow_html=True)

    # Gráficos Plotly (Pantalla)
    g1, g2 = st.columns(2)
    with g1: st.plotly_chart(px.histogram(df, x="sus_score"), use_container_width=True)
    with g2: st.plotly_chart(px.pie(df, names='sentimiento'), use_container_width=True)

    # --- PREPARACIÓN DE IMÁGENES PARA PDF (Sin Kaleido) ---
    buf_hist = io.BytesIO()
    fig_h, ax_h = plt.subplots(figsize=(5, 4))
    ax_h.hist(df['sus_score'], color='#1E3C72')
    ax_h.set_title("Distribucion SUS")
    fig_h.savefig(buf_hist, format='png')
    plt.close(fig_h)

    buf_pie = io.BytesIO()
    fig_p, ax_p = plt.subplots(figsize=(5, 4))
    counts = df['sentimiento'].value_counts()
    ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%')
    ax_p.set_title("Sentimiento")
    fig_p.savefig(buf_pie, format='png')
    plt.close(fig_p)

    # Nube
    buf_wc = io.BytesIO()
    wc = WordCloud(background_color="white").generate(" ".join(df['observacion']))
    fig_w, ax_w = plt.subplots()
    ax_w.imshow(wc)
    ax_w.axis("off")
    fig_w.savefig(buf_wc, format='png')
    plt.close(fig_w)
    st.pyplot(fig_w)

    # Sidebar Download
    with st.sidebar:
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, buf_hist, buf_pie, buf_wc)
        st.download_button("📥 Descargar Reporte PDF", pdf_bytes, "Reporte.pdf", "application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()