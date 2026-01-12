import streamlit as st
import pandas as pd
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime
import io
from PIL import Image

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
    score = TextBlob(texto).sentiment.polarity
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_avanzado(score_promedio, total, sentimiento, fig_hist, fig_pie, fig_wc):
    """Genera un PDF que incluye las gráficas del dashboard"""
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE EJECUTIVO DE USABILIDAD (REFLEJO DASHBOARD)", ln=True, align='C')
    pdf.ln(5)
    
    # Métricas Principales
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Puntaje SUS: {score_promedio:.1f} | Sentimiento: {sentimiento} | Muestra: {total}", ln=True, align='C')
    pdf.ln(5)

    # --- INSERTAR GRÁFICA DE HISTOGRAMA ---
    # Convertimos la gráfica de Plotly a imagen (Bytes)
    img_hist_bytes = fig_hist.to_image(format="png", width=600, height=350)
    img_hist = Image.open(io.BytesIO(img_hist_bytes))
    img_hist.save("temp_hist.png")
    pdf.image("temp_hist.png", x=10, w=180)
    pdf.ln(5)

    # --- INSERTAR GRÁFICA DE PIE ---
    img_pie_bytes = fig_pie.to_image(format="png", width=600, height=350)
    img_pie = Image.open(io.BytesIO(img_pie_bytes))
    img_pie.save("temp_pie.png")
    pdf.image("temp_pie.png", x=50, w=110)
    
    # --- INSERTAR NUBE DE PALABRAS ---
    if fig_wc:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos Identificados", ln=True, align='C')
        fig_wc.savefig("temp_wc.png", format="png", bbox_inches='tight')
        pdf.image("temp_wc.png", x=10, w=180)

    # Retornar el PDF como bytes de forma segura
    return pdf.output(dest='S')

# --- MÓDULO PRINCIPAL ---

def render_modulo_usabilidad():
    # Título Centrado
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos (Misma estructura de 21 registros)
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
        'observacion': ["Sin comentario", "Mejorar graficos", "Excelente sistema", "Facil", "Lento", "Bien", "Complejo", "Util", "Error", "Bueno", "Mal", "Ok", "Graficos", "Data", "Rapido", "Satisfecho", "Diseño", "Interface", "Flujo", "Ayuda", "Todo bien"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # Crear las figuras primero para poder pasarlas al PDF
    fig_hist = px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'], title="Distribucion SUS")
    fig_pie = px.pie(df, names='sentimiento', color='sentimiento', title="Sentimiento IA",
                     color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})

    # Generar Nube de Palabras
    textos = " ".join([str(c) for c in df['observacion'] if str(c).lower() != "sin comentario"])
    wc = WordCloud(width=800, height=400, background_color="white").generate(textos)
    fig_wc, ax = plt.subplots()
    ax.imshow(wc)
    ax.axis("off")

    # Sidebar con descarga de PDF "Espejo"
    with st.sidebar:
        st.subheader("📄 Reporte Completo")
        try:
            pdf_bytes = generar_pdf_avanzado(promedio_sus, len(df), sent_predom, fig_hist, fig_pie, fig_wc)
            st.download_button(
                label="📥 Descargar Espejo PDF (con Gráficas)",
                data=pdf_bytes,
                file_name="Reporte_Dashboard_Visual.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error exportando gráficas: {e}. Asegúrate de tener 'kaleido' instalado.")

    # Renderizado en pantalla (Streamlit)
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS", f"{promedio_sus:.1f}")
    col2.metric("Sentimiento", sent_predom)
    col3.metric("Evaluaciones", len(df))

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_hist, use_container_width=True)
    c2.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("☁️ Nube de Conceptos")
    st.pyplot(fig_wc)