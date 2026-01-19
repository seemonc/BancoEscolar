import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os

# ==========================================
# 1. LOGO SIMPLE
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

# ==========================================
# 2. PRECIOS (CATÁLOGOS)
# ==========================================
OPCIONES_MULTAS = {
    "--- Personalizado ---": 0,
    "Uso de Celular": 50,
    "No traer Tarea": 100,
    "Falta de Respeto": 500,
    "Dañar Material": 300,
    "Uniforme Incompleto": 50,
    "Platicar / Interrumpir": 30
}

OPCIONES_PAGOS = {
    "--- Personalizado ---": 0,
    "Tarea Cumplida": 100,
    "Proyecto Especial": 200,
    "Participación": 20,
    "Ayudar al Profesor": 50,
    "Mantener lugar limpio": 30,
    "Asistencia Perfecta": 50
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
    c.execute('''CREATE TABLE IF NOT EXISTS solicitudes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, fecha TEXT)''')
    
    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  ('admin', 'admin', 1000000, '1234', 'admin@summerhill.edu', '', ''))
        conn.commit()
    conn.close()

# ==========================================
# 4. FUNCIONES
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
            saldo = 1000000 if rol in ['admin', 'profesor', 'director', 'administrativo'] else 0
            if grado == "-": grado = ""
            if grupo == "-": grupo = ""
            c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, grado, grupo) VALUES (?, ?, ?, ?, ?, ?)", 
                      (str(nombre), str(rol), saldo, str(pwd), str(grado), str(grupo)))
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
        c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE nombre = ?", (monto, str(origen)))
        c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nombre = ?", (monto, str(destino)))
        c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                  (fecha, str(origen), str(destino), monto, str(concepto), str(tipo)))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def gestion_solicitud(accion, remitente=None, destinatario=None, monto=0, concepto="", id_sol=None):
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
                              (str(remitente), str(destinatario), monto, str(concepto), fecha))
                    conn.commit()
                    return True, "Enviado"
                else:
                    return False, "Saldo insuficiente"
            else:
                return False, "Usuario no encontrado"
        elif accion == "aprobar":
            sol_df = pd.read_sql("SELECT * FROM solicitudes WHERE id=?", conn, params=(str(id_sol),))
            if not sol_df.empty:
                sol = sol_df.iloc[0]
                rem_str = str(sol['remitente'])
                saldo_rem = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(rem_str,)).iloc[0]['saldo']
                if saldo_rem >= sol['monto']:
                    c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE nombre = ?", (sol['monto'], rem_str))
                    c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nombre = ?", (sol['monto'], str(sol['destinatario'])))
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                              (fecha, rem_str, str(sol['destinatario']), sol['monto'], str(sol['concepto']), "transferencia"))
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

# --- LOGIN ---
if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        if archivo_logo: st.image(archivo_logo, width=200)
        st.markdown("<h1 style='text-align: center;'>Banco Summerhill</h1>", unsafe_allow_html=True)
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

