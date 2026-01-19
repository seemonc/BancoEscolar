import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os

# ==========================================
# 1. DETECTOR INTELIGENTE DE IMAGEN
# ==========================================
def obtener_logo():
    nombres_posibles = ["logo.png", "logo.png.png", "Logo.png", "escudo.png", "imagen.png"]
    for nombre in nombres_posibles:
        if os.path.exists(nombre):
            return nombre
    return None

archivo_logo = obtener_logo()

# Configuración de página
if archivo_logo:
    try:
        st.set_page_config(page_title="Banco Summerhill", page_icon=archivo_logo, layout="wide")
    except:
        st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")
else:
    st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")

# ==========================================
# 2. CONFIGURACIÓN GENERAL
# ==========================================
ROLES_ADMINISTRATIVOS = ['admin', 'profesor', 'director', 'administrativo']
CATALOGO_MULTAS = {
    "Incumplimiento de Tarea": 200, "Interrupción de Clase": 150,
    "Falta de Respeto (Verbal)": 500, "Uso de Celular": 100,
    "Área sucia": 50, "Daño a Material": 300
}

# ==========================================
# 3. BASE DE DATOS
# ==========================================
def get_connection():
    return sqlite3.connect('banco_escolar.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, rol TEXT, saldo REAL, password TEXT, email TEXT,
                  grado TEXT, grupo TEXT)''') 
    
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, tipo TEXT)''')
    
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN grado TEXT")
        c.execute("ALTER TABLE usuarios ADD COLUMN grupo TEXT")
        c.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
    except:
        pass

    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  ('admin', 'admin', 1000000, '1234', 'admin@summerhill.edu', '', ''))
        conn.commit()
    conn.close()

# ==========================================
# 4. LÓGICA DEL SISTEMA
# ==========================================
def login(usuario, password):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM usuarios WHERE nombre=? AND password=?", conn, params=(usuario, password))
    conn.close()
    return df

def crear_usuario(nombre, rol, password, email, grado, grupo):
    conn = get_connection()
    c = conn.cursor()
    saldo_inicial = 1000000 if rol in ROLES_ADMINISTRATIVOS else 0
    try:
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (nombre, rol, saldo_inicial, password, email, grado, grupo))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def eliminar_usuario(nombre_usuario):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM usuarios WHERE nombre=?", (nombre_usuario,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def limpiar_historial_completo():
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM transacciones")
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def ejecutar_transaccion(remitente, destinatario, monto, concepto, tipo):
    conn = get_connection()
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE nombre = ?", (monto, remitente))
        c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nombre = ?", (monto, destinatario))
        c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                  (fecha, remitente, destinatario, monto, concepto, tipo))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ==========================================
# 5. INTERFAZ GRÁFICA
# ==========================================
init_db()

# --- PANTALLA DE LOGIN ---
if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        if archivo_logo:
            st.image(archivo_logo, width=200)
        else:
            st.markdown("<h1>🏦</h1>", unsafe_allow_html=True)

        st.markdown("<h1 style='text-align: center;'>Banco Summerhill</h1>", unsafe_allow_html=True)
        st.info("Sistema Financiero Escolar")
        
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", use_container_width=True):
            df = login(user, pw)
            if not df.empty:
                st.session_state['usuario'] = user
                st.session_state['rol'] = df.iloc[0]['rol']
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

