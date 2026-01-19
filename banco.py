import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import random

# ==========================================
# 1. CONFIGURACIÓN E INYECCIÓN CSS
# ==========================================
if os.path.exists("logo.png"):
    st.set_page_config(page_title="Banco Summerhill", page_icon="logo.png", layout="wide")
    archivo_logo = "logo.png"
elif os.path.exists("Logo.png"):
    st.set_page_config(page_title="Banco Summerhill", page_icon="Logo.png", layout="wide")
    archivo_logo = "Logo.png"
else:
    st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")
    archivo_logo = None

def cargar_estilos():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
        
        /* BOTONES MODERNOS */
        .stButton > button {
            background-image: linear-gradient(to right, #1fa2ff 0%, #12d8fa 51%, #1fa2ff 100%);
            margin: 5px 0px; padding: 12px 20px; text-align: center; text-transform: uppercase;
            transition: 0.5s; background-size: 200% auto; color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 12px; border: none; font-weight: bold; width: 100%;
        }
        .stButton > button:hover { background-position: right center; color: #fff; transform: scale(1.02); }
        
        /* TARJETA DE SALDO */
        div[data-testid="stMetric"] { background-color: #f8f9fa; border-left: 5px solid #1fa2ff; padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        
        /* EXPANDERS MÁS LIMPIOS */
        .stExpander { border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        
        /* OCULTAR COSAS INNECESARIAS */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
        
        /* MOBILE */
        @media only screen and (max-width: 600px) {
            .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
            h1 { font-size: 1.8rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)
cargar_estilos()

# ==========================================
# 2. CONSTANTES
# ==========================================
ROLES_ADMIN = ['admin', 'director']
ROLES_DOCENTE = ['profesor', 'administrativo']

OPCIONES_MULTAS = {
    "--- Personalizado ---": 0, "Uso de Celular": 50, "No traer Tarea": 100,
    "Falta de Respeto": 500, "Dañar Material": 300, "Uniforme Incompleto": 50, "Platicar / Interrumpir": 30
}

OPCIONES_PAGOS = {
    "--- Personalizado ---": 0, "Tarea Cumplida": 100, "Proyecto Especial": 200,
    "Participación": 20, "Ayudar al Profesor": 50, "Mantener lugar limpio": 30, "Asistencia Perfecta": 50
}

# ==========================================
# 3. BASE DE DATOS
# ==========================================
def get_connection():
    return sqlite3.connect('banco_escolar.db')

def generar_cuenta():
    return str(random.randint(10000000, 99999999))

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, rol TEXT, saldo REAL, password TEXT, email TEXT,
                  grado TEXT, grupo TEXT, cuenta TEXT)''') 
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS solicitudes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, fecha TEXT)''')

    try: c.execute("ALTER TABLE usuarios ADD COLUMN cuenta TEXT")
    except: pass

    c.execute("SELECT id FROM usuarios WHERE cuenta IS NULL OR cuenta = ''")
    for usr in c.fetchall():
        c.execute("UPDATE usuarios SET cuenta = ? WHERE id = ?", (generar_cuenta(), usr[0]))
    
    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo, cuenta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                  ('admin', 'admin', 1000000, '1234', 'admin@summerhill.edu', '', '', generar_cuenta()))
    conn.commit()
    conn.close()

# ==========================================
# 4. FUNCIONES LÓGICAS
# ==========================================
def login(usuario, password):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM usuarios WHERE nombre=? AND password=?", conn, params=(str(usuario), str(password)))
    conn.close()
    return df

def crud_usuario(accion, nombre, rol=None, pwd=None, grado="", grupo=""):
    conn = get_connection()
    c = conn.cursor()
    try:
        if accion == "crear":
            saldo = 1000000 if rol in (ROLES_ADMIN + ROLES_DOCENTE) else 0
            if grado == "-": grado = ""
            if grupo == "-": grupo = ""
            c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, grado, grupo, cuenta) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (str(nombre), str(rol), saldo, str(pwd), str(grado), str(grupo), generar_cuenta()))
        elif accion == "borrar":
            c.execute("DELETE FROM usuarios WHERE nombre=?", (str(nombre),))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def transaccion(origen, destino, monto, concepto, tipo):
    conn = get_connection()
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        monto_float = float(monto)
        c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE nombre = ?", (monto_float, str(origen)))
        c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nombre = ?", (monto_float, str(destino)))
        c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                  (fecha, str(origen), str(destino), monto_float, str(concepto), str(tipo)))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def gestion_solicitud(accion, remitente=None, destinatario=None, monto=0.0, concepto="", id_sol=None):
    conn = get_connection()
    c = conn.cursor()
    try:
        if accion == "crear":
            saldo_df = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(str(remitente),))
            if not saldo_df.empty:
                saldo = saldo_df.iloc[0]['saldo']
                if saldo >= monto:
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO solicitudes (remitente, destinatario, monto, concepto, fecha) VALUES (?, ?, ?, ?, ?)",
                              (str(remitente), str(destinatario), float(monto), str(concepto), fecha))
                    conn.commit()
                    return True, "Enviado"
                else: return False, "Saldo insuficiente"
            else: return False, "Usuario no encontrado"
        elif accion == "aprobar":
            sol_df = pd.read_sql("SELECT * FROM solicitudes WHERE id=?", conn, params=(str(id_sol),))
            if not sol_df.empty:
                sol = sol_df.iloc[0]
                rem_str = str(sol['remitente'])
                saldo_rem = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(rem_str,)).iloc[0]['saldo']
                if saldo_rem >= sol['monto']:
                    monto_float = float(sol['monto'])
                    c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE nombre = ?", (monto_float, rem_str))
                    c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nombre = ?", (monto_float, str(sol['destinatario'])))
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                              (fecha, rem_str, str(sol['destinatario']), monto_float, str(sol['concepto']), "transferencia"))
                    c.execute("DELETE FROM solicitudes WHERE id=?", (str(id_sol),))
                    conn.commit()
                    return True, "Aprobada"
                else:
                    c.execute("DELETE FROM solicitudes WHERE id=?", (str(id_sol),))
                    conn.commit()
                    return False, "Sin fondos"
            return False, "Error"
        elif accion == "rechazar":
            c.execute("DELETE FROM solicitudes WHERE id=?", (str(id_sol),))
            conn.commit()
            return True, "Rechazada"
        return False, "Error"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ==========================================
