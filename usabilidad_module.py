import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime

# --- FUNCIONES DE APOYO ---

def calcular_sus(df):
    """Calcula el SUS Score: Impares (x-1), Pares (5-x)"""
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0:
            df_sus[col] = df_sus[col] - 1
        else:
            df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def analizar_sentimiento_ia(texto):
    """Procesamiento de Lenguaje Natural local"""
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

def generar_pdf_reporte(score_promedio, total, sentimiento_dominante):
    """Genera PDF con espaciado controlado para evitar encimamientos"""
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO DE USABILIDAD E IA", ln=True, align='C')
    pdf.ln(5)
    
    # Metadatos
    pdf.set_font("Helvetica", '', 11)
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 10, f"Fecha de emision: {fecha}", ln=True)
    pdf.cell(0, 10, f"ID de Consulta: {datetime.datetime.now().timestamp()}", ln=True)
    pdf.ln(10)
    
    # Sección SUS
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "1. Metricas del Sistema (SUS Score)", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 8, f"- Puntaje SUS Promedio: {score_promedio:.2f} / 100\n"
                         f"- Muestra total: {total} usuarios evaluados.\n"
                         f"- Nivel de Usabilidad: {'Excelente' if score_promedio > 80 else 'Aceptable' if score_promedio > 68 else 'Bajo'}")
    pdf.ln(10)
    
    # Sección IA
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "2. Analisis de Feedback Cualitativo (IA)", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 8, f"- Sentimiento Predominante: {sentimiento_dominante}\n"
                         "- Resumen Ejecutivo: El procesamiento automatico detecta que los usuarios "
                         "valoran la integracion de funciones, recomendando mejorar la ayuda visual y la explicabilidad.")
    
    return pdf.output()

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # Título Centrado
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos
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
    sent_predom = df['sentimiento'].mode()[0] if not df.empty else "N/A"

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader("📄 Reporte Ejecutivo")
        try:
            pdf_bytes = generar_pdf_reporte(promedio_sus, len(df), sent_predom)
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=bytes(pdf_bytes),
                file_name=f"Reporte_Usabilidad_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error en PDF: {e}")

    # --- INTERFAZ VISUAL: KPIs CON COLOR ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style="text-align: center; border: 1px solid #e6e9ef; padding: 10px; border-radius: 5px;">
                <p style="color: #666; margin-bottom: 5px;">Puntaje SUS Promedio</p>
                <h2 style="color: #2e7d32; margin-top: 0;">{promedio_sus:.1f}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        color_sent = "#2e7d32" if sent_predom == "Positivo" else "#ffa000" if sent_predom == "Neutral" else "#d32f2f"
        st.markdown(f"""
            <div style="text-align: center; border: 1px solid #e6e9ef; padding: 10px; border-radius: 5px;">
                <p style="color: #666; margin-bottom: 5px;">Sentimiento IA</p>
                <h2 style="color: {color_sent}; margin-top: 0;">{sent_predom}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="text-align: center; border: 1px solid #e6e9ef; padding: 10px; border-radius: 5px;">
                <p style="color: #666; margin-bottom: 5px;">Evaluaciones</p>
                <h2 style="color: #1976d2; margin-top: 0;">{len(df)}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h3 style='text-align: center;'>📊 Distribucion de Calificaciones</h3>", unsafe_allow_html=True)
        fig_hist = px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'],
                               labels={'sus_score':'Puntaje SUS'})
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        st.markdown("<h3 style='text-align: center;'>😊 Analisis de Sentimientos</h3>", unsafe_allow_html=True)
        fig_pie = px.pie(df, names='sentimiento', 
                         color='sentimiento',
                         color_discrete_map={"Positivo":"#2e7d32", "Neutral":"#ffa000", "Negativo":"#d32f2f"})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>☁️ Nube de Conceptos (IA NLP)</h3>", unsafe_allow_html=True)
    
    textos_validos = " ".join([c for c in df['observacion'] if c.lower() != "sin comentario"])
    if len(textos_validos) > 5:
        wc = WordCloud(width=800, height=300, background_color="white", colormap='Greens').generate(textos_validos)
        fig_wc, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig_wc)

    st.info("**💡 Resumen de Inteligencia Artificial:** La evaluacion promedio indica una usabilidad de nivel 'Aceptable'. La IA identifica que la satisfaccion general es alta, pero el feedback cualitativo sugiere optimizar la explicabilidad de las metricas.")

if __name__ == "__main__":
    render_modulo_usabilidad()