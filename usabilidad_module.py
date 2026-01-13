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
    pos = ['excelente', 'bueno', 'facil', 'util', 'satisfecho', 'bien']
    neg = ['lento', 'error', 'complejo', 'dificil', 'malo', 'engorroso']
    if any(p in texto.lower() for p in pos): score += 0.2
    if any(p in texto.lower() for p in neg): score -= 0.2
    return "Positivo" if score > 0.1 else "Negativo" if score < -0.1 else "Neutral"

def obtener_oportunidades(df, promedio_sus):
    ops = []
    textos = " ".join(df['observacion'].astype(str)).lower()
    if promedio_sus < 75:
        ops.append({"prioridad": "Alta", "msg": "Revisión de flujos críticos: El puntaje SUS sugiere fricción en la experiencia."})
    if any(p in textos for p in ["filtro", "ubicar", "buscar"]):
        ops.append({"prioridad": "Media", "msg": "Optimización de Navegación: Los usuarios sugieren mejorar la ubicación de filtros."})
    if any(p in textos for p in ["explic", "grafic", "entender"]):
        ops.append({"prioridad": "Media", "msg": "Explicabilidad Visual: Se recomienda añadir descripciones a los gráficos complejos."})
    if not ops:
        ops.append({"prioridad": "Baja", "msg": "Mantenimiento: Continuar con el monitoreo de satisfacción actual."})
    return ops

def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc, oportunidades, analisis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, limpiar_texto_pdf("REPORTE ESTRATEGICO: USABILIDAD E IA"), ln=True, align='C')
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento IA", 1, 0, 'C', True)
    pdf.cell(70, 10, "Muestra Total", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, limpiar_texto_pdf(sentimiento_dominante), 1, 0, 'C')
    pdf.cell(70, 15, f"{total} usuarios", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.image(path_hist, x=10, w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y()-68, w=90)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis de Conceptos Clave", ln=True)
    pdf.image(path_wc, x=15, w=180)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, limpiar_texto_pdf("Interpretación Estratégica"), ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 7, limpiar_texto_pdf(analisis))
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Radar de Mejoras", ln=True)
    for op in oportunidades:
        pdf.multi_cell(0, 7, limpiar_texto_pdf(f"- [{op['prioridad']}] {op['msg']}"))
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFAZ ---
def render_modulo_usabilidad():
    st.markdown("""
        <style>
        .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .op-card { padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 6px solid; }
        .op-Alta { background-color: #ffebee; border-left-color: #c62828; }
        .op-Media { background-color: #fff3e0; border-left-color: #ef6c00; }
        .op-Baja { background-color: #e3f2fd; border-left-color: #1565c0; }
        .stPlotlyChart { margin-top: -20px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Evaluación de experiencia de usuario asistida por NLP</p>", unsafe_allow_html=True)
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
    oportunidades = obtener_oportunidades(df, promedio_sus)
    analisis_texto = f"El puntaje de {promedio_sus:.1f} indica que el sistema es altamente usable. El sentimiento predominante {sent_predom} valida la adopción positiva de la IA por parte de los usuarios, aunque existen áreas de oportunidad en la navegación."

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:gray;">Puntaje SUS</p><h1 style="color:#2E7D32;">{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2:
        color = "#2e7d32" if sent_predom == "Positivo" else "#ffa000"
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Sentimiento IA</p><h1 style="color:{color};">{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:gray;">Usuarios</p><h1 style="color:#1976D2;">{len(df)}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS (DISEÑO ORIGINAL) ---
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Distribución SUS")
        fig = px.histogram(df, x="sus_score", nbins=10, color_discrete_sequence=['#1E3C72'], template="simple_white")
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("😊 Clima de Opinión")
        fig2 = px.pie(df, names='sentimiento', color='sentimiento', 
                      color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"}, hole=0.4)
        fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig2, use_container_width=True)

    # --- NUBE DE PALABRAS (ANCHO COMPLETO) ---
    st.markdown("---")
    st.subheader("☁️ Temas Relevantes (NLP)")
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    fig_wc, ax = plt.subplots(figsize=(15, 5))
    if len(textos) > 5:
        wc = WordCloud(width=1000, height=300, background_color="white", colormap='Blues').generate(textos)
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)

    # --- ANÁLISIS Y RADAR ---
    st.markdown("---")
    st.subheader("📊 Análisis Estratégico")
    st.info(analisis_texto)

    st.subheader("🚀 Radar de Oportunidades de Mejora")
    for op in oportunidades:
        st.markdown(f'<div class="op-card op-{op["prioridad"]}"><b>{op["prioridad"]}:</b> {op["msg"]}</div>', unsafe_allow_html=True)

    # --- GENERACIÓN IMÁGENES PDF ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_h:
        fig_h, ax_h = plt.subplots(figsize=(5,4)); ax_h.hist(df['sus_score'], color='#1E3C72'); fig_h.savefig(tmp_h.name); path_hist = tmp_h.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p:
        fig_p, ax_p = plt.subplots(figsize=(5,4)); counts = df['sentimiento'].value_counts()
        ax_p.pie(counts, labels=counts.index, colors=["#2e7d32", "#ffa000", "#d32f2f"]); fig_p.savefig(tmp_p.name); path_pie = tmp_p.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_w:
        fig_wc.savefig(tmp_w.name); path_wc = tmp_w.name

    with st.sidebar:
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc, oportunidades, analisis_texto)
        st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name="Reporte_SUS.pdf", mime="application/pdf", use_container_width=True)

if __name__ == "__main__":
    render_modulo_usabilidad()