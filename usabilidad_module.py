import streamlit as st
import pandas as pd
import plotly.express as px
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF # Librería para generar el PDF
import base64

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf(promedio_sus, total_encuestas, sentimiento_predominante):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Reporte de Usabilidad e IA - Dashboard Rotacion", ln=True, align='C')
    pdf.ln(10)
    
    # Cuerpo del reporte
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Fecha del reporte: {pd.Timestamp.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "1. Metricas de Usabilidad (SUS Score)", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, f"El puntaje promedio obtenido es de {promedio_sus:.2f} sobre 100 puntos.\n"
                         f"Total de usuarios evaluados: {total_encuestas}")
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "2. Analisis de Feedback con IA", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, f"Sentimiento predominante detectado por la IA: {sentimiento_predominante}\n"
                         "Resumen Ejecutivo: Se observa una alta satisfaccion en la integracion de funciones, "
                         "pero se sugiere mejorar la visibilidad de los filtros y la ayuda contextual.")
    
    return pdf.output(dest='S').encode('latin-1')

def render_modulo_usabilidad():
    st.title("🧠 Panel de Usabilidad e IA")
    
    # --- (Aquí va la lógica de carga de datos y cálculos SUS que ya tenemos) ---
    # Simulamos valores para el ejemplo:
    promedio_sus = 78.5
    total_encuestas = 21
    sentimiento_predominante = "Positivo 😊"
    
    # --- SECCIÓN DE DESCARGA ---
    st.sidebar.markdown("### 📄 Exportar Resultados")
    pdf_data = generar_pdf(promedio_sus, total_encuestas, sentimiento_predominante)
    
    st.sidebar.download_button(
        label="📥 Descargar Reporte PDF",
        data=pdf_data,
        file_name="Reporte_Usabilidad_IA.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # --- RESTO DEL DASHBOARD VISUAL ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Puntaje SUS Promedio", f"{promedio_sus}")
    with col2:
        st.metric("Sentimiento IA", sentimiento_predominante)

    # Gráficos (Histogramas y Pie Charts)
    # 
    
    st.markdown("---")
    # Nube de palabras y análisis detallado...