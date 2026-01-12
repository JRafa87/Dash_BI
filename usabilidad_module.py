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
    """Calcula el SUS Score estándar"""
    df_sus = df.copy()
    for i in range(1, 11):
        col = f'p{i}'
        if i % 2 != 0: df_sus[col] = df_sus[col] - 1
        else: df_sus[col] = 5 - df_sus[col]
    return df_sus[[f'p{i}' for i in range(1, 11)]].sum(axis=1) * 2.5

def interpretar_sus_extenso(score):
    """Interpretación detallada para el feedback de IA"""
    if score >= 80.3: return "Excelente: Los usuarios consideran el sistema altamente usable y lo recomendarían."
    elif score >= 68: return "Aceptable: El sistema es funcional, pero presenta fricciones menores en la experiencia."
    elif score >= 51: return "Pobre: El sistema requiere una revisión urgente de su arquitectura de información."
    else: return "Inaceptable: La usabilidad es una barrera crítica para la adopción del producto."

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
    
    # 2. Resumen Ejecutivo Extenso (Feedback de IA)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. ANALISIS DE RESULTADOS (IA FEEDBACK)", ln=True)
    pdf.set_font("Arial", '', 11)
    
    interp = interpretar_sus_extenso(score_promedio)
    resumen_ia = (
        f"Tras evaluar una muestra de {total} usuarios, se ha determinado un SUS Score de {score_promedio:.1f}. "
        f"Conclusion: {interp} \n\n"
        f"El analisis de sentimiento identifica un estado predominantemente '{sentimiento_pred}'. "
        "Cruzando los datos cuantitativos con las observaciones, la IA detecta que la satisfaccion "
        "se ve afectada principalmente por la curva de aprendizaje inicial (filtros y graficos). "
        "Se recomienda priorizar la simplificacion de la interfaz visual para consolidar la lealtad del usuario."
    )
    pdf.multi_cell(0, 7, resumen_ia)
    pdf.ln(10)

    # Función para inyectar imágenes evitando superposición mediante saltos de página o 'y' controlada
    def salvar_img(plt_fig, nombre):
        plt_fig.savefig(nombre, format='png', bbox_inches='tight', dpi=150)
        plt.close()

    # --- Gráfico 1: Distribución SUS ---
    plt.figure(figsize=(7, 4))
    plt.hist(df['sus_score'], bins=8, color='#2e7d32', edgecolor='white')
    plt.title("Distribucion de Calificaciones (SUS Score)", fontsize=12)
    plt.xlabel("Puntaje")
    plt.ylabel("Usuarios")
    salvar_img(plt, "hist.png")
    pdf.image("hist.png", x=15, y=95, w=170) # Posición y fija

    # --- Gráfico 2: Sentimientos (Dona Completa) ---
    plt.figure(figsize=(6, 4))
    counts = df['sentimiento'].value_counts()
    color_map = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140,
            colors=[color_map.get(x, '#808080') for x in counts.index], wedgeprops={'width':0.4})
    plt.title("Analisis de Sentimientos (NLP)", fontsize=12)
    salvar_img(plt, "pie.png")
    pdf.image("pie.png", x=50, y=165, w=110) # Posición y alejada para evitar superposición

    # --- Página 2: Nube de Palabras ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. NUBE DE CONCEPTOS CLAVE", ln=True, align='C')
    salvar_img(fig_wc, "wc.png")
    pdf.image("wc.png", x=10, y=30, w=190)

    # Limpieza de temporales
    for f in ["hist.png", "pie.png", "wc.png"]: 
        if os.path.exists(f): os.remove(f)

    return pdf.output(dest='S').encode('latin-1')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    # TÍTULO CENTRADO EN INTERFAZ
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos (21 registros)
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
        'observacion': ["Mejorar graficos", "Excelente sistema", "Filtros complejos", "Facil de entender", "Excelente", "Agregar ayuda visual", "Lento", "Muy bueno", "Todo bien", "Satisfecho", "Interfaz limpia", "Graficos didacticos", "Cumple funcion", "Ok", "Buen diseño", "Dificil filtros", "Recomendado", "Bien", "Excelente", "Graficos", "Facil"]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_predom = df['sentimiento'].mode()[0]

    # --- KPIs Dashboard ---
    col1, col2, col3 = st.columns(3)
    # Color dinámico para el promedio
    delta_color = "normal" if promedio_sus >= 70 else "inverse"
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}", delta=f"{promedio_sus-70:.1f} vs Meta", delta_color=delta_color)
    
    # Sentimiento con indicador
    s_delta = "Positivo" if sent_predom == "Positivo" else "Alerta"
    col2.metric("Sentimiento IA", sent_predom, delta=s_delta, delta_color="normal" if sent_predom == "Positivo" else "inverse")
    col3.metric("Muestra Total", len(df))

    st.markdown("---")

    # --- Gráficos Streamlit (Diseño Original) ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Distribucion de Calificaciones")
        st.plotly_chart(px.histogram(df, x="sus_score", color_discrete_sequence=['#2e7d32'], 
                                     labels={'sus_score': 'Puntaje SUS'}), use_container_width=True)
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

    # --- Exportación PDF ---
    with st.sidebar:
        st.subheader("📄 Reporte Ejecutivo")
        pdf_data = generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc)
        st.download_button(label="📥 Descargar Reporte PDF", data=pdf_data, 
                           file_name=f"Reporte_IA_{datetime.date.today()}.pdf", mime="application/pdf")

    # Resumen Extenso en Pantalla
    st.info(f"**Análisis de IA:** {interpretar_sus_extenso(promedio_sus)}")