# --- DENTRO DEL SISTEMA ---
else:
    conn = get_connection()
    try:
        saldo_data = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(str(st.session_state['usuario']),))
        saldo_actual = saldo_data.iloc[0]['saldo'] if not saldo_data.empty else 0
    except:
        saldo_actual = 0
    conn.close()

    with st.sidebar:
        if archivo_logo: st.image(archivo_logo, width=100)
        st.title(st.session_state['usuario'])
        st.caption(st.session_state['rol'])
        st.metric("Saldo", f"${saldo_actual:,.2f}")
        if st.button("Salir", type="primary"):
            del st.session_state['usuario']
            st.rerun()

    # VISTA ADMIN
    if st.session_state['rol'] in ['admin', 'profesor', 'director', 'administrativo']:
        st.title("Panel de Control")
        tabs = st.tabs(["⚡ Operaciones", "🛡️ Autorizaciones", "👥 Gestión", "📊 Historial"])

        # TAB 1: OPERACIONES
        with tabs[0]:
            conn = get_connection()
            alumnos = pd.read_sql("SELECT nombre, grado, grupo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()
            
            if alumnos.empty:
                st.warning("No hay alumnos.")
            else:
                lista_nombres = alumnos['nombre'].tolist()
                c_op1, c_op2 = st.columns(2)
                
                # === ZONA DE COBRO (AUTOMÁTICA) ===
                with c_op1:
                    st.error("🚨 COBROS / MULTAS")
                    target_cobro = st.selectbox("Alumno", lista_nombres, key="u_cobro")
                    
                    # 1. Menú desplegable
                    opcion_c = st.selectbox("Selecciona Multa", list(OPCIONES_MULTAS.keys()), key="sel_cobro_auto")
                    
                    # 2. Lógica de Actualización Inmediata
                    # Si la selección cambia, actualizamos los valores de session_state que alimentan los inputs de abajo
                    if 'last_op_c' not in st.session_state or st.session_state['last_op_c'] != opcion_c:
                        precio = OPCIONES_MULTAS[opcion_c]
                        texto = opcion_c if precio > 0 else ""
                        st.session_state['monto_c_input'] = precio
                        st.session_state['motivo_c_input'] = texto
                        st.session_state['last_op_c'] = opcion_c

                    # 3. Inputs conectados al session_state
                    monto_final_c = st.number_input("Monto ($)", min_value=0, key="monto_c_input")
                    motivo_final_c = st.text_input("Motivo", key="motivo_c_input")

                    if st.button("Aplicar Multa"):
                        if monto_final_c > 0 and motivo_final_c:
                            transaccion(target_cobro, st.session_state['usuario'], monto_final_c, motivo_final_c, "multa")
                            st.toast("Multa aplicada", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning("Verifica los datos")

                # === ZONA DE PAGO (AUTOMÁTICA) ===
                with c_op2:
                    st.success("💵 PAGOS / PREMIOS")
                    target_pago = st.selectbox("Alumno", lista_nombres, key="u_pago")
                    
                    # 1. Menú desplegable
                    opcion_p = st.selectbox("Selecciona Premio", list(OPCIONES_PAGOS.keys()), key="sel_pago_auto")
                    
                    # 2. Lógica de Actualización Inmediata
                    if 'last_op_p' not in st.session_state or st.session_state['last_op_p'] != opcion_p:
                        precio_p = OPCIONES_PAGOS[opcion_p]
                        texto_p = opcion_p if precio_p > 0 else ""
                        st.session_state['monto_p_input'] = precio_p
                        st.session_state['motivo_p_input'] = texto_p
                        st.session_state['last_op_p'] = opcion_p
                    
                    # 3. Inputs conectados
                    monto_final_p = st.number_input("Monto ($)", min_value=0, key="monto_p_input")
                    motivo_final_p = st.text_input("Motivo", key="motivo_p_input")
                    
                    if st.button("Aplicar Pago"):
                        if monto_final_p > 0 and motivo_final_p:
                            transaccion(st.session_state['usuario'], target_pago, monto_final_p, motivo_final_p, "ingreso")
                            st.toast("Pago aplicado", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning("Verifica los datos")

        # TAB 2: AUTORIZACIONES
        with tabs[1]:
            conn = get_connection()
            solicitudes = pd.read_sql("SELECT * FROM solicitudes", conn)
            conn.close()
            if solicitudes.empty:
                st.info("Sin solicitudes.")
            else:
                for _, row in solicitudes.iterrows():
                    with st.expander(f"${row['monto']} | {row['remitente']} -> {row['destinatario']}", expanded=True):
                        c1, c2, c3 = st.columns([2,1,1])
                        c1.write(f"**Motivo:** {row['concepto']}")
                        if c2.button("✅ Aprobar", key=f"ap_{row['id']}"):
                            ok, msg = gestion_solicitud("aprobar", id_sol=row['id'])
                            if ok: st.success(msg)
                            else: st.error(msg)
                            time.sleep(1)
                            st.rerun()
                        if c3.button("❌ Rechazar", key=f"re_{row['id']}"):
                            gestion_solicitud("rechazar", id_sol=row['id'])
                            st.rerun()

        # TAB 3: GESTIÓN
        with tabs[2]:
            st.markdown("### 📝 EDITOR TOTAL")
            conn = get_connection()
            df_usuarios = pd.read_sql("SELECT * FROM usuarios", conn)
            conn.close()
            df_editado = st.data_editor(df_usuarios, num_rows="dynamic", key="editor_usuarios")
            if st.button("💾 GUARDAR CAMBIOS TABLA"):
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    for index, row in df_editado.iterrows():
                        c.execute("""UPDATE usuarios SET 
                                     nombre=?, rol=?, password=?, grado=?, grupo=?, saldo=?, email=? 
                                     WHERE id=?""",
                                  (str(row['nombre']), str(row['rol']), str(row['password']), 
                                   str(row['grado']), str(row['grupo']), float(row['saldo']), 
                                   str(row['email']), row['id']))
                    conn.commit()
                    conn.close()
                    st.success("Guardado.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            st.divider()
            
            st.markdown("### ➕ Crear Usuario (Individual)")
            with st.form("crear_uno"):
                c1, c2, c3 = st.columns(3)
                n_nuevo = c1.text_input("Nombre de Usuario")
                p_nuevo = c2.text_input("Contraseña", "1234")
                r_nuevo = c3.selectbox("Rol", ["alumno", "profesor", "director", "administrativo"])
                c4, c5 = st.columns(2)
                g_grado = c4.selectbox("Grado", ["-", "1°", "2°", "3°"])
                g_grupo = c5.selectbox("Grupo", ["-", "A", "B"])
                if st.form_submit_button("Crear Usuario"):
                    if crud_usuario("crear", n_nuevo, r_nuevo, p_nuevo, g_grado, g_grupo):
                        st.success(f"Usuario {n_nuevo} creado.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error: Nombre duplicado.")

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                with open("banco_escolar.db", "rb") as f: st.download_button("Descargar DB", f, "respaldo.db")
            with c2:
                up_db = st.file_uploader("Restaurar DB", type="db")
                if up_db and st.button("Restaurar"):
                    with open("banco_escolar.db", "wb") as f: f.write(up_db.getbuffer())
                    st.success("Listo"); st.rerun()
            
            st.markdown("### Cargar CSV")
            up_csv = st.file_uploader("CSV", type="csv")
            if up_csv and st.button("Procesar CSV"):
                try:
                    df = pd.read_csv(up_csv)
                    for _, row in df.iterrows():
                        crud_usuario("crear", row['nombre'], row['rol'], str(row['password']), str(row.get('grado','')), str(row.get('grupo','')))
                    st.success("Listo")
                except: st.error("Error en CSV")

        # TAB 4: HISTORIAL
        with tabs[3]:
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()

    # VISTA ALUMNO
    else:
        conn = get_connection()
        try:
            data_alu = pd.read_sql("SELECT grado, grupo FROM usuarios WHERE nombre=?", conn, params=(str(st.session_state['usuario']),))
            if not data_alu.empty: info = f"{data_alu.iloc[0]['grado']} {data_alu.iloc[0]['grupo']}"
            else: info = ""
        except: info = ""
        conn.close()
        st.info(f"Alumno: {info}")
        
        with st.expander("Transferir", expanded=True):
            conn = get_connection()
            comps = pd.read_sql("SELECT nombre FROM usuarios WHERE rol='alumno' AND nombre!=?", conn, params=(str(st.session_state['usuario']),))['nombre'].tolist()
            conn.close()
            if comps:
                dst = st.selectbox("Para:", comps)
                mnt = st.number_input("Monto", min_value=1)
                mot = st.text_input("Motivo")
                if st.button("Enviar"):
                    ok, msg = gestion_solicitud("crear", remitente=st.session_state['usuario'], destinatario=dst, monto=mnt, concepto=mot)
                    if ok: st.success(msg)
                    else: st.error(msg)
        st.divider()
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(str(st.session_state['usuario']), str(st.session_state['usuario']))), use_container_width=True)
        conn.close()