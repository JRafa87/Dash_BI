import streamlit as st
from supabase import create_client, Client

def render_formulario_encuesta():
    st.header("📝 Encuesta de Satisfacción (SUS)")
    st.write("Tu opinión nos ayuda a mejorar la herramienta. Por favor, sé honesto.")

    # Diccionario de conversión: Lo que el usuario ve vs lo que la tabla recibe
    opciones = {
        "Muy en desacuerdo": 1,
        "En desacuerdo": 2,
        "Ni de acuerdo ni en desacuerdo": 3,
        "De acuerdo": 4,
        "Muy de acuerdo": 5
    }

    with st.form("encuesta_sus"):
        st.subheader("Califica las siguientes afirmaciones:")
        
        # Creamos las 10 preguntas con Radio Buttons
        p1 = st.radio("1. Considero que usaría este Dashboard con frecuencia", opciones.keys(), index=2, horizontal=True)
        p2 = st.radio("2. Encontré el Dashboard innecesariamente complejo", opciones.keys(), index=2, horizontal=True)
        p3 = st.radio("3. Pensé que el Dashboard era fácil de usar", opciones.keys(), index=2, horizontal=True)
        p4 = st.radio("4. Creo que necesitaría apoyo técnico para poder utilizarlo", opciones.keys(), index=2, horizontal=True)
        p5 = st.radio("5. Encontré que las funciones del dashboard estaban bien integradas", opciones.keys(), index=2, horizontal=True)
        p6 = st.radio("6. Pensé que había demasiada inconsistencia en este Dashboard", opciones.keys(), index=2, horizontal=True)
        p7 = st.radio("7. Imagino que la mayoría de la gente aprendería a usarlo muy rápido", opciones.keys(), index=2, horizontal=True)
        p8 = st.radio("8. Encontré el Dashboard muy engorroso de utilizar", opciones.keys(), index=2, horizontal=True)
        p9 = st.radio("9. Me sentí muy confiado al usar el Dashboard", opciones.keys(), index=2, horizontal=True)
        p10 = st.radio("10. Necesité aprender muchas cosas antes de poder seguir con el dashboard", opciones.keys(), index=2, horizontal=True)
        
        st.write("---")
        observacion = st.text_area("¿Tienes algún comentario adicional o sugerencia de mejora?")

        submit = st.form_submit_button("Enviar Encuesta")

        if submit:
            # Conexión a Supabase
            supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            
            # Preparamos la data convirtiendo el texto a número usando el diccionario 'opciones'
            data_insert = {
                "usuario": st.session_state.get('user_email', 'Anonimo'),
                "p1": opciones[p1], "p2": opciones[p2], "p3": opciones[p3],
                "p4": opciones[p4], "p5": opciones[p5], "p6": opciones[p6],
                "p7": opciones[p7], "p8": opciones[p8], "p9": opciones[p9],
                "p10": opciones[p10],
                "observacion": observacion
            }

            try:
                supabase.table("encuestas_usabilidad").insert(data_insert).execute()
                st.success("✅ ¡Gracias! Tu feedback ha sido registrado exitosamente.")
                st.balloons()
            except Exception as e:
                st.error(f"Hubo un error al guardar: {e}")