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
    """Genera PDF robusto inyectando versiones Matplotlib de los gráficos para evitar error de Chrome"""
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado centrado
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Fecha de emision: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.multi_cell(0, 10, f"Puntaje SUS Promedio: {score_promedio:.2f} / 100\n"
                          f"Muestra total: {total} usuarios.\n"
                          f"Sentimiento Predominante: {sentimiento}")
    pdf.ln(5)

    # --- Gráfico 1: Histograma imitando a Plotly ---
    plt.figure(figsize=(6, 3))
    plt.hist(df['sus_score'], color='#2e7d32', rwidth=0.9)
    plt.title("Distribucion SUS")
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png')
    buf1.seek(0) # IMPORTANTE: Rebobinar el buffer
    pdf.image(buf1, x=15, w=180, type='PNG')
    plt.close()

    # --- Gráfica 2: Pie imitando Dona de Plotly ---
    plt.figure(figsize=(5, 3))
    counts = df['sentimiento'].value_counts()
    colors = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', 
            colors=[colors.get(x, '#808080') for x in counts.index], wedgeprops={'width':0.4})
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0) # IMPORTANTE: Rebobinar el buffer
    pdf.image(buf2, x=55, w=100, type='PNG')
    plt.close()

    # --- Nube de Conceptos ---
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis de Conceptos (NLP)", ln=True, align='C')
    buf3 = io.BytesIO()
    fig_wc.savefig(buf3, format='png')
    buf3.seek(0) # IMPORTANTE: Rebobinar el buffer
    pdf.image(buf3, x=10, w=190, type='PNG')

    return pdf.output()

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # TÍTULO CENTRADO CON HTML
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
        'observacion': ["Sin comentario", "Mejorar graficos", "Me costo ubicar filtros", "Excelente sistema", "Agregar ayuda visual", "Facil de entender", "Parece complejo", "Simplificar", "Agregar descripciones", "Cumple su funcion", "Mejorar navegacion", "Buena experiencia", "Retroalimentacion", "Util", "Explicabilidad", "Diseño agradable", "Relevante", "Usabilidad", "Satisfecho", "Didacticos", "Todo bien"]
    }
    df = pd.DataFrame(data)

    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0] if not df.empty else "N/A"

    # --- KPIs CON FORMATO DINÁMICO ---
    col1, col2, col3 = st.columns(3)
    
    # Lógica de color para SUS
    sus_color = "normal" if promedio_sus < 70 else "inverse" # Verde si es alto
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}", delta=None, delta_color=sus_color)
    
    # Lógica de color para Sentimiento
    sent_delta = "Neutral"
    if sent_predom == "Positivo": sent_delta = "Saludable"
    elif sent_predom == "Negativo": sent_delta = "Crítico"
    
    col2.metric("Sentimiento IA", sent_predom, delta=sent_delta, delta_color="normal" if sent_predom == "Positivo" else "inverse")
    col3.metric("Evaluaciones", len(df))

    st.markdown("---")

    # --- GRÁFICOS INTERACTIVOS (STREAMLIT) ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Distribucion de Calificaciones")
        fig_hist = px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'], labels={'sus_score':'Puntaje SUS'})
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        st.subheader("😊 Analisis de Sentimientos")
        fig_pie = px.pie(df, names='sentimiento', hole=0.4, # Hole para estilo dona
                         color='sentimiento',
                         color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("☁️ Nube de Conceptos (IA NLP)")
    
    textos_validos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    if len(textos_validos) > 5:
        wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos_validos)
        ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # --- EXPORTACIÓN SEGURA ---
    with st.sidebar:
        st.subheader("📄 Reporte Ejecutivo")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc)
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_Usabilidad_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error: {e}")

    st.info("**💡 Resumen de Inteligencia Artificial:** Evaluacion finalizada. El sistema detecta una usabilidad aceptable con oportunidades en ayuda visual.")