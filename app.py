import streamlit as st
from supabase import create_client, Client
import datetime
import pytz
import time

# --- IMPORTACIONES DE MÓDULOS LOCALES ---
# Asegúrate de que estos archivos existan en tu directorio
try:
    from dashboard_rotacion import render_rotacion_dashboard
    from encuestas_historial import historial_encuestas_module
    from usabilidad_module import render_modulo_usabilidad 
    from encuesta_interna import render_formulario_encuesta
except ImportError as e:
    st.error(f"Error al importar módulos: {e}")

# ============================================================
# 0. CONFIGURACIÓN INICIAL
# ============================================================
TIMEZONE_PERU = pytz.timezone("America/Lima")
st.set_page_config(page_title="App Deserción Laboral", layout="wide")

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = get_supabase()

# ============================================================
# 1. GESTIÓN DE SESIÓN (ESTRICTA)
# ============================================================

def _setup_session(auth_user):
    """Establece las variables de sesión solo tras validación exitosa."""
    metadata = getattr(auth_user, 'user_metadata', {})
    role = metadata.get("role", "analista").lower()
    
    st.session_state.update({
        "authenticated": True,
        "user_id": auth_user.id,
        "user_email": auth_user.email,
        "user_role": role,
        "full_name": metadata.get("full_name", auth_user.email.split("@")[0]),
        "session_time_pe": datetime.datetime.now(TIMEZONE_PERU).strftime("%Y-%m-%d %H:%M hrs (PE)")
    })
    
    # Redirección inicial por rol
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Historial de Encuesta" if role == "auditor" else "Dashboard"

def login_callback():
    """Procesa el intento de login."""
    email = st.session_state.get("login_email", "").strip().lower()
    password = st.session_state.get("login_pass", "")
    
    if not email or not password:
        st.session_state.login_error = "Ingresa correo y contraseña."
        return

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res and res.user:
            # Limpiamos errores y configuramos sesión
            if "login_error" in st.session_state: del st.session_state.login_error
            _setup_session(res.user)
        else:
            st.session_state.login_error = "Credenciales incorrectas."
    except Exception:
        st.session_state.login_error = "Error de conexión o credenciales inválidas."

def handle_logout():
    supabase.auth.sign_out()
    # Limpieza total para evitar que la sesión quede "colgada"
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ============================================================
# 2. INTERFAZ DE AUTENTICACIÓN
# ============================================================

def render_password_reset_form():
    st.subheader("🔄 Recuperar Contraseña")
    if "recovery_step" not in st.session_state:
        st.session_state.recovery_step = 1

    if st.session_state.recovery_step == 1:
        with st.form("otp_request"):
            email = st.text_input("Ingresa tu correo institucional")
            if st.form_submit_button("Enviar Código OTP"):
                try:
                    supabase.auth.reset_password_for_email(email.strip().lower())
                    st.session_state.temp_email = email.strip().lower()
                    st.session_state.recovery_step = 2
                    st.rerun()
                except: st.error("Error al enviar el correo.")
    else:
        with st.form("otp_verify"):
            st.info(f"Código enviado a: {st.session_state.temp_email}")
            otp_code = st.text_input("Código OTP")
            new_pass = st.text_input("Nueva contraseña (mín. 8 caracteres)", type="password")
            if st.form_submit_button("Restablecer y volver al Login"):
                try:
                    supabase.auth.verify_otp({
                        "email": st.session_state.temp_email,
                        "token": otp_code.strip(),
                        "type": "recovery"
                    })
                    supabase.auth.update_user({"password": new_pass})
                    st.success("✅ Contraseña actualizada correctamente.")
                    time.sleep(2)
                    # Cumplimos tu instrucción: redirigir a login tras recuperar
                    st.session_state.clear() 
                    st.rerun()
                except: st.error("Código inválido o expirado.")

