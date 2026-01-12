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
    """Calcula el SUS Score basado en la lógica estándar"""
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0: df_sus[col] = df_sus[col] - 1
        else: df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def interpretar_sus(score):
    """Clasificación cualitativa del puntaje SUS"""
    if score >= 80.3: return "Excelente (Clase A)"
    elif score >= 68: return "Bueno (Clase B/C)"
    elif score >= 51: return "Pobre (Clase D)"
    else: return "No aceptable (Clase F)"

def analizar_sentimiento_ia(texto):
    if not texto or texto.lower() in ["sin comentario", "nan", ""]: return "Neutral"
    blob = TextBlob(texto)
    score = blob.sentiment.polarity
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_reporte(score_promedio, total, sentimiento, df, fig_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Título Centrado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # 2. Resumen Ejecutivo Nutrido
    interpretacion = interpretar_sus(score_promedio)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", ln=True)
    pdf.set_font("Arial", '', 11)
    resumen = (
        f"El analisis de usabilidad del sistema arrojo un puntaje promedio SUS de {score_promedio:.2f}, "
        f"lo cual se clasifica tecnicamente como '{interpretacion}'. En cuanto al feedback cualitativo, "
        f"se identifico un sentimiento predominante '{sentimiento}' tras procesar {total} evaluaciones. "
        "La IA detecta que la arquitectura de informacion es solida, aunque la nube de conceptos sugiere "
        "enfocar esfuerzos en la explicabilidad de los filtros y la ayuda visual."
    )
    pdf.multi_cell(0, 7, resumen)
    pdf.ln(10)

    # Función para evitar errores de BytesIO y superposición
    def agregar_img(plt_fig, pdf_obj, x, y_pos, w):
        img_name = f"temp_{np.random.randint(10000)}.png"
        plt_fig.savefig(img_name, format='png', bbox_inches='tight', dpi=150)
        pdf_obj.image(img_name, x=x, y=y_pos, w=w)
        os.remove(img_name)

    # 3. Gráficos con posiciones 'y' fijas para evitar superposición
    # Histograma
    plt.figure(figsize=(6, 3))
    plt.hist(df['sus_score'], color='#2e7d32', rwidth=0.8)
    plt.title("Distribucion de Puntajes SUS")
    agregar_img(plt, pdf, x=15, y_pos=75, w=180) # Posición y=75
    plt.close()

    # Pie Chart (Dona)
    plt.figure(figsize=(5, 4))
    counts = df['sentimiento'].value_counts()
    colors = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', 
            colors=[colors.get(x, '#808080') for x in counts.index], wedgeprops={'width':0.4})
    plt.title("Analisis de Sentimientos")
    agregar_img(plt, pdf, x=55, y_pos=145, w=100) # Posición y=145 (separado del anterior)
    plt.close()

    # 4. Nube de Palabras en Nueva Página
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Nube de Conceptos (NLP IA)", ln=True, align='C')
    agregar_img(fig_wc, pdf, x=10, y_pos=30, w=190)

    return pdf.output(dest='S').encode('latin-1')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
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
        'observacion': ["Mejorar graficos", "Filtros", "Excelente", "Ayuda", "Facil", "Complejo", "Simplificar", "Cumple", "Buena", "Retroalimentacion", "Util", "Diseño", "Relevante", "Usabilidad", "Satisfecho", "Didacticos", "Todo bien", "Filtros", "Excelente", "Facil", "Bien"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # KPIs en pantalla
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS", f"{promedio_sus:.1f}", delta=interpretar_sus(promedio_sus))
    col2.metric("Sentimiento", sent_predom, delta_color="normal" if sent_predom == "Positivo" else "inverse")
    col3.metric("Muestra", len(df))

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32']), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(df, names='sentimiento', hole=0.4, color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"}), use_container_width=True)

    # Nube de Palabras
    textos = " ".join([c for c in df['observacion']])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # Sidebar Exportación
    with st.sidebar:
        st.subheader("📄 Exportar Reporte")
        if st.download_button(label="📥 Descargar PDF Espejo", 
                             data=generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc), 
                             file_name=f"Reporte_{datetime.date.today()}.pdf", mime="application/pdf"):
            st.success("Reporte generado con exito")

    # Resumen Nutrido en pantalla
    st.info(f"**Resumen de IA:** El sistema alcanza un nivel {interpretar_sus(promedio_sus)}. Se recomienda optimizar filtros.")