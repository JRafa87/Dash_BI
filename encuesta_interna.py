import streamlit as st
from supabase import create_client, Client

def render_formulario_encuesta():
    # Estilo CSS personalizado para mejorar la apariencia de los radio buttons y el contenedor
    st.markdown("""
        <style>
        /* Estilo para que los radio buttons se vean horizontales y centrados */
        .stRadio [role="radiogroup"] {
            flex-direction: row;
            justify-content: flex-start;
            gap: 10px;
        }
        /* Contenedor con borde suave para cada pregunta */
        div.stRadio {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e6e6e6;
            margin-bottom: 10px;
        }
        /* Estilo del botón de enviar */
        div.stButton > button:first-child {
            background-color: #2e7d32;
            color: white;
            height: 3em;
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📝 Evaluación de Experiencia de Usuario")
    st.write("Tu feedback es anónimo y nos ayuda a mejorar las herramientas de análisis. Por favor, califica según tu percepción.")

    # Diccionario de conversión: Lo que el usuario selecciona vs el valor numérico
    opciones = {
        "Muy en desacuerdo": 1,
        "En desacuerdo": 2,
        "Neutral": 3,
        "De acuerdo": 4,
        "Muy de acuerdo": 5
    }

    with st.form("encuesta_sus_mejorada", clear_on_submit=True):
        # Usamos columnas para que no sea una lista infinita hacia abajo
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.markdown("### ✨ Fortalezas")
            p1 = st.radio("1. Usaría este Dashboard con frecuencia", opciones.keys(), index=2)
            p3 = st.radio("3. El Dashboard es fácil de usar", opciones.keys(), index=2)
            p5 = st.radio("5. Las funciones están bien integradas", opciones.keys(), index=2)
            p7 = st.radio("7. La gente aprendería a usarlo rápido", opciones.keys(), index=2)
            p9 = st.radio("9. Me sentí confiado usando el Dashboard", opciones.keys(), index=2)

        with col2:
            st.markdown("### 🛠️ Áreas de Mejora")
            p2 = st.radio("2. El Dashboard es innecesariamente complejo", opciones.keys(), index=2)
            p4 = st.radio("4. Necesitaría apoyo técnico para usarlo", opciones.keys(), index=2)
            p6 = st.radio("6. Hay inconsistencias en el sistema", opciones.keys(), index=2)
            p8 = st.radio("8. Es muy engorroso de utilizar", opciones.keys(), index=2)
            p10 = st.radio("10. Tuve que aprender mucho antes de usarlo", opciones.keys(), index=2)

        st.markdown("---")
        st.subheader("💬 Comentarios Adicionales")
        observacion = st.text_area("¿Qué cambiarías o agregarías para que esta herramienta sea más útil?", 
                                   placeholder="Escribe aquí tus sugerencias...")

        # Botón de envío destacado
        submit = st.form_submit_button("Enviar Evaluación Final")

        if submit:
            # Conexión a Supabase
            try:
                url = st.secrets["SUPABASE_URL"]
                key = st.secrets["SUPABASE_KEY"]
                supabase: Client = create_client(url, key)
                
                # Conversión y preparación de datos
                data_insert = {
                    "id_encuesta": "DASHBOARD_GENERAL", # Identificador persistente
                    "usuario": st.session_state.get('user_email', 'Anonimo'),
                    "p1": opciones[p1], "p2": opciones[p2], "p3": opciones[p3],
                    "p4": opciones[p4], "p5": opciones[p5], "p6": opciones[p6],
                    "p7": opciones[p7], "p8": opciones[p8], "p9": opciones[p9],
                    "p10": opciones[p10],
                    "observacion": observacion
                }

                # Inserción en la tabla
                supabase.table("encuestas_usabilidad").insert(data_insert).execute()
                
                st.success(f"✅ ¡Muchas gracias! Tu opinión ha sido guardada.")
                st.balloons()
            except Exception as e:
                st.error(f"Error técnico al guardar: {e}")