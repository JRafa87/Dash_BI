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

# --- FUNCIONES DE APOYO ---

def calcular_sus(df):
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0: df_sus[col] = df_sus[col] - 1
        else: df_sus[col] = 5 - df_sus[col]
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
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def generar_pdf_reporte(score_promedio, total, sentimiento, df, fig_wc):
    # Usamos fpdf estándar
    pdf = FPDF()
    pdf.add_page()
    
    # Título centrado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.multi_cell(0, 10, f"Puntaje SUS Promedio: {score_promedio:.2f} / 100\n"
                          f"Muestra total: {total} usuarios.\n"
                          f"Sentimiento Predominante: {sentimiento}")
    pdf.ln(5)

    # --- Función interna para procesar imágenes sin error startswith ---
    def agregar_img_matplotlib(plt_fig, pdf_obj, x, y, w):
        buf = io.BytesIO()
        plt_fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        # Guardar temporalmente para evitar el error de BytesIO en versiones antiguas de fpdf
        img_name = f"temp_{np.random.randint(1000)}.png"
        with open(img_name, "wb") as f:
            f.write(buf.read())
        pdf_obj.image(img_name, x=x, y=y, w=w)
        import os
        os.remove(img_name)

    # --- Gráfico 1: Histograma ---
    plt.figure(figsize=(6, 3))
    plt.hist(df['sus_score'], color='#2e7d32', rwidth=0.8)
    plt.title("Distribucion SUS")
    agregar_img_matplotlib(plt, pdf, x=15, y=70, w=180)
    plt.close()

    # --- Gráfica 2: Pie (Dona) ---
    plt.figure(figsize=(5, 4))
    counts = df['sentimiento'].value_counts()
    colors = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', 
            colors=[colors.get(x, '#808080') for x in counts.index], wedgeprops={'width':0.4})
    agregar_img_matplotlib(plt, pdf, x=55, y=140, w=100)
    plt.close()

    # --- Nube de Conceptos ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Analisis de Conceptos (NLP)", ln=True, align='C')
    agregar_img_matplotlib(fig_wc, pdf, x=10, y=30, w=190)

    return pdf.output(dest='S').encode('latin-1')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # 1. TÍTULO CENTRADO
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
        'observacion': ["Excelente", "Mejorar graficos", "Filtros", "Excelente", "Ayuda", "Facil", "Complejo", "Simplificar", "Descripciones", "Cumple", "Navegacion", "Buena", "Retroalimentacion", "Util", "Explicabilidad", "Diseño", "Relevante", "Usabilidad", "Satisfecho", "Didacticos", "Todo bien"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # --- KPIs CON FORMATO ---
    col1, col2, col3 = st.columns(3)
    
    # Color métrica SUS
    sus_delta = f"{promedio_sus - 68:.1f}" # Comparado con la media industrial de 68
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}", delta=sus_delta, delta_color="normal" if promedio_sus >= 70 else "inverse")
    
    # Color métrica Sentimiento
    sent_color = "normal" if sent_predom == "Positivo" else "off" if sent_predom == "Neutral" else "inverse"
    col2.metric("Sentimiento IA", sent_predom, delta="Predominante", delta_color=sent_color)
    
    col3.metric("Evaluaciones", len(df))

    st.markdown("---")

    # --- GRÁFICOS INTERACTIVOS (PANTALLA) ---
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
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # --- EXPORTACIÓN ---
    with st.sidebar:
        st.subheader("📄 Reporte")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc)
            st.download_button(label="📥 Descargar Reporte PDF", data=pdf_bytes, 
                               file_name=f"Reporte_{datetime.date.today()}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Error: {e}")

    st.info("**💡 Resumen IA:** La usabilidad se mantiene en niveles altos.")