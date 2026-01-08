import streamlit as st
from supabase import create_client, Client
import datetime
import pytz

# Importaciones de tus módulos locales
from dashboard_rotacion import render_rotacion_dashboard
from encuestas_historial import historial_encuestas_module

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
# 1. GESTIÓN DE SESIÓN (LÓGICA VOLÁTIL POR METADATA)
# ============================================================

def _setup_session(auth_user):
    """Extrae el rol de los metadatos de Auth y define la página inicial."""
    metadata = getattr(auth_user, 'user_metadata', {})
    role = metadata.get("role", "analista").lower()
    
    # Hora del sistema para evitar el N/A en cualquier reporte interno
    if "session_time_pe" not in st.session_state:
        st.session_state["session_time_pe"] = datetime.datetime.now(TIMEZONE_PERU).strftime("%Y-%m-%d %H:%M hrs (PE)")
    
    # REGLA: Al iniciar sesión, ir directo a la página que le corresponde
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
            # Al loguearse con éxito, se configura la sesión y el cargo
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
# 2. INTERFAZ DE ACCESO (LOGIN, REGISTRO, RECUPERAR)
# ============================================================

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
            # Selección de cargo que define el acceso
            reg_role = st.selectbox("Cargo / Puesto", ["analista", "auditor", "admin"])
            reg_pass = st.text_input("Contraseña (mín. 8)", type="password", key="reg_pass_key")
            
            if st.button("Registrarse", use_container_width=True):
                if len(reg_pass) >= 8 and reg_name and reg_email:
                    try:
                        supabase.auth.sign_up({
                            "email": reg_email, 
                            "password": reg_pass,
                            "options": {"data": {"full_name": reg_name, "role": reg_role}}
                        })
                        st.success("✅ Registro enviado. Revisa tu correo.")
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Datos incompletos.")

        with tabs[2]:
            st.subheader("Recuperar Acceso")
            email_reset = st.text_input("Correo registrado", key="reset_email")
            if st.button("Enviar instrucciones", use_container_width=True):
                supabase.auth.reset_password_for_email(email_reset)
                st.info("Correo de recuperación enviado.")

# ============================================================
# 3. SIDEBAR Y NAVEGACIÓN POR CARGO
# ============================================================

def render_sidebar():
    role = st.session_state.get("user_role", "analista")
    current_page = st.session_state.get("current_page")
    
    with st.sidebar:
        st.title(f"👋 {st.session_state.get('full_name', 'User').split(' ')[0]}")
        st.info(f"Acceso: **{role.upper()}**")
        st.markdown("---")
        
        # Filtrar menú lateral según cargo (Sin Mi Perfil)
        menu = []
        if role == "admin":
            menu = ["Dashboard", "Historial de Encuesta"]
        elif role == "analista":
            menu = ["Dashboard"]
        elif role == "auditor":
            menu = ["Historial de Encuesta"]
            
        for p in menu:
            st.button(
                p, 
                use_container_width=True, 
                type="primary" if current_page == p else "secondary",
                on_click=lambda page=p: st.session_state.update({"current_page": page})
            )
        
        st.markdown("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            handle_logout()

# ============================================================
# 4. EJECUCIÓN MAESTRA
# ============================================================

if st.session_state.get("authenticated"):
    if "just_logged_in" in st.session_state: del st.session_state["just_logged_in"]
    
    render_sidebar()
    current = st.session_state.get("current_page")
    
    # Renderizado según la selección
    if current == "Dashboard":
        render_rotacion_dashboard()
    elif current == "Historial de Encuesta":
        historial_encuestas_module()
else:
    # Intento de recuperar sesión persistente
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            _setup_session(session.user)
            st.rerun()
        else: render_auth_page()
    except:
        render_auth_page()