import streamlit as st
from supabase import create_client, Client

def render_formulario_encuesta():
    # --- ESTILOS CSS AISLADOS ---
    st.markdown("""
        <style>
        /* 1. Botón de Envío: Solo afecta al formulario de encuesta */
        div[data-testid="stForm"] .stButton > button {
            background-color: #2e7d32 !important;
            color: white !important;
            border: none !important;
            padding: 0.75rem 1rem !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-testid="stForm"] .stButton > button:hover {
            background-color: #1b5e20 !important;
            transform: scale(1.01) !important;
        }

        /* 2. Contenedores de Radio Buttons: Diseño de tarjetas limpias */
        div.stRadio {
            background-color: #ffffff;
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #eeeeee;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        /* 3. Alineación Horizontal de las 5 opciones */
        div.stRadio [role="radiogroup"] {
            flex-direction: row !important;
            justify-content: space-between !important;
        }

        /* 4. Encabezados de sección con línea decorativa */
        .section-header {
            font-size: 1.1rem;
            font-weight: bold;
            color: #2e7d32;
            margin-top: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #2e7d32;
            padding-left: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- TÍTULO E INTRODUCCIÓN ---
    st.title("📝 Evaluación de Usabilidad (SUS)")
    st.markdown("Por favor, califica tu experiencia con el Dashboard. **Todos los campos de texto son opcionales.**")

    opciones = {
        "Muy en desacuerdo": 1,
        "En desacuerdo": 2,
        "Neutral": 3,
        "De acuerdo": 4,
        "Muy de acuerdo": 5
    }

    # --- INICIO DEL FORMULARIO ---
    with st.form("encuesta_sus_final", clear_on_submit=True):
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="section-header">✨ Fortalezas del Sistema</div>', unsafe_allow_html=True)
            p1 = st.radio("1. Usaría este Dashboard con frecuencia", opciones.keys(), index=2)
            p3 = st.radio("3. El Dashboard es fácil de usar", opciones.keys(), index=2)
            p5 = st.radio("5. Las funciones están bien integradas", opciones.keys(), index=2)
            p7 = st.radio("7. La gente aprendería a usarlo rápido", opciones.keys(), index=2)
            p9 = st.radio("9. Me sentí confiado usando el Dashboard", opciones.keys(), index=2)

        with col2:
            st.markdown('<div class="section-header">🛠️ Áreas de Mejora</div>', unsafe_allow_html=True)
            p2 = st.radio("2. El Dashboard es innecesariamente complejo", opciones.keys(), index=2)
            p4 = st.radio("4. Necesitaría apoyo técnico para usarlo", opciones.keys(), index=2)
            p6 = st.radio("6. Hay inconsistencias en el sistema", opciones.keys(), index=2)
            p8 = st.radio("8. Es muy engorroso de utilizar", opciones.keys(), index=2)
            p10 = st.radio("10. Tuve que aprender mucho antes de usarlo", opciones.keys(), index=2)

        st.markdown("---")
        
        # CAMPO OPCIONAL: Permitir enviar vacío
        st.subheader("💬 Comentarios adicionales (Opcional)")
        observacion = st.text_area(
            "¿Hay algo más que nos quieras decir?", 
            placeholder="Puedes dejar este espacio en blanco si no tienes comentarios...",
            value="" # Asegura que inicie vacío
        )

        # Botón de envío
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            submit = st.form_submit_button("🚀 Enviar Evaluación")

        if submit:
            try:
                # Conexión a Supabase
                url = st.secrets["SUPABASE_URL"]
                key = st.secrets["SUPABASE_KEY"]
                supabase: Client = create_client(url, key)
                
                # Preparar datos para inserción
                data_insert = {
                    "id_encuesta": "DASHBOARD_GENERAL",
                    "usuario": st.session_state.get('user_email', 'Usuario_Anonimo'),
                    "p1": opciones[p1], "p2": opciones[p2], "p3": opciones[p3],
                    "p4": opciones[p4], "p5": opciones[p5], "p6": opciones[p6],
                    "p7": opciones[p7], "p8": opciones[p8], "p9": opciones[p9],
                    "p10": opciones[p10],
                    "observacion": observacion.strip() if observacion else "Sin comentario"
                }

                # Inserción en Supabase
                supabase.table("encuestas_usabilidad").insert(data_insert).execute()
                
                st.success("✅ ¡Gracias! Tus respuestas han sido enviadas correctamente.")
                st.balloons()
                
            except Exception as e:
                st.error("Hubo un problema al conectar con la base de datos.")
                st.exception(e)