import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
import tempfile
import os

# --- FUNCIONES DE APOYO ---
def limpiar_texto_pdf(texto):
    if not texto: return ""
    return texto.encode('latin-1', 'replace').decode('latin-1')

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

def obtener_oportunidades(df, promedio_sus):
    ops = []
    textos = " ".join(df['observacion'].astype(str)).lower()
    if promedio_sus < 80:
        ops.append({"prioridad": "Alta", "color": (198, 40, 40), "msg": "Optimización de Flujos: El puntaje SUS indica barreras de usabilidad."})
    if any(p in textos for p in ["filtro", "ubicar", "buscar"]):
        ops.append({"prioridad": "Media", "color": (239, 108, 0), "msg": "Interfaz de Búsqueda: Los usuarios reportan dificultad con los filtros."})
    if any(p in textos for p in ["explic", "grafic", "entender"]):
        ops.append({"prioridad": "Media", "color": (239, 108, 0), "msg": "Alfabetización de Datos: Mejorar la interpretación de gráficos."})
    return ops

# --- GENERADOR DE PDF COMPLETO ---
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc, oportunidades, analisis):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, limpiar_texto_pdf("INFORME ESTRATÉGICO DE USABILIDAD (SUS & IA)"), ln=True, align='C')
    pdf.ln(5)
    
    # TABLA DE KPIs (Recuperada)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_fill_color(230, 235, 245)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 10, "Puntaje Promedio SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento Predominante", 1, 0, 'C', True)
    pdf.cell(70, 10, "Muestra Analizada", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f} / 100", 1, 0, 'C')
    pdf.cell(60, 15, limpiar_texto_pdf(sentimiento_dominante), 1, 0, 'C')
    pdf.cell(70, 15, f"{total} Usuarios", 1, 1, 'C')
    pdf.ln(10)
    
    # Gráficos con Títulos
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(95, 10, "Distribucion de Puntajes SUS", 0, 0, 'L')
    pdf.cell(95, 10, "Clima de Opinion (IA)", 0, 1, 'L')
    pdf.image(path_hist, x=10, y=pdf.get_y(), w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y(), w=90)
    pdf.ln(75)
    
    # Nube de Palabras
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Analisis de Conceptos Clave (NLP)", ln=True)
    pdf.image(path_wc, x=15, w=180)
    pdf.ln(65)
    
    # ANÁLISIS ESTRATÉGICO (Recuperado)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, limpiar_texto_pdf("Análisis e Interpretación"), ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, limpiar_texto_pdf(analisis))
    pdf.ln(5)
    
    # Radar de Mejoras
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, "Radar de Oportunidades de Mejora", ln=True)
    pdf.ln(2)
    for op in oportunidades:
        pdf.set_fill_color(*op['color'])
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(25, 8, op['prioridad'], 0, 0, 'C', True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"  {limpiar_texto_pdf(op['msg'])}", 0, 1)
        pdf.ln(1)

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- RENDERIZADO INTERFAZ ---
def render_modulo_usabilidad():
    st.markdown("""
        <style>
        .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .op-card { padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 5px solid; }
        .op-Alta { background-color: #ffebee; border-left-color: #c62828; }
        .op-Media { background-color: #fff3e0; border-left-color: #ef6c00; }
        </style>
    """, unsafe_allow_html=True)

    # Datos (21 registros para asegurar porcentajes de tu imagen)
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
        'observacion': ["Neutral", "Neutral", "Mejorar graficos", "Filtros dificiles", "Excelente", "Neutral", "Neutral"] * 3
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]
    oportunidades = obtener_oportunidades(df, promedio_sus)
    
    analisis_texto = f"El sistema presenta un SUS Score de {promedio_sus:.1f}, lo que lo sitúa en un rango de aceptabilidad alta. El análisis de sentimiento vía IA muestra un clima predominantemente {sent_predom}, aunque se identifican fricciones menores en la localización de filtros y la densidad de datos en gráficos complejos."

    st.markdown("<h1 style='text-align:center; color:#1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)

    # Gráficos en Interfaz (Plotly)
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

    # Nube de Palabras
    st.markdown("---")
    textos_nube = " ".join([o for o in df['observacion'] if o != "Neutral"])
    wc = WordCloud(width=1200, height=400, background_color="white", colormap="Blues", max_words=100).generate(textos_nube)
    fig_w, ax_w = plt.subplots(figsize=(12, 4))
    ax_w.imshow(wc, interpolation='bilinear'); ax_w.axis("off")
    st.pyplot(fig_w)

    # Análisis y Radar
    st.markdown("---")
    st.subheader("📊 Análisis Estratégico")
    st.info(analisis_texto)

    st.subheader("🚀 Radar de Oportunidades")
    for op in oportunidades:
        st.markdown(f'<div class="op-card op-{op["prioridad"]}"><b>{op["prioridad"]}:</b> {op["msg"]}</div>', unsafe_allow_html=True)

    # --- ARCHIVOS TEMPORALES PARA PDF ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as th:
        fig_h, ax_h = plt.subplots(figsize=(5,4)); ax_h.hist(df['sus_score'], color='#1E3C72'); fig_h.savefig(th.name); path_h = th.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tp:
        fig_p, ax_p = plt.subplots(figsize=(5,4)); counts = df['sentimiento'].value_counts()
        ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#ffa000", "#2e7d32", "#d32f2f"]); fig_p.savefig(tp.name); path_p = tp.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tw:
        fig_w.savefig(tw.name); path_w = tw.name

    with st.sidebar:
        pdf_b = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_h, path_p, path_w, oportunidades, analisis_texto)
        st.download_button("📥 Descargar Reporte Completo PDF", data=pdf_b, file_name="Analisis_Estrategico_SUS.pdf", mime="application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()