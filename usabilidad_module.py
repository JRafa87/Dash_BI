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
    if promedio_sus < 75:
        ops.append({"prioridad": "Alta", "msg": "Revisión de flujos críticos: El puntaje SUS sugiere fricción en la experiencia."})
    if any(palabra in textos for palabra in ["filtro", "ubicar", "buscar"]):
        ops.append({"prioridad": "Media", "msg": "Optimización de Navegación: Los usuarios sugieren mejorar la ubicación de filtros y búsquedas."})
    if any(palabra in textos for palabra in ["explic", "grafic", "entender"]):
        ops.append({"prioridad": "Media", "msg": "Explicabilidad Visual: Se recomienda añadir descripciones o guías a los gráficos."})
    if not ops:
        ops.append({"prioridad": "Baja", "msg": "Mantenimiento: Continuar con el monitoreo de satisfacción actual."})
    return ops

# --- FUNCIÓN PDF CORREGIDA ---
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc, oportunidades, analisis_estrategico):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, limpiar_texto_pdf("REPORTE ESTRATEGICO DE USABILIDAD E IA"), ln=True, align='C')
    pdf.ln(5)
    
    # KPIs
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento", 1, 0, 'C', True)
    pdf.cell(70, 10, "Muestra Total", 1, 1, 'C', True)
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, limpiar_texto_pdf(sentimiento_dominante), 1, 0, 'C')
    pdf.cell(70, 15, f"{total} usuarios", 1, 1, 'C')
    pdf.ln(10)
    
    # Gráficos de distribución
    pdf.image(path_hist, x=10, y=pdf.get_y(), w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y(), w=90)
    pdf.ln(75)

    # Nube de Palabras (Ancho completo)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis de Conceptos Clave (NLP)", ln=True)
    pdf.image(path_wc, x=15, w=180)
    pdf.ln(65)

    # Análisis Estratégico
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, limpiar_texto_pdf("Interpretación Estratégica"), ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, limpiar_texto_pdf(analisis_estrategico))
    pdf.ln(5)

    # Radar de Mejora
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, "Radar de Oportunidades de Mejora", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    for op in oportunidades:
        linea = f"- [{op['prioridad']}] {op['msg']}"
        pdf.multi_cell(0, 7, limpiar_texto_pdf(linea))
    
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
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos originales (21 registros)
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
        'observacion': ["Mejorar graficos", "Filtros dificiles", "Muy bueno", "Excelente", "Falta guia visual"] * 4 + ["Todo bien"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]
    oportunidades = obtener_oportunidades(df, promedio_sus)
    
    analisis_estrategico = f"El sistema alcanza un SUS de {promedio_sus:.1f}. La IA detecta un clima {sent_predom}. Aunque la usabilidad es buena, el feedback sugiere que la optimización de elementos visuales y de filtrado elevaría la experiencia al siguiente nivel."

    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p>Puntaje SUS</p><h1>{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p>Sentimiento IA</p><h1>{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p>Usuarios</p><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

    # Gráficos Distribución
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1: st.plotly_chart(px.histogram(df, x="sus_score", title="Distribución de Puntajes", template="simple_white"), use_container_width=True)
    with g2: st.plotly_chart(px.pie(df, names='sentimiento', title="Clima de Opinión", hole=0.4), use_container_width=True)

    # NUBE DE PALABRAS (ANCHO COMPLETO)
    st.markdown("---")
    st.subheader("☁️ Nube de Conceptos Relevantes")
    textos = " ".join(df['observacion'])
    wc = WordCloud(width=1200, height=400, background_color="white", colormap="Blues").generate(textos)
    fig_w, ax_w = plt.subplots(figsize=(12, 4))
    ax_w.imshow(wc, interpolation='bilinear'); ax_w.axis("off")
    st.pyplot(fig_w)
    
    # Análisis Estratégico
    st.markdown("---")
    st.subheader("📊 Análisis Estratégico")
    st.info(analisis_estrategico)

    # Radar de Mejora
    st.subheader("🚀 Radar de Oportunidades de Mejora")
    for op in oportunidades:
        st.markdown(f'<div class="op-card op-{op["prioridad"]}"><b>{op["prioridad"]}:</b> {op["msg"]}</div>', unsafe_allow_html=True)

    # --- ARCHIVOS TEMPORALES PARA PDF ---
    tmp_h = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); fig_h, ax_h = plt.subplots(); ax_h.hist(df['sus_score']); fig_h.savefig(tmp_h.name); plt.close(fig_h)
    tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); fig_p, ax_p = plt.subplots(); counts = df['sentimiento'].value_counts(); ax_p.pie(counts, labels=counts.index); fig_p.savefig(tmp_p.name); plt.close(fig_p)
    tmp_w = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); fig_w.savefig(tmp_w.name); plt.close(fig_w)

    with st.sidebar:
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, tmp_h.name, tmp_p.name, tmp_w.name, oportunidades, analisis_estrategico)
        st.download_button("📥 Descargar Reporte Completo PDF", data=pdf_bytes, file_name="Reporte_Final_SUS.pdf", mime="application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()