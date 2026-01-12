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
    if score > 0.1: return "Positivo"
    elif score < -0.1: return "Negativo"
    else: return "Neutral"

def render_matplotlib_hist(df):
    """Genera histograma en Matplotlib para evitar usar kaleido"""
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.hist(df['sus_score'], bins=10, color='#2e7d32', edgecolor='white')
    ax.set_title("Distribucion de Puntajes SUS")
    ax.set_xlabel("Puntaje")
    ax.set_ylabel("Frecuencia")
    return fig

def render_matplotlib_pie(df):
    """Genera gráfico de pastel en Matplotlib para evitar usar kaleido"""
    counts = df['sentimiento'].value_counts()
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    ax.pie(counts, labels=counts.index, autopct='%1.1f%%', 
           colors=[colors.get(x, '#666') for x in counts.index])
    ax.set_title("Analisis de Sentimientos")
    return fig

def generar_pdf_reporte(promedio, total, sent, fig_h, fig_p, fig_w, resumen):
    pdf = FPDF()
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 5, f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')} | Muestra: {total} usuarios", ln=True, align='C')
    pdf.ln(10)

    # KPIs con color simulado (rectángulos)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento", 1, 0, 'C', True)
    pdf.cell(70, 10, "Evaluaciones", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 12, f"{promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 12, f"{sent}", 1, 0, 'C')
    pdf.cell(70, 12, f"{total}", 1, 1, 'C')
    pdf.ln(10)

    # Gráficos 1 y 2 (Lado a lado)
    y_charts = pdf.get_y()
    
    buf_h = io.BytesIO()
    fig_h.savefig(buf_h, format='png', bbox_inches='tight')
    pdf.image(buf_h, x=10, y=y_charts, w=90)
    
    buf_p = io.BytesIO()
    fig_p.savefig(buf_p, format='png', bbox_inches='tight')
    pdf.image(buf_p, x=105, y=y_charts, w=90)
    
    pdf.ln(75) # Espacio para los gráficos

    # Gráfico 3: Nube de Palabras
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "3. Nube de Conceptos (NLP):", ln=True)
    buf_w = io.BytesIO()
    fig_w.savefig(buf_w, format='png', bbox_inches='tight')
    pdf.image(buf_w, x=30, w=150)
    
    pdf.ln(10)
    # Resumen Final
    pdf.set_y(pdf.get_y() + 65)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Resumen Ejecutivo de IA:", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 7, resumen)
    
    return pdf.output()

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
    resumen_txt = "La evaluacion promedio indica una usabilidad de nivel 'Aceptable'. La IA identifica que la satisfaccion general es alta, pero el feedback cualitativo sugiere optimizar la explicabilidad de las metricas y mejorar la ayuda visual en los filtros."

    # Interfaz KPIs
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='text-align:center; background:#f0f2f6; padding:10px; border-radius:10px;'><h4>SUS</h4><h2 style='color:#2e7d32;'>{promedio_sus:.1f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center; background:#f0f2f6; padding:10px; border-radius:10px;'><h4>Sentimiento</h4><h2 style='color:#1976d2;'>{sent_predom}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:center; background:#f0f2f6; padding:10px; border-radius:10px;'><h4>Muestra</h4><h2 style='color:#ffa000;'>{len(df)}</h2></div>", unsafe_allow_html=True)

    # Gráficos para la interfaz (Plotly)
    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<h4 style='text-align:center;'>Distribucion SUS</h4>", unsafe_allow_html=True)
        st.plotly_chart(px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32']), use_container_width=True)
    with col_b:
        st.markdown("<h4 style='text-align:center;'>Sentimientos</h4>", unsafe_allow_html=True)
        st.plotly_chart(px.pie(df, names='sentimiento', color_discrete_sequence=px.colors.qualitative.Set2), use_container_width=True)

    # Nube de Palabras
    st.markdown("<h4 style='text-align:center;'>Nube de Conceptos</h4>", unsafe_allow_html=True)
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # Exportación PDF
    with st.sidebar:
        st.subheader("📄 Exportar")
        if st.button("Generar Reporte PDF"):
            # Generamos versiones Matplotlib de los gráficos para el PDF (sin kaleido)
            fig_h = render_matplotlib_hist(df)
            fig_p = render_matplotlib_pie(df)
            
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, fig_h, fig_p, fig_wc, resumen_txt)
            
            st.download_button(
                label="📥 Descargar Reporte",
                data=bytes(pdf_bytes),
                file_name=f"Reporte_UX_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    st.info(f"**💡 Resumen de IA:** {resumen_txt}")

if __name__ == "__main__":
    render_modulo_usabilidad()