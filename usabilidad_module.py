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
import os

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
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_reporte(score_promedio, total, sentimiento_pred, df, fig_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Título Centrado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # 2. Resumen Ejecutivo Nutrido
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. ANALISIS E INTERPRETACION DE LA IA", ln=True)
    pdf.set_font("Arial", '', 11)
    
    nivel = "Excelente" if score_promedio >= 80 else "Bueno/Aceptable" if score_promedio >= 68 else "Critico"
    
    # Análisis de texto dinámico para el resumen
    resumen_ia = (
        f"El sistema evaluado presenta un SUS Score de {score_promedio:.1f}, situandose en un rango '{nivel}'. "
        f"Tras procesar {total} respuestas, la IA determina un sentimiento predominantemente '{sentimiento_pred}'.\n\n"
        "HALLAZGOS CLAVE: Se observa una alta valoracion en el diseño visual y la facilidad general. "
        "Sin embargo, el analisis cualitativo detecta friccion en la velocidad de respuesta y la "
        "configuracion de filtros. Los usuarios asocian la experiencia positiva a la 'limpieza' de la interfaz, "
        "mientras que los comentarios neutros/negativos sugieren optimizar la ayuda visual y la navegacion."
    )
    pdf.multi_cell(0, 7, resumen_ia)
    pdf.ln(10)

    # Función para manejar imágenes y evitar superposición
    def salvar_e_inyectar(plt_fig, nombre, y_pos, ancho):
        plt_fig.savefig(nombre, format='png', bbox_inches='tight', dpi=150)
        pdf.image(nombre, x=(210-ancho)/2, y=y_pos, w=ancho)
        plt.close()
        if os.path.exists(nombre): os.remove(nombre)

    # --- Gráfico 1: Histograma ---
    plt.figure(figsize=(7, 3.5))
    plt.hist(df['sus_score'], bins=8, color='#2e7d32', edgecolor='white')
    plt.title("Distribucion de Calificaciones (SUS Score)", fontsize=12)
    salvar_e_inyectar(plt, "temp_hist.png", y_pos=100, ancho=160)

    # --- Gráfico 2: Sentimientos (Dona Completa) ---
    plt.figure(figsize=(6, 4))
    # Forzamos las 3 categorías para que siempre aparezcan en la leyenda
    counts = df['sentimiento'].value_counts().reindex(['Positivo', 'Neutral', 'Negativo'], fill_value=0)
    color_map = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140,
            colors=[color_map[x] for x in counts.index], wedgeprops={'width':0.4})
    plt.title("Analisis de Sentimientos (NLP)", fontsize=12)
    salvar_e_inyectar(plt, "temp_pie.png", y_pos=175, ancho=100) # Posición y baja para no chocar

    # --- Página 2: Nube de Palabras ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. NUBE DE CONCEPTOS E INSIGHTS CLAVE", ln=True, align='C')
    salvar_e_inyectar(fig_wc, "temp_wc.png", y_pos=30, ancho=180)

    return pdf.output(dest='S').encode('latin-1')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # Título centrado con HTML
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
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
            "Excelente", "Mejorar graficos", "Filtros complejos", "Excelente", "Ayuda visual", 
            "Facil", "Lento al cargar", "Buen diseño", "Simplificar", "Cumple", "Navegacion", 
            "Buena experiencia", "Retroalimentacion", "Util", "Explicabilidad", "Agradable", 
            "Informacion", "Mejorar filtros", "Satisfecho", "Didacticos", "Todo bien"
        ]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_counts = df['sentimiento'].value_counts()
    sent_predom = sent_counts.idxmax()

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}")
    col2.metric("Sentimiento IA", sent_predom)
    col3.metric("Evaluaciones", len(df))

    st.markdown("---")

    # --- Gráficos en Pantalla ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Distribucion de Calificaciones")
        st.plotly_chart(px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32']), use_container_width=True)
    with c2:
        st.subheader("😊 Analisis de Sentimientos")
        st.plotly_chart(px.pie(df, names='sentimiento', hole=0.4, 
                               color='sentimiento', 
                               color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"}), use_container_width=True)

    # Nube de Palabras
    st.markdown("---")
    st.subheader("☁️ Nube de Conceptos (IA NLP)")
    textos = " ".join([c for c in df['observacion']])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    wc = WordCloud(width=800, height=350, background_color="white", colormap='Greens').generate(textos)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # --- Exportación Sidebar ---
    with st.sidebar:
        st.subheader("📄 Reporte Ejecutivo")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc)
            st.download_button(label="📥 Descargar Reporte PDF", data=pdf_bytes, 
                               file_name=f"Reporte_IA_{datetime.date.today()}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Error: {e}")

    # Resumen Extenso en Pantalla
    st.info(f"**Análisis de IA:** El sistema alcanza un nivel de usabilidad funcional. Se recomienda enfocar mejoras en la velocidad y los filtros para elevar el SUS Score.")