def render_auth_page():
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("Acceso al Sistema")
        tabs = st.tabs(["🔑 Login", "📝 Registro", "🔄 Recuperar"])
        
        with tabs[0]:
            if "login_error" in st.session_state: 
                st.error(st.session_state.login_error)
            st.text_input("Correo electrónico", key="login_email")
            st.text_input("Contraseña", type="password", key="login_pass")
            st.button("Iniciar Sesión", use_container_width=True, type="primary", on_click=login_callback)
            
        with tabs[1]:
            st.subheader("Nuevo Usuario")
            reg_email = st.text_input("Correo institucional", key="reg_email")
            reg_name = st.text_input("Nombre completo")
            reg_role = st.selectbox("Cargo / Puesto", ["analista", "auditor", "admin"])
            reg_pass = st.text_input("Contraseña", type="password", key="reg_pass_key")
            if st.button("Registrarse", use_container_width=True):
                if len(reg_pass) >= 8 and reg_name and reg_email:
                    try:
                        supabase.auth.sign_up({
                            "email": reg_email, "password": reg_pass,
                            "options": {"data": {"full_name": reg_name, "role": reg_role}}
                        })
                        st.success("✅ Registro enviado. Revisa tu correo para confirmar.")
                    except Exception as e: st.error(f"Error: {e}")
                else:
                    st.warning("Completa todos los campos (Pass mín. 8 caracteres).")
                    
        with tabs[2]:
            render_password_reset_form()

# ============================================================
# 3. SIDEBAR Y NAVEGACIÓN POR ROL
# ============================================================

def render_sidebar():
    role = st.session_state.get("user_role", "analista")
    current_page = st.session_state.get("current_page")

    with st.sidebar:
        st.title(f"👋 {st.session_state.get('full_name', 'User').split(' ')[0]}")
        st.info(f"Cargo: **{role.upper()}**")
        st.caption(f"🕒 {st.session_state.get('session_time_pe')}")
        st.markdown("---")
        
        # Definición de menú según rol
        if role == "admin":
            menu = ["Dashboard", "Historial de Encuesta", "Calificar Dashboard", "Módulo de Usabilidad"]
        elif role == "analista":
            menu = ["Dashboard", "Historial de Encuesta", "Calificar Dashboard"]
        else: # auditor
            menu = ["Historial de Encuesta", "Calificar Dashboard"]
        
        for p in menu:
            if st.button(p, use_container_width=True, type="primary" if current_page == p else "secondary"):
                st.session_state.current_page = p
                st.rerun()
        
        st.markdown("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            handle_logout()

# ============================================================
# 4. LÓGICA DE CONTROL PRINCIPAL
# ============================================================

# Paso 1: Verificar si ya hay una sesión autenticada en el estado de Streamlit
if st.session_state.get("authenticated") is True:
    render_sidebar()
    current = st.session_state.get("current_page")
    role = st.session_state.get("user_role")

    # Ejecución de módulos con protección de ruta
    if current == "Dashboard" and role in ["admin", "analista"]:
        render_rotacion_dashboard()
    elif current == "Historial de Encuesta":
        historial_encuestas_module()
    elif current == "Calificar Dashboard":
        render_formulario_encuesta()
    elif current == "Módulo de Usabilidad" and role == "admin":
        render_modulo_usabilidad()
    else:
        # Si por alguna razón el usuario está en una página no permitida, lo mandamos a la base
        st.warning("No tienes permisos para esta sección.")
        st.session_state.current_page = "Historial de Encuesta"
        st.rerun()

# Paso 2: Si no está autenticado, intentar recuperar de Supabase o mostrar Login
else:
    try:
        # Solo intentamos recuperar sesión si no hay un error de login actual
        if "login_error" not in st.session_state:
            session_resp = supabase.auth.get_session()
            if session_resp and session_resp.session:
                _setup_session(session_resp.session.user)
                st.rerun()
            else:
                render_auth_page()
        else:
            render_auth_page()
    except:
        render_auth_page()