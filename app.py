import streamlit as st
from supabase import create_client, Client
import datetime
import pytz
import time


# Importaciones de tus módulos locales
from dashboard_rotacion import render_rotacion_dashboard
from encuestas_historial import historial_encuestas_module
from usabilidad_module import render_modulo_usabilidad # <--- Nuevo Módulo

# ============================================================
# 0. CONFIGURACIÓN
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
# 1. GESTIÓN DE SESIÓN
# ============================================================

def _setup_session(auth_user):
    metadata = getattr(auth_user, 'user_metadata', {})
    role = metadata.get("role", "analista").lower()
    
    if "session_time_pe" not in st.session_state:
        st.session_state["session_time_pe"] = datetime.datetime.now(TIMEZONE_PERU).strftime("%Y-%m-%d %H:%M hrs (PE)")
    
    # Definición de página inicial por cargo
    if "current_page" not in st.session_state:
        if role == "auditor":
            st.session_state["current_page"] = "Historial de Encuesta"
        else:
            st.session_state["current_page"] = "Dashboard"

    st.session_state.update({
        "authenticated": True,
        "user_id": auth_user.id,
        "user_email": auth_user.email,
        "user_role": role,
        "full_name": metadata.get("full_name", auth_user.email.split("@")[0])
    })

def login_callback():
    email = st.session_state.get("login_email", "").strip().lower()
    password = st.session_state.get("login_pass", "")
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res and res.user:
            _setup_session(res.user)
            st.session_state.just_logged_in = True
        else:
            st.session_state.login_error = "Credenciales incorrectas."
    except:
        st.session_state.login_error = "Error de autenticación."

def handle_logout():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

# ============================================================
# 2. INTERFAZ DE ACCESO (RECUPERACIÓN LIMPITADA)
# ============================================================

def render_password_reset_form():
    st.subheader("🔄 Recuperar Contraseña")
    # Se eliminó la opción "Cambio Directo" por solicitud
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
            otp_code = st.text_input("Código OTP recibido")
            new_pass = st.text_input("Nueva contraseña (mín. 8 caracteres)", type="password")
            if st.form_submit_button("Restablecer y volver al Login"):
                try:
                    supabase.auth.verify_otp({
                        "email": st.session_state.temp_email,
                        "token": otp_code.strip(),
                        "type": "recovery"
                    })
                    supabase.auth.update_user({"password": new_pass})
                    st.success("✅ Contraseña actualizada.")
                    time.sleep(2)
                    st.session_state.clear() # Redirección automática al Login
                    st.rerun()
                except: st.error("Código inválido o expirado.")

def render_auth_page():
    if st.session_state.get("just_logged_in"): return
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("Acceso al Sistema")
        tabs = st.tabs(["🔑 Login", "📝 Registro", "🔄 Recuperar"])
        with tabs[0]:
            if st.session_state.get("login_error"): st.error(st.session_state.login_error)
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
                        st.success("✅ Registro enviado. Revisa tu correo.")
                    except Exception as e: st.error(f"Error: {e}")
        with tabs[2]:
            render_password_reset_form()

# ============================================================
# 3. SIDEBAR CON MENÚ POR ROL
# ============================================================

def render_sidebar():
    role = st.session_state.get("user_role", "analista")
    current_page = st.session_state.get("current_page")

    with st.sidebar:
        st.title(f"👋 {st.session_state.get('full_name', 'User').split(' ')[0]}")
        st.info(f"Cargo: **{role.upper()}**")
        st.caption(f"🕒 {st.session_state.get('session_time_pe')}")
        st.markdown("---")
        
        # Lógica de visibilidad por rol
        menu = []
        if role == "admin":
            menu = ["Dashboard", "Historial de Encuesta", "Módulo de Usabilidad"]
        elif role == "analista":
            menu = ["Dashboard", "Historial de Encuesta"]
        elif role == "auditor":
            menu = ["Historial de Encuesta"]
        
        for p in menu:
            if st.button(p, use_container_width=True, type="primary" if current_page == p else "secondary"):
                st.session_state.current_page = p
                st.rerun()
        
        st.markdown("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            handle_logout()

# ============================================================
# 4. EJECUCIÓN DINÁMICA
# ============================================================

if st.session_state.get("authenticated"):
    if "just_logged_in" in st.session_state: del st.session_state["just_logged_in"]
    render_sidebar()
    current = st.session_state.get("current_page")
    
    # Renderizado condicional
    if current == "Dashboard": 
        render_rotacion_dashboard()
    elif current == "Historial de Encuesta": 
        historial_encuestas_module()
    elif current == "Módulo de Usabilidad" and st.session_state.user_role == "admin":
        render_modulo_usabilidad()
else:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            _setup_session(session.user)
            st.rerun()
        else: render_auth_page()
    except: render_auth_page()