else:
    # --- BARRA LATERAL ---
    conn = get_connection()
    try:
        saldo_admin = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]['saldo']
    except:
        saldo_admin = 0
    conn.close()

    with st.sidebar:
        if archivo_logo:
            st.image(archivo_logo, width=120)
        st.markdown(f"## 👤 {st.session_state['usuario']}")
        st.caption(f"Rol: {st.session_state['rol'].upper()}")
        st.metric("💰 MI SALDO", f"${saldo_admin:,.2f}")
        st.divider()
        if st.button("Cerrar Sesión", type="primary"):
            del st.session_state['usuario']
            st.rerun()

    # --- VISTA DIRECTIVOS ---
    if st.session_state['rol'] in ROLES_ADMINISTRATIVOS:
        st.title("Panel de Dirección - Summerhill")
        
        tab1, tab2, tab3 = st.tabs(["⚡ Operaciones", "👥 Gestión", "📊 Historial"])

        # --- TAB 1: OPERACIONES ---
        with tab1:
            st.markdown("### 🔍 Buscador de Alumnos")
            conn = get_connection()
            df_full = pd.read_sql("SELECT nombre, grado, grupo, saldo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()

            if df_full.empty:
                st.warning("⚠️ No hay alumnos registrados.")
            else:
                c_fil1, c_fil2, c_fil3 = st.columns(3)
                l_grados = ["Todos"] + sorted([x for x in df_full['grado'].unique() if x])
                l_grupos = ["Todos"] + sorted([x for x in df_full['grupo'].unique() if x])
                
                filtro_grado = c_fil1.selectbox("Grado", l_grados)
                filtro_grupo = c_fil2.selectbox("Grupo", l_grupos)
                busqueda = c_fil3.text_input("Buscar Nombre")

                df_f = df_full.copy()
                if filtro_grado != "Todos": df_f = df_f[df_f['grado'] == filtro_grado]
                if filtro_grupo != "Todos": df_f = df_f[df_f['grupo'] == filtro_grupo]
                if busqueda: df_f = df_f[df_f['nombre'].str.contains(busqueda, case=False)]

                st.divider()
                op_mode = st.radio("Modo:", ["Individual", "Selección Múltiple"], horizontal=True)

                if op_mode == "Individual":
                    lst = df_f['nombre'].tolist()
                    if lst:
                        c_i1, c_i2 = st.columns(2)
                        with c_i1:
                            st.error("🚨 Cobrar Multa")
                            u_s = st.selectbox("Alumno", lst, key="us")
                            m_s = st.selectbox("Motivo", list(CATALOGO_MULTAS.keys()), key="ms")
                            if st.button("Aplicar Multa"):
                                ejecutar_transaccion(u_s, st.session_state['usuario'], CATALOGO_MULTAS[m_s], m_s, "multa")
                                st.toast(f"Cobrado a {u_s}", icon="✅")
                                time.sleep(1)
                                st.rerun()
                        with c_i2:
                            st.success("💵 Pagar Estímulo")
                            u_p = st.selectbox("Alumno", lst, key="up")
                            a_p = st.number_input("Monto", 50, key="ap")
                            if st.button("Aplicar Pago"):
                                ejecutar_transaccion(st.session_state['usuario'], u_p, a_p, "Pago", "ingreso")
                                st.toast(f"Pagado a {u_p}", icon="✅")
                                time.sleep(1)
                                st.rerun()
                else:
                    st.info("Marca las casillas de los alumnos:")
                    df_f.insert(0, "Sel", False)
                    res = st.data_editor(df_f, column_config={"Sel": st.column_config.CheckboxColumn("Elegir", default=False)}, disabled=["nombre","grado","grupo","saldo"], hide_index=True, use_container_width=True)
                    sel = res[res["Sel"] == True]["nombre"].tolist()
                    
                    if sel:
                        c_m1, c_m2 = st.columns(2)
                        with c_m1:
                            m_m = st.selectbox("Motivo Masivo", list(CATALOGO_MULTAS.keys()), key="mm")
                            if st.button(f"Multar a {len(sel)} Alumnos"):
                                for u in sel: ejecutar_transaccion(u, st.session_state['usuario'], CATALOGO_MULTAS[m_m], m_m, "multa")
                                st.success("Multas aplicadas")
                                time.sleep(1)
                                st.rerun()
                        with c_m2:
                            if st.button(f"Pagar a {len(sel)} Alumnos"):
                                for u in sel: ejecutar_transaccion(st.session_state['usuario'], u, 50, "Beca", "ingreso")
                                st.success("Pagos aplicados")
                                time.sleep(1)
                                st.rerun()

        # --- TAB 2: GESTIÓN (AQUÍ ESTÁ EL ARREGLO) ---
        with tab2:
            st.header("Gestión")
            with st.expander("➕ Nuevo Usuario", expanded=True): # Lo puse abierto por defecto para que lo veas
                with st.form("new"):
                    c1, c2 = st.columns(2)
                    n = c1.text_input("Nombre de Usuario (Único)")
                    p = c2.text_input("Contraseña", "1234")
                    
                    # --- AQUÍ ESTÁ EL SELECTOR DE ROL NUEVO ---
                    c3, c4, c5 = st.columns(3)
                    r_rol = c3.selectbox("Rol", ["alumno", "profesor", "director", "administrativo"])
                    g_grado = c4.text_input("Grado (solo alumnos)")
                    g_grupo = c5.text_input("Grupo (solo alumnos)")
                    
                    if st.form_submit_button("Crear Usuario"):
                        # Ahora pasamos la variable 'r_rol' en vez de "alumno" fijo
                        if crear_usuario(n, r_rol, p, "", g_grado, g_grupo):
                            st.success(f"Usuario {n} creado como {r_rol}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Ese usuario ya existe.")
            
            with st.expander("📂 Carga Masiva (CSV)", expanded=False):
                st.markdown("Sube un archivo CSV con columnas: `nombre`, `rol` (alumno), `password`, `grado`, `grupo`")
                up = st.file_uploader("Subir archivo CSV", type="csv")
                if up:
                    df = pd.read_csv(up)
                    if st.button("Procesar Archivo"):
                        for _, row in df.iterrows():
                            mail = row.get('email', '')
                            gr = row.get('grado', '')
                            gp = row.get('grupo', '')
                            crear_usuario(row['nombre'], row['rol'], str(row['password']), mail, str(gr), str(gp))
                        st.success("Usuarios cargados exitosamente.")
                        time.sleep(1)
                        st.rerun()
            
            conn = get_connection()
            df_u = pd.read_sql("SELECT id, nombre, rol, password, grado, grupo FROM usuarios", conn)
            conn.close()
            ed = st.data_editor(df_u, hide_index=True, use_container_width=True)
            if st.button("Guardar Cambios"):
                conn = get_connection()
                c = conn.cursor()
                for _, r in ed.iterrows():
                    c.execute("UPDATE usuarios SET nombre=?, password=?, rol=?, grado=?, grupo=? WHERE id=?", (r['nombre'], r['password'], r['rol'], r['grado'], r['grupo'], r['id']))
                conn.commit()
                conn.close()
                st.rerun()

        # --- TAB 3: HISTORIAL ---
        with tab3:
            st.subheader("Historial")
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()
            if st.button("🗑️ BORRAR HISTORIAL", type="primary"):
                limpiar_historial_completo()
                st.rerun()

    else:
        # --- VISTA ALUMNO ---
        conn = get_connection()
        data = pd.read_sql("SELECT saldo, grado, grupo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
        conn.close()
        st.metric(f"Mi Saldo ({data['grado']}{data['grupo']})", f"${data['saldo']:,.2f}")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario'])), use_container_width=True)
        conn.close()