# 5. UI PRINCIPAL
# ==========================================
init_db()

if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        if archivo_logo: st.image(archivo_logo, width=200)
        st.markdown("<h1 style='text-align: center; color: #1fa2ff;'>Banco Summerhill</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True):
            user_data = login(u, p)
            if not user_data.empty:
                st.session_state['usuario'] = u
                st.session_state['rol'] = user_data.iloc[0]['rol']
                st.rerun()
            else:
                st.error("Error de acceso")

else:
    conn = get_connection()
    try:
        saldo_data = pd.read_sql("SELECT saldo, cuenta FROM usuarios WHERE nombre=?", conn, params=(str(st.session_state['usuario']),))
        saldo_actual = saldo_data.iloc[0]['saldo'] if not saldo_data.empty else 0
        mi_cuenta = saldo_data.iloc[0]['cuenta'] if not saldo_data.empty else "Sin Cuenta"
    except:
        saldo_actual = 0
        mi_cuenta = "Error"
    conn.close()

    with st.sidebar:
        if archivo_logo: st.image(archivo_logo, width=100)
        st.title(st.session_state['usuario'])
        rol_actual = st.session_state['rol'].upper()
        st.caption(f"Rol: {rol_actual}")
        st.markdown(f"💳 **Cta:** `{mi_cuenta}`")
        st.metric("Saldo", f"${saldo_actual:,.2f}")
        if st.button("Salir", type="primary"):
            del st.session_state['usuario']
            st.rerun()

    # =======================================================
    # VISTA: STAFF (Admin, Director, Profesor, Adminis)
    # =======================================================
    if st.session_state['rol'] in (ROLES_ADMIN + ROLES_DOCENTE):
        st.title("Panel de Control")
        
        if st.session_state['rol'] in ROLES_ADMIN:
            tabs = st.tabs(["⚡ Operaciones", "🛡️ Autorizaciones", "👥 Gestión (Admin)", "📊 Historial"])
        else:
            tabs = st.tabs(["⚡ Operaciones", "🛡️ Autorizaciones", "📊 Historial"])

        # --- TAB 1: OPERACIONES (FLUJO UNIFICADO CON MENÚS) ---
        with tabs[0]:
            conn = get_connection()
            df_alumnos = pd.read_sql("SELECT nombre, cuenta, grado, grupo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()
            
            if df_alumnos.empty:
                st.warning("No hay alumnos registrados.")
            else:
                with st.expander("🔍 FILTROS DE BÚSQUEDA", expanded=True):
                    c_fil1, c_fil2, c_fil3 = st.columns(3)
                    grados = ["Todos"] + sorted([x for x in df_alumnos['grado'].unique() if x])
                    grupos = ["Todos"] + sorted([x for x in df_alumnos['grupo'].unique() if x])
                    
                    f_grado = c_fil1.selectbox("Grado", grados)
                    f_grupo = c_fil2.selectbox("Grupo", grupos)
                    f_nombre = c_fil3.text_input("Nombre")

                    df_filtrado = df_alumnos.copy()
                    if f_grado != "Todos": df_filtrado = df_filtrado[df_filtrado['grado'] == f_grado]
                    if f_grupo != "Todos": df_filtrado = df_filtrado[df_filtrado['grupo'] == f_grupo]
                    if f_nombre: df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(f_nombre, case=False)]
                
                if df_filtrado.empty:
                    st.info("No se encontraron alumnos.")
                else:
                    # Crear etiquetas
                    df_filtrado['label'] = df_filtrado.apply(lambda x: f"{x['nombre']} ({x['grado']}{x['grupo']})", axis=1)
                    dic_alumnos = dict(zip(df_filtrado['label'], df_filtrado['nombre']))
                    
                    st.divider()
                    
                    # === ZONA UNIFICADA DE ACCIÓN ===
                    st.markdown("### 🎯 Realizar Operación")
                    
                    # 1. SELECCIONAR ALUMNO
                    sel_alumno = st.selectbox("1. Seleccionar Alumno", list(dic_alumnos.keys()))
                    target_alumno = dic_alumnos[sel_alumno]

                    # 2. SELECCIONAR TIPO DE ACCIÓN (MULTA O PAGO)
                    tipo_accion = st.selectbox("2. Tipo de Operación", ["🔴 COBRAR MULTA", "🟢 PAGAR PREMIO"])

                    # 3. SELECCIONAR MOTIVO Y MONTOS (DINÁMICO)
                    if tipo_accion == "🔴 COBRAR MULTA":
                        lista_opciones = OPCIONES_MULTAS
                        key_prefix = "multa"
                        color_btn = "primary"
                        txt_btn = "Aplicar Cobro"
                        tipo_db = "multa"
                    else:
                        lista_opciones = OPCIONES_PAGOS
                        key_prefix = "premio"
                        color_btn = "primary" # Streamlit solo tiene primary/secondary
                        txt_btn = "Aplicar Pago"
                        tipo_db = "ingreso"
                    
                    opcion_motivo = st.selectbox("3. Seleccionar Motivo", list(lista_opciones.keys()), key=f"sel_{key_prefix}")
                    
                    # Lógica de auto-llenado
                    if f'last_{key_prefix}' not in st.session_state or st.session_state[f'last_{key_prefix}'] != opcion_motivo:
                        st.session_state[f'm_{key_prefix}'] = lista_opciones[opcion_motivo]
                        st.session_state[f't_{key_prefix}'] = opcion_motivo if lista_opciones[opcion_motivo]>0 else ""
                        st.session_state[f'last_{key_prefix}'] = opcion_motivo
                    
                    c_monto, c_detalle = st.columns([1, 2])
                    monto_final = c_monto.number_input("Monto ($)", min_value=0, key=f"m_{key_prefix}")
                    detalle_final = c_detalle.text_input("Detalle / Comentario", key=f"t_{key_prefix}")
                    
                    if st.button(txt_btn, use_container_width=True):
                        if monto_final > 0 and detalle_final:
                            if tipo_db == "multa":
                                transaccion(target_alumno, st.session_state['usuario'], monto_final, detalle_final, tipo_db)
                            else:
                                transaccion(st.session_state['usuario'], target_alumno, monto_final, detalle_final, tipo_db)
                            
                            st.toast(f"Operación Exitosa: {txt_btn}", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning("Verifica el monto y el detalle.")

        # --- TAB 2: AUTORIZACIONES ---
        with tabs[1]:
            conn = get_connection()
            sol = pd.read_sql("SELECT * FROM solicitudes", conn)
            conn.close()
            if sol.empty: st.info("✅ No hay solicitudes pendientes.")
            else:
                for _, r in sol.iterrows():
                    with st.expander(f"💰 ${r['monto']} | De {r['remitente']} para {r['destinatario']}"):
                        st.write(f"**Razón:** {r['concepto']}")
                        st.caption(f"Fecha: {r['fecha']}")
                        col_ok, col_no = st.columns(2)
                        if col_ok.button("✅ Aprobar", key=f"ap{r['id']}", use_container_width=True):
                            gestion_solicitud("aprobar", id_sol=r['id']); st.rerun()
                        if col_no.button("❌ Rechazar", key=f"re{r['id']}", use_container_width=True):
                            gestion_solicitud("rechazar", id_sol=r['id']); st.rerun()

        # --- TAB 3: GESTIÓN (SOLO ADMINS) ---
        if st.session_state['rol'] in ROLES_ADMIN:
            with tabs[2]:
                st.header("⚙️ Gestión Administrativa")
                
                with st.expander("➕ CREAR NUEVO USUARIO", expanded=True):
                    with st.form("new"):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre")
                        p = c2.text_input("Contraseña", "1234")
                        r = c3.selectbox("Rol", ["alumno", "profesor", "director", "administrativo"])
                        c4, c5 = st.columns(2)
                        gr = c4.selectbox("Grado", ["-", "1°", "2°", "3°"])
                        gp = c5.selectbox("Grupo", ["-", "A", "B"])
                        if st.form_submit_button("Crear Usuario", use_container_width=True):
                            if crud_usuario("crear", n, r, p, gr, gp): st.success("Creado"); time.sleep(1); st.rerun()
                            else: st.error("Error: Nombre duplicado")

                with st.expander("📝 VER / EDITAR BASE DE DATOS COMPLETA", expanded=False):
                    conn = get_connection()
                    df_u = pd.read_sql("SELECT * FROM usuarios", conn)
                    conn.close()
                    ed = st.data_editor(df_u, num_rows="dynamic", use_container_width=True)
                    if st.button("💾 Guardar Cambios en Tabla"):
                        conn = get_connection()
                        c = conn.cursor()
                        for _, row in ed.iterrows():
                            cta = str(row['cuenta'])
                            if cta == "None" or cta == "": cta = generar_cuenta()
                            c.execute("UPDATE usuarios SET nombre=?, rol=?, password=?, grado=?, grupo=?, saldo=?, email=?, cuenta=? WHERE id=?",
                                     (str(row['nombre']), str(row['rol']), str(row['password']), str(row['grado']), str(row['grupo']), float(row['saldo']), str(row['email']), cta, row['id']))
                        conn.commit(); conn.close(); st.success("Guardado"); time.sleep(1); st.rerun()

                with st.expander("📂 CARGA MASIVA (CSV)", expanded=False):
                    st.info("Sube un archivo CSV con columnas: nombre, rol, password, grado, grupo")
                    up_csv = st.file_uploader("Seleccionar archivo", type="csv")
                    if up_csv and st.button("Procesar Archivo"):
                        try:
                            df = pd.read_csv(up_csv)
                            for _, row in df.iterrows():
                                crud_usuario("crear", row['nombre'], row['rol'], str(row['password']), str(row.get('grado','')), str(row.get('grupo','')))
                            st.success("Usuarios cargados exitosamente")
                        except: st.error("Error en el formato del CSV")

                with st.expander("💾 RESPALDOS DE SEGURIDAD", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        with open("banco_escolar.db", "rb") as f: st.download_button("⬇️ Descargar Backup", f, "respaldo.db", use_container_width=True)
                    with c2:
                        up = st.file_uploader("Restaurar Backup")
                        if up and st.button("🔴 Restaurar", use_container_width=True):
                            with open("banco_escolar.db", "wb") as f: f.write(up.getbuffer())
                            st.success("Restaurado"); time.sleep(1); st.rerun()

        # --- TAB HISTORIAL ---
        idx_hist = 3 if st.session_state['rol'] in ROLES_ADMIN else 2
        with tabs[idx_hist]:
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()

    # =======================================================
    # VISTA: ALUMNO
    # =======================================================
    else:
        conn = get_connection()
        df_alumnos = pd.read_sql("SELECT nombre, grado, grupo, cuenta FROM usuarios WHERE rol='alumno' AND nombre != ?", conn, params=(st.session_state['usuario'],))
        conn.close()

        st.info("👋 ¡Hola! Para transferir, busca a tu compañero en la lista.")

        if df_alumnos.empty:
            st.warning("No hay otros alumnos registrados.")
        else:
            df_alumnos['label'] = df_alumnos.apply(lambda x: f"{x['nombre']} ({x['grado']}{x['grupo']})", axis=1)
            dic_alumnos = dict(zip(df_alumnos['label'], df_alumnos['nombre']))
            
            with st.form("form_transf_alumno"):
                st.subheader("💸 Nueva Transferencia")
                seleccion = st.selectbox("¿A quién le envías?", list(dic_alumnos.keys()))
                destinatario_real = dic_alumnos[seleccion]
                
                c_a, c_b = st.columns(2)
                monto = c_a.number_input("Cantidad ($)", min_value=1.0)
                motivo = c_b.text_input("Motivo (Ej. Cooperación)")
                
                if st.form_submit_button("🚀 Enviar Dinero", use_container_width=True):
                    ok, msg = gestion_solicitud("crear", remitente=st.session_state['usuario'], destinatario=destinatario_real, monto=monto, concepto=motivo)
                    if ok: st.success(f"Solicitud enviada a {destinatario_real}.")
                    else: st.error(msg)
        
        st.divider()
        st.subheader("📜 Mis Movimientos")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(str(st.session_state['usuario']), str(st.session_state['usuario']))), use_container_width=True)
        conn.close()