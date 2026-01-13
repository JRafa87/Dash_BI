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

def obtener_oportunidades(df, promedio_sus):
    ops = []
    textos = " ".join(df['observacion'].astype(str)).lower()
    
    if promedio_sus < 70:
        ops.append("🔴 **Prioridad Alta:** El puntaje SUS está por debajo del estándar (70). Se requiere una revisión urgente del flujo de usuario.")
    
    if "filtro" in textos or "ubicar" in textos:
        ops.append("🔍 **Optimización de Filtros:** Los usuarios reportan dificultad para segmentar información. Simplificar la barra de búsqueda.")
    
    if "explic" in textos or "grafic" in textos:
        ops.append("📊 **Mejora en Visualización:** Se detecta necesidad de leyendas más claras o tooltips en los gráficos dinámicos.")
    
    if "lento" in textos or "espera" in textos:
        ops.append("⚡ **Rendimiento:** Optimizar tiempos de carga en procesos críticos mencionados por el feedback.")
    
    if not ops:
        ops.append("✅ **Mantenimiento Preventivo:** No se detectan fricciones críticas. Continuar con el monitoreo actual.")
        
    return ops

# --- FUNCIÓN PDF ---
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc, oportunidades):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "INFORME ESTRATEGICO DE USABILIDAD (SUS & IA)", ln=True, align='C')
    pdf.ln(5)
    
    # KPIs
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento", 1, 0, 'C', True)
    pdf.cell(70, 10, "Usuarios", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, f"{sentimiento_dominante}", 1, 0, 'C')
    pdf.cell(70, 15, f"{total}", 1, 1, 'C')
    pdf.ln(10)
    
    # Gráficos
    pdf.set_font("Helvetica", 'B', 13)
    pdf.cell(90, 10, "Distribucion de Puntajes", ln=0)
    pdf.cell(90, 10, "Clima de Opinion", ln=1)
    pdf.image(path_hist, x=10, y=pdf.get_y(), w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y(), w=90)
    
    # Oportunidades en PDF
    pdf.set_y(pdf.get_y() + 75)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, "Oportunidades de Mejora Detectadas", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    
    for op in oportunidades:
        pdf.multi_cell(0, 8, f"- {op.replace('**', '')}")
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
def render_modulo_usabilidad():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff; padding: 20px; border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center;
        }
        .opportunity-card {
            background-color: #f8f9fa; padding: 15px; border-left: 5px solid #1E3C72;
            margin-bottom: 10px; border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos (Mantenemos tus 21 registros)
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

    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p>Puntaje SUS</p><h1 style="color:#2E7D32;">{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p>Sentimiento IA</p><h1 style="color:#ffa000;">{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p>Muestra</p><h1 style="color:#1976D2;">{len(df)}</h1></div>', unsafe_allow_html=True)

    # Gráficos e Imágenes para PDF
    g1, g2 = st.columns(2)
    
    tmp_h = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_h, ax_h = plt.subplots(figsize=(5,4)); ax_h.hist(df['sus_score'], color='#1E3C72')
    fig_h.savefig(tmp_h.name); path_hist = tmp_h.name; plt.close(fig_h)

    tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_p, ax_p = plt.subplots(figsize=(5,4)); counts = df['sentimiento'].value_counts()
    ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#2e7d32", "#ffa000", "#d32f2f"])
    fig_p.savefig(tmp_p.name); path_pie = tmp_p.name; plt.close(fig_p)

    with g1: st.plotly_chart(px.histogram(df, x="sus_score", template="simple_white", title="Distribución SUS"), use_container_width=True)
    with g2: st.plotly_chart(px.pie(df, names='sentimiento', hole=0.4, title="Clima de Opinión"), use_container_width=True)

    # Nube y Oportunidades
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("☁️ Nube de Conceptos")
        textos = " ".join(df['observacion'])
        wc = WordCloud(background_color="white", colormap="Blues").generate(textos)
        fig_w, ax_w = plt.subplots(); ax_w.imshow(wc); ax_w.axis("off")
        st.pyplot(fig_w)
        tmp_w = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig_w.savefig(tmp_w.name); path_wc = tmp_w.name; plt.close(fig_w)

    with col_b:
        st.subheader("🚀 Radar de Oportunidades (IA)")
        for op in oportunidades:
            st.markdown(f'<div class="opportunity-card">{op}</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Reporte Ejecutivo")
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc, oportunidades)
        st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name="Analisis_IA.pdf", mime="application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()