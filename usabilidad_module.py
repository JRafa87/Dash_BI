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
    pos = ['excelente', 'bueno', 'facil', 'util', 'satisfecho', 'bien']
    neg = ['lento', 'error', 'complejo', 'dificil', 'malo', 'engorroso']
    if any(p in texto.lower() for p in pos): score += 0.2
    if any(p in texto.lower() for p in neg): score -= 0.2
    return "Positivo" if score > 0.1 else "Negativo" if score < -0.1 else "Neutral"

# FUNCIÓN PDF MEJORADA CON TÍTULOS Y ANÁLISIS DETALLADO
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "INFORME ESTRATEGICO DE USABILIDAD (SUS & IA)", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 5, f"Fecha de emision: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # KPIs en el PDF
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje Promedio SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Clima de Sentimiento", 1, 0, 'C', True)
    pdf.cell(70, 10, "Usuarios Evaluados", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}/100", 1, 0, 'C')
    pdf.cell(60, 15, f"{sentimiento_dominante}", 1, 0, 'C')
    pdf.cell(70, 15, f"{total}", 1, 1, 'C')
    
    pdf.ln(10)
    
    # Sección de Gráficos con títulos
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(0, 0, 0)
    
    y_start_graphs = pdf.get_y()
    pdf.cell(90, 10, "Distribucion de Puntajes", ln=0)
    pdf.cell(90, 10, "Distribucion de Sentimientos", ln=1)
    
    pdf.image(path_hist, x=10, y=pdf.get_y(), w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y(), w=90)
    
    # Nube de Palabras
    pdf.set_y(pdf.get_y() + 75)
    if path_wc:
        pdf.set_font("Helvetica", 'B', 13)
        pdf.cell(0, 10, "Analisis de Conceptos Clave (NLP)", ln=True)
        pdf.image(path_wc, x=15, w=180)
        pdf.ln(5)

    # --- ANÁLISIS ESTRATÉGICO DETALLADO ---
    pdf.set_y(pdf.get_y() + 60)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, "Interpretacion y Oportunidades de Mejora", ln=True)
    
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    
    # Lógica de análisis dinámico
    analisis_texto = (
        f"El sistema presenta un puntaje SUS de {score_promedio:.1f}, lo que se traduce en una "
        f"aceptabilidad {'Excelente' if score_promedio > 80 else 'Buena' if score_promedio > 70 else 'Marginal'}. "
        f"El sentimiento predominante es {sentimiento_dominante}, validando una percepcion positiva del usuario.\n\n"
        "Oportunidades de Mejora:\n"
        "1. Optimizacion de Navegacion: Los comentarios sugieren simplificar la ubicacion de filtros.\n"
        "2. Explicabilidad: Se detecta la necesidad de agregar descripciones visuales en graficos complejos.\n"
        "3. Retroalimentacion: Reforzar las ayudas visuales para usuarios nuevos."
    )
    
    pdf.multi_cell(0, 7, analisis_texto)
    
    return pdf.output(dest='S').encode('latin-1')

# --- RENDERIZADO DE LA INTERFAZ ---
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
        .stPlotlyChart { margin-top: -20px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

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
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:gray;">Puntaje SUS</p><h1 style="color:#2E7D32;">{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2: 
        color = "#2e7d32" if sent_predom == "Positivo" else "#ffa000"
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Sentimiento IA</p><h1 style="color:{color};">{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:gray;">Usuarios</p><h1 style="color:#1976D2;">{len(df)}</h1></div>', unsafe_allow_html=True)

    # --- GRÁFICOS INTERACTIVOS (PLOTLY) ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Distribución SUS")
        fig = px.histogram(df, x="sus_score", nbins=10, color_discrete_sequence=['#1E3C72'], template="simple_white")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("😊 Clima de Opinión")
        fig2 = px.pie(df, names='sentimiento', color='sentimiento', 
                      color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"}, hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

    # --- NUBE DE PALABRAS ---
    st.markdown("---")
    st.subheader("☁️ Temas Relevantes (NLP)")
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    
    path_wc = None
    if len(textos) > 5:
        wc = WordCloud(width=1000, height=300, background_color="white", colormap='Blues').generate(textos)
        fig_wc, ax = plt.subplots(figsize=(15, 5))
        ax.imshow(wc, interpolation='bilinear'); ax.axis("off")
        st.pyplot(fig_wc)
        
        tmp_w = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig_wc.savefig(tmp_w.name, format='png', bbox_inches='tight')
        path_wc = tmp_w.name
        plt.close(fig_wc)

    # --- PREPARACIÓN IMÁGENES PDF (MATPLOTLIB) ---
    tmp_h = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_h, ax_h = plt.subplots(figsize=(5, 4))
    ax_h.hist(df['sus_score'], bins=10, color='#1E3C72', edgecolor='white')
    ax_h.set_xlabel("Puntaje SUS"); ax_h.set_ylabel("Frecuencia")
    fig_h.savefig(tmp_h.name); path_hist = tmp_h.name; plt.close(fig_h)

    tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_p, ax_p = plt.subplots(figsize=(5, 4))
    counts = df['sentimiento'].value_counts()
    ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#2e7d32", "#ffa000", "#d32f2f"])
    fig_p.savefig(tmp_p.name); path_pie = tmp_p.name; plt.close(fig_p)

    # --- SIDEBAR Y DESCARGA ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1491/1491214.png", width=100)
        st.subheader("Acciones del Sistema")
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc)
        st.download_button(
            label="📥 Descargar Reporte PDF Completo",
            data=pdf_bytes,
            file_name=f"Reporte_IA_SUS_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.info(f"**Análisis Estratégico:** El puntaje de **{promedio_sus:.1f}** indica usabilidad alta. El clima **{sent_predom}** sugiere una adopción exitosa.")

if __name__ == "__main__":
    render_modulo_usabilidad()