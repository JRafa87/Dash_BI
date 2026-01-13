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
        ops.append({"prioridad": "Alta", "color": (198, 40, 40), "msg": "Revision de flujos criticos: El puntaje SUS sugiere friccion."})
    if any(p in textos for p in ["filtro", "ubicar", "buscar"]):
        ops.append({"prioridad": "Media", "color": (239, 108, 0), "msg": "Optimizacion de Navegacion: Mejorar la ubicacion de filtros."})
    if any(p in textos for p in ["explic", "grafic", "entender"]):
        ops.append({"prioridad": "Media", "color": (239, 108, 0), "msg": "Explicabilidad Visual: Añadir descripciones a graficos."})
    if not ops:
        ops.append({"prioridad": "Baja", "color": (21, 101, 192), "msg": "Mantenimiento: Monitoreo de satisfaccion actual."})
    return ops

# --- GENERADOR DE PDF MEJORADO ---
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, path_hist, path_pie, path_wc, oportunidades, analisis):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, limpiar_texto_pdf("REPORTE ESTRATEGICO: USABILIDAD E IA"), ln=True, align='C')
    pdf.ln(5)
    
    # Gráficos con títulos (Simulando la imagen subida)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(95, 10, "Distribucion SUS", 0, 0, 'L')
    pdf.cell(95, 10, "Clima de Opinion", 0, 1, 'L')
    
    pdf.image(path_hist, x=10, y=pdf.get_y(), w=90)
    pdf.image(path_pie, x=105, y=pdf.get_y(), w=90)
    pdf.ln(75)
    
    # Nube de Palabras
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Temas Relevantes (NLP)", ln=True)
    pdf.image(path_wc, x=15, w=180)
    pdf.ln(65)
    
    # Radar de Mejoras con Diseño
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 10, "Radar de Oportunidades de Mejora", ln=True)
    pdf.ln(2)
    
    for op in oportunidades:
        # Dibujar cajita de color para la prioridad
        pdf.set_fill_color(*op['color'])
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(25, 8, op['prioridad'], 0, 0, 'C', True)
        
        # Texto de la mejora
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"  {limpiar_texto_pdf(op['msg'])}", 0, 1)
        pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFAZ STREAMLIT ---
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

    # Gráficos Plotly (Originales)
    st.markdown("<h1 style='text-align: center; color: #1E3C72;'>🧠 Inteligencia Artificial y Análisis SUS</h1>", unsafe_allow_html=True)
    
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
    textos = " ".join(df['observacion'])
    wc = WordCloud(width=1200, height=400, background_color="white", colormap="Blues").generate(textos)
    fig_w, ax_w = plt.subplots(figsize=(12, 4))
    ax_w.imshow(wc, interpolation='bilinear'); ax_w.axis("off")
    st.pyplot(fig_w)

    # Radar
    st.subheader("🚀 Radar de Oportunidades de Mejora")
    for op in oportunidades:
        st.markdown(f'<div class="op-card op-{op["prioridad"]}"><b>{op["prioridad"]}:</b> {op["msg"]}</div>', unsafe_allow_html=True)

    # --- PREPARAR IMÁGENES PARA EL PDF (MATPLOTLIB) ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_h:
        fig_h, ax_h = plt.subplots(figsize=(5,4))
        ax_h.hist(df['sus_score'], color='#1E3C72', edgecolor='white')
        ax_h.set_title("Distribucion SUS", fontsize=10)
        fig_h.savefig(tmp_h.name); path_hist = tmp_h.name
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p:
        fig_p, ax_p = plt.subplots(figsize=(5,4))
        counts = df['sentimiento'].value_counts()
        # Aquí forzamos que salgan los porcentajes tal cual tu imagen
        ax_p.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=["#ffa000", "#2e7d32", "#d32f2f"], startangle=90)
        ax_p.set_title("Clima de Opinion", fontsize=10)
        fig_p.savefig(tmp_p.name); path_pie = tmp_p.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_w:
        fig_w.savefig(tmp_w.name); path_wc = tmp_w.name

    with st.sidebar:
        pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, path_hist, path_pie, path_wc, oportunidades, "Análisis de usabilidad satisfactorio.")
        st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name="Reporte_Final.pdf", mime="application/pdf")

if __name__ == "__main__":
    render_modulo_usabilidad()