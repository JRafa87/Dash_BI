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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard IA & SUS", layout="wide")

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

# ACTUALIZADO: Ahora recibe las imágenes de los gráficos y la nube
def generar_pdf_reporte(score_promedio, total, sentimiento_dominante, img_hist, img_pie, img_wc):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 70, 120)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO: USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # KPIs en el PDF
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Puntaje SUS", 1, 0, 'C', True)
    pdf.cell(60, 10, "Sentimiento IA", 1, 0, 'C', True)
    pdf.cell(70, 10, "Muestra Total", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(60, 15, f"{score_promedio:.1f}", 1, 0, 'C')
    pdf.cell(60, 15, f"{sentimiento_dominante}", 1, 0, 'C')
    pdf.cell(70, 15, f"{total} usuarios", 1, 1, 'C')
    
    pdf.ln(10)
    
    # Gráficos (Mismo orden que en pantalla)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analisis Visual de Metricas", ln=True)
    
    # Posicionar Histogram y Pie lado a lado
    y_antes_graficos = pdf.get_y()
    pdf.image(img_hist, x=10, y=y_antes_graficos, w=90)
    pdf.image(img_pie, x=105, y=y_antes_graficos, w=90)
    
    pdf.set_y(y_antes_graficos + 75) # Espacio para que no se encime el texto
    
    # Nube de Palabras
    if img_wc:
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Nube de Conceptos (Temas Relevantes)", ln=True)
        pdf.image(img_wc, x=15, w=180)

    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Resumen Estrategico:", ln=True)
    pdf.set_font("Helvetica", '', 11)
    resumen_texto = (f"El sistema presenta un puntaje SUS de {score_promedio:.1f}, "
                     f"con un sentimiento predominantemente {sentimiento_dominante}. "
                     "La IA identifica una satisfaccion alta con oportunidades en la explicabilidad.")
    pdf.multi_cell(0, 8, resumen_texto)
    
    return pdf.output(dest='S').encode('latin-1')

# --- RENDERIZADO DE LA INTERFAZ ---
def render_modulo_usabilidad():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
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

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Puntaje SUS</p><h1 style="color:#2E7D32;">{promedio_sus:.1f}</h1></div>', unsafe_allow_html=True)
    with c2:
        color = "#2e7d32" if sent_predom == "Positivo" else "#ffa000"
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Sentimiento IA</p><h1 style="color:{color};">{sent_predom}</h1></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><p style="color:gray;">Usuarios</p><h1 style="color:#1976D2;">{len(df)}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS (Captura de imágenes para el PDF) ---
    g1, g2 = st.columns(2)
    
    # Generar Figuras
    fig = px.histogram(df, x="sus_score", nbins=10, color_discrete_sequence=['#1E3C72'], template="simple_white")
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
    
    fig2 = px.pie(df, names='sentimiento', color='sentimiento', 
                  color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"},
                  hole=0.4)
    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)

    # Renderizar en Streamlit
    with g1:
        st.subheader("📊 Distribución SUS")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("😊 Clima de Opinión")
        st.plotly_chart(fig2, use_container_width=True)

    # --- NUBE DE PALABRAS ---
    st.markdown("---")
    st.subheader("☁️ Temas Relevantes (NLP)")
    textos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    
    img_wc_bytes = None
    if len(textos) > 5:
        wc = WordCloud(width=1000, height=300, background_color="white", colormap='Blues').generate(textos)
        fig_wc, ax = plt.subplots(figsize=(15, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)
        
        # Guardar nube para el PDF
        tmp_wc = io.BytesIO()
        fig_wc.savefig(tmp_wc, format='png', bbox_inches='tight')
        img_wc_bytes = tmp_wc

    # --- SIDEBAR (Procesamiento del PDF) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1491/1491214.png", width=100)
        st.subheader("Acciones del Sistema")
        try:
            # Convertir gráficos de Plotly a bytes (Imagen)
            img_hist_bytes = io.BytesIO(fig.to_image(format="png"))
            img_pie_bytes = io.BytesIO(fig2.to_image(format="png"))
            
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom, img_hist_bytes, img_pie_bytes, img_wc_bytes)
            
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_SUS_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error PDF: {e}. Asegúrate de tener 'kaleido' instalado.")

    st.info(f"**Análisis Estratégico:** El puntaje de **{promedio_sus:.1f}** indica que el sistema es altamente usable. El sentimiento predominante **{sent_predom}** valida la adopción positiva de la IA por parte de los usuarios.")

if __name__ == "__main__":
    render_modulo_usabilidad()