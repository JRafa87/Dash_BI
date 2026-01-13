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

# --- CONFIGURACIÓN DE PÁGINA ---
if 'page_config_done' not in st.session_state:
    st.set_page_config(page_title="Dashboard IA & SUS", layout="wide")
    st.session_state.page_config_done = True

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
    pos = ['excelente', 'bueno', 'facil', 'util', 'satisfecho', 'bien']
    neg = ['lento', 'error', 'complejo', 'dificil', 'malo', 'engorroso']
    if any(p in texto.lower() for p in pos): score += 0.2
    if any(p in texto.lower() for p in neg): score -= 0.2
    return "Positivo" if score > 0.1 else "Negativo" if score < -0.1 else "Neutral"

# FUNCIÓN PDF CORREGIDA CON RUTAS TEMPORALES
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO: USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # KPIs en el PDF
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
    
    # Imágenes
    y_pos = pdf.get_y()
    pdf.image(path_hist, x=10, y=y_pos, w=90)
    pdf.image(path_pie, x=105, y=y_pos, w=90)
    
    if path_wc:
        pdf.set_y(y_pos + 75)
        pdf.image(path_wc, x=15, w=180)
    
    return pdf.output(dest='S').encode('latin-1')

# --- RENDERIZADO DE LA INTERFAZ ---
def render_modulo_usabilidad():
    # Estilo CSS Personalizado (TU DISEÑO)
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stPlotlyChart { margin-top: -20px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Evaluación de experiencia de usuario asistida por NLP</p>", unsafe_allow_html=True)
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
        'observacion': ["Todo bien", "Excelente", "Fácil", "Mejorar", "Rápido"] * 4 + ["Bien"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # --- KPIs CON TU DISEÑO ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Puntaje SUS</p><h1 style="color:#2E7D32;">{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2:
        color = "#2e7d32" if sent_predom == "Positivo" else "#ffa000"
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Sentimiento IA</p><h1 style="color:{color};">{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Usuarios</p><h1 style="color:#1976D2;">{len(df)}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS Y ARCHIVOS TEMPORALES ---
    g1, g2 = st.columns(2)
    
    # Generar Histograma para PDF
    fig_h, ax_h = plt.subplots(figsize=(5, 4))
    ax_h.hist(df['sus_score'], bins=10, color='#1E3C72', edgecolor='white')
    tmp_h = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_h.savefig(tmp_h.name, format='png')
    path_hist = tmp_h.name
    plt.close(fig_h)

    # Generar Pie para PDF
    fig_p, ax_p = plt.subplots(figsize=(5, 4))
    counts = df['sentimiento'].value_counts()
    ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#2e7d32", "#ffa000", "#d32f2f"])
    tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_p.savefig(tmp_p.name, format='png')
    path_pie = tmp_p.name
    plt.close(fig_p)

    with g1:
        st.subheader("📊 Distribución SUS")
        fig = px.histogram(df, x="sus_score", nbins=10, color_discrete_sequence=['#1E3C72'], template="simple_white")
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with g2:
        st.subheader("😊 Clima de Opinión")
        fig2 = px.pie(df, names='sentimiento', color='sentimiento', 
                      color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"},
                      hole=0.4)
        fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig2, use_container_width=True)

    # --- NUBE DE PALABRAS ---
    st.markdown("---")
    st.subheader("☁️ Temas Relevantes (NLP)")
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    path_wc = None
    if len(textos) > 5:
        wc = WordCloud(width=1000, height=300, background_color="white", colormap='Blues').generate(textos)
        fig_wc, ax = plt.subplots(figsize=(15, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)
        
        tmp_w = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig_wc.savefig(tmp_w.name, format='png', bbox_inches='tight')
        path_wc = tmp_w.name
        plt.close(fig_wc)

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1491/1491214.png", width=100)
        st.subheader("Acciones del Sistema")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc)
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_SUS_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error PDF: {e}")

    st.info(f"**Análisis Estratégico:** El puntaje de **{promedio_sus:.1f}** indica que el sistema es altamente usable.")

if __name__ == "__main__":
    render_modulo_usabilidad()