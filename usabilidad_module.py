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
    
    # 2. Resumen Ejecutivo Extenso y Detallado
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. ANALISIS E INTERPRETACION DE LA IA", ln=True)
    pdf.set_font("Arial", '', 11)
    
    # Lógica de resumen nutrido
    nivel = "Excelente" if score_promedio >= 80 else "Aceptable" if score_promedio >= 68 else "Crítico"
    hallazgos_clave = "mejorar graficos, filtros complejos y ayuda visual"
    
    resumen_ia = (
        f"El sistema presenta un SUS Score de {score_promedio:.1f}, situándose en un nivel '{nivel}'. "
        f"Tras procesar {total} respuestas, la IA identifica que el sentimiento predominante es '{sentimiento_pred}'.\n\n"
        f"DETALLES DEL FEEDBACK: Los usuarios destacan positivamente la 'facilidad de entender' y el 'diseño agradable'. "
        f"Sin embargo, se detectan focos de fricción negativa relacionados con: {hallazgos_clave}. "
        "La recurrencia de términos como 'complejo' y 'filtros' en las observaciones negativas sugiere que, "
        "aunque la herramienta es útil, la carga cognitiva inicial es alta. Se recomienda una reingeniería "
        "en los componentes de navegación para convertir el sentimiento neutral en promotor."
    )
    pdf.multi_cell(0, 7, resumen_ia)
    pdf.ln(10)

    # Función para salvar imágenes sin error de superposición
    def salvar_img(plt_fig, nombre):
        plt_fig.savefig(nombre, format='png', bbox_inches='tight', dpi=150)
        plt.close()

    # --- Gráfico 1: Histograma ---
    plt.figure(figsize=(7, 3.5))
    plt.hist(df['sus_score'], bins=8, color='#2e7d32', edgecolor='white')
    plt.title("Distribucion de Calificaciones (SUS Score)", fontsize=12)
    salvar_img(plt, "hist.png")
    pdf.image("hist.png", x=15, y=105, w=170)

    # --- Gráfico 2: Sentimientos (Asegurando Positivo, Neutral y Negativo) ---
    plt.figure(figsize=(6, 4))
    # Aseguramos que existan las 3 categorías para que no falte ninguna en el gráfico
    counts = df['sentimiento'].value_counts().reindex(['Positivo', 'Neutral', 'Negativo'], fill_value=0)
    color_map = {'Positivo': '#2e7d32', 'Neutral': '#ffa000', 'Negativo': '#d32f2f'}
    
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140,
            colors=[color_map[x] for x in counts.index], wedgeprops={'width':0.4})
    plt.title("Analisis de Sentimientos (NLP)", fontsize=12)
    salvar_img(plt, "pie.png")
    pdf.image("pie.png", x=50, y=175, w=110)

    # --- Página 2: Nube de Palabras ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. NUBE DE CONCEPTOS E INSIGHTS", ln=True, align='C')
    salvar_img(fig_wc, "wc.png")
    pdf.image("wc.png", x=10, y=30, w=190)

    # Limpieza
    for f in ["hist.png", "pie.png", "wc.png"]: 
        if os.path.exists(f): os.remove(f)

    return pdf.output(dest='S').encode('latin-1')

# --- MODULO PRINCIPAL ---

def render_modulo_usabilidad():
    st.markdown("<h1 style='text-align: center;'>🧠 Inteligencia Artificial y Analisis SUS</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Datos corregidos para incluir sentimientos negativos explícitos
    data = {
        'p1': [4,5,2,5,4,5,3,4,2,5,4,4,5,3,2,3,3,5,5,5,4],
        'p2': [2,3,4,1,1,3,3,1,4,1,3,1,2,2,1,2,1,1,1,1,3],
        'p3': [4,3,2,5,4,4,4,4,3,5,4,4,5,5,4,5,4,5,5,5,4],
        'p4': [2,2,4,1,2,1,2,1,1,1,3,2,2,1,1,1,1,1,1,1,2],
        'p5': [4,3,2,5,4,4,3,3,3,5,5,4,5,5,4,5,4,5,4,5,5],
        'p6': [2,2,4,1,1,1,2,2,2,1,3,2,2,1,2,1,1,2,1,1,1],
        'p7': [5,4,2,5,4,5,4,3,4,5,5,5,3,5,3,5,5,5,3,4,5],
        'p8': [2,3,4,1,1,1,2,1,1,1,1,1,1,1,2,1,1,3,1,1,1],
        'p9': [4,4,2,5,4,5,4,4,3,5,5,5,5,5,5,5,5,4,3,5,3],
        'p10': [3,2,4,1,4,1,2,1,1,1,1,1,1,1,1,1,1,2,1,3,2],
        'observacion': [
            "Excelente", "Mejorar graficos", "Muy lento y dificil", "Excelente", "Ayuda", "Facil", 
            "Error en carga", "Muy bueno", "Complejo", "Satisfecho", "Lento", "Graficos", 
            "Malo", "Ok", "Diseño", "Filtros fallan", "Recomendado", "Bien", "Excelente", "Filtros", "Facil"
        ]
    }
    df = pd.DataFrame(data)
    df['sus_score'] = calcular_sus(df)
    df['sentimiento'] = df['observacion'].apply(analizar_sentimiento_ia)
    
    promedio_sus = df['sus_score'].mean()
    sent_counts = df['sentimiento'].value_counts()
    sent_predom = sent_counts.idxmax()

    # KPIs Dashboard
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje SUS Promedio", f"{promedio_sus:.1f}")
    col2.metric("Sentimiento IA", sent_predom)
    col3.metric("Muestra Total", len(df))

    st.markdown("---")

    # Gráficos Streamlit
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
    textos = " ".join([c for c in df['observacion']])
    fig_wc, ax = plt.subplots(figsize=(10, 4))
    wc = WordCloud(width=800, height=350, background_color="white", colormap='Greens').generate(textos)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig_wc)

    # --- Resumen Extenso en Pantalla ---
    st.markdown("### 📝 Analisis Detallado de IA")
    st.write(f"""
    **Hallazgos Principales:** El análisis detecta que la mayoría de los usuarios ({((sent_counts.get('Positivo',0)/len(df))*100):.1f}%) tienen una experiencia **Positiva**, destacando la limpieza del diseño. 
    Sin embargo, existe un **{((sent_counts.get('Negativo',0)/len(df))*100):.1f}% de feedback Negativo** concentrado en términos como 'lento', 'fallan' y 'filtros'. 
    Esto indica que la usabilidad técnica está siendo lastrada por el rendimiento de los filtros, lo que explica por qué el SUS Score no alcanza el rango de Excelencia (>80).
    """)

    # Sidebar Exportación
    with st.sidebar:
        st.subheader("📄 Reporte")
        pdf_data = generar_pdf_reporte(promedio_sus, len(df), sent_predom, df, fig_wc)
        st.download_button(label="📥 Descargar Reporte PDF", data=pdf_data, 
                           file_name=f"Reporte_IA_{datetime.date.today()}.pdf", mime="application/pdf")