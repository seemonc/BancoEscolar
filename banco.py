import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import random

# ==========================================
# 1. LOGO
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
# 2. LISTAS
# ==========================================
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
# 4. LÓGICA (CORREGIDA PARA FLOATS)
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
        # Aseguramos que monto sea float
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

# AQUÍ ESTABA EL ERROR: Cambié monto=0 a monto=0.0
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
                    # Usamos float explícito
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
        st.caption(f"Rol: {st.session_state['rol']}")
        st.markdown(f"💳 **Cta:** `{mi_cuenta}`")
        st.metric("Saldo", f"${saldo_actual:,.2f}")
        if st.button("Salir", type="primary"):
            del st.session_state['usuario']
            st.rerun()

    # VISTA ADMIN
    if st.session_state['rol'] in ['admin', 'profesor', 'director', 'administrativo']:
        st.title("Panel de Control")
        tabs = st.tabs(["⚡ Operaciones", "🛡️ Autorizaciones", "👥 Gestión", "📊 Historial"])

        with tabs[0]:
            conn = get_connection()
            alumnos = pd.read_sql("SELECT nombre, cuenta, grado, grupo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()
            if alumnos.empty: st.warning("No hay alumnos.")
            else:
                alumnos['label'] = alumnos['nombre'].astype(str) + " (Cta: " + alumnos['cuenta'].astype(str) + ")"
                dic_alumnos = dict(zip(alumnos['label'], alumnos['nombre']))
                c1, c2 = st.columns(2)
                
                with c1:
                    st.error("🚨 MULTAS")
                    sel_c = st.selectbox("Alumno", list(dic_alumnos.keys()), key="sc")
                    op_c = st.selectbox("Motivo", list(OPCIONES_MULTAS.keys()), key="oc")
                    
                    if 'last_c' not in st.session_state or st.session_state['last_c'] != op_c:
                        st.session_state['m_c'] = OPCIONES_MULTAS[op_c]
                        st.session_state['t_c'] = op_c if OPCIONES_MULTAS[op_c]>0 else ""
                        st.session_state['last_c'] = op_c
                    
                    m_c = st.number_input("Monto", min_value=0, key="m_c")
                    t_c = st.text_input("Detalle", key="t_c")
                    if st.button("Aplicar Multa"):
                        transaccion(dic_alumnos[sel_c], st.session_state['usuario'], m_c, t_c, "multa")
                        st.toast("Listo", icon="✅"); time.sleep(0.5); st.rerun()

                with c2:
                    st.success("💵 PREMIOS")
                    sel_p = st.selectbox("Alumno", list(dic_alumnos.keys()), key="sp")
                    op_p = st.selectbox("Motivo", list(OPCIONES_PAGOS.keys()), key="op")
                    
                    if 'last_p' not in st.session_state or st.session_state['last_p'] != op_p:
                        st.session_state['m_p'] = OPCIONES_PAGOS[op_p]
                        st.session_state['t_p'] = op_p if OPCIONES_PAGOS[op_p]>0 else ""
                        st.session_state['last_p'] = op_p
                    
                    m_p = st.number_input("Monto", min_value=0, key="m_p")
                    t_p = st.text_input("Detalle", key="t_p")
                    if st.button("Aplicar Premio"):
                        transaccion(st.session_state['usuario'], dic_alumnos[sel_p], m_p, t_p, "ingreso")
                        st.toast("Listo", icon="✅"); time.sleep(0.5); st.rerun()

        with tabs[1]:
            conn = get_connection()
            sol = pd.read_sql("SELECT * FROM solicitudes", conn)
            conn.close()
            if sol.empty: st.info("Sin solicitudes.")
            else:
                for _, r in sol.iterrows():
                    with st.expander(f"${r['monto']} | {r['remitente']} -> {r['destinatario']}"):
                        st.write(f"Motivo: {r['concepto']}")
                        c1, c2 = st.columns(2)
                        if c1.button("✅", key=f"ap{r['id']}"): gestion_solicitud("aprobar", id_sol=r['id']); st.rerun()
                        if c2.button("❌", key=f"re{r['id']}"): gestion_solicitud("rechazar", id_sol=r['id']); st.rerun()

        with tabs[2]:
            st.header("Gestión")
            with st.expander("➕ Crear Usuario", expanded=True):
                with st.form("new"):
                    c1, c2, c3 = st.columns(3)
                    n = c1.text_input("Nombre")
                    p = c2.text_input("Password", "1234")
                    r = c3.selectbox("Rol", ["alumno", "profesor", "director"])
                    c4, c5 = st.columns(2)
                    gr = c4.selectbox("Grado", ["-", "1°", "2°", "3°"])
                    gp = c5.selectbox("Grupo", ["-", "A", "B"])
                    if st.form_submit_button("Crear"):
                        if crud_usuario("crear", n, r, p, gr, gp): st.success("Creado"); st.rerun()
                        else: st.error("Duplicado")
            
            conn = get_connection()
            df_u = pd.read_sql("SELECT * FROM usuarios", conn)
            conn.close()
            ed = st.data_editor(df_u, num_rows="dynamic")
            if st.button("💾 Guardar Cambios"):
                conn = get_connection()
                c = conn.cursor()
                for _, row in ed.iterrows():
                    cta = str(row['cuenta'])
                    if cta == "None" or cta == "": cta = generar_cuenta()
                    c.execute("UPDATE usuarios SET nombre=?, rol=?, password=?, grado=?, grupo=?, saldo=?, email=?, cuenta=? WHERE id=?",
                             (str(row['nombre']), str(row['rol']), str(row['password']), str(row['grado']), str(row['grupo']), float(row['saldo']), str(row['email']), cta, row['id']))
                conn.commit(); conn.close(); st.success("Guardado"); time.sleep(1); st.rerun()

            c1, c2 = st.columns(2)
            with c1:
                with open("banco_escolar.db", "rb") as f: st.download_button("Descargar DB", f, "respaldo.db")
            with c2:
                up = st.file_uploader("Restaurar DB")
                if up and st.button("Restaurar"):
                    with open("banco_escolar.db", "wb") as f: f.write(up.getbuffer())
                    st.success("Listo"); st.rerun()

        with tabs[3]:
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()

    # VISTA ALUMNO (DIRECTORIO Y ENVÍO MANUAL)
    else:
        conn = get_connection()
        df_dir = pd.read_sql("SELECT nombre, grado, grupo, cuenta FROM usuarios WHERE rol='alumno' AND nombre != ?", conn, params=(st.session_state['usuario'],))
        conn.close()

        col_izq, col_der = st.columns([1, 1])

        # IZQUIERDA: DIRECTORIO
        with col_izq:
            st.info("📒 **Directorio de Cuentas**")
            st.markdown("Busca el número de cuenta de tu compañero.")
            
            c_fil1, c_fil2 = st.columns(2)
            f_grado = c_fil1.selectbox("Grado", ["Todos"] + sorted([x for x in df_dir['grado'].unique() if x]))
            f_grupo = c_fil2.selectbox("Grupo", ["Todos"] + sorted([x for x in df_dir['grupo'].unique() if x]))
            f_nombre = st.text_input("Buscar por Nombre")

            df_show = df_dir.copy()
            if f_grado != "Todos": df_show = df_show[df_show['grado'] == f_grado]
            if f_grupo != "Todos": df_show = df_show[df_show['grupo'] == f_grupo]
            if f_nombre: df_show = df_show[df_show['nombre'].str.contains(f_nombre, case=False)]

            st.dataframe(df_show[['nombre', 'cuenta']], hide_index=True, use_container_width=True)

        # DERECHA: TRANSFERENCIA MANUAL
        with col_der:
            st.success("💸 **Transferir Dinero**")
            with st.form("form_transf"):
                cta_destino = st.text_input("Ingresa Número de Cuenta Destino")
                monto = st.number_input("Monto ($)", min_value=1.0)
                motivo = st.text_input("Motivo")
                
                if st.form_submit_button("🚀 Enviar"):
                    conn = get_connection()
                    res = pd.read_sql("SELECT nombre FROM usuarios WHERE cuenta=?", conn, params=(str(cta_destino),))
                    conn.close()
                    
                    if not res.empty:
                        nombre_dest = res.iloc[0]['nombre']
                        if nombre_dest == st.session_state['usuario']:
                            st.error("No puedes transferirte a ti mismo.")
                        else:
                            ok, msg = gestion_solicitud("crear", remitente=st.session_state['usuario'], destinatario=nombre_dest, monto=monto, concepto=motivo)
                            if ok: st.success(f"Enviado a {nombre_dest}.")
                            else: st.error(msg)
                    else:
                        st.error("❌ Cuenta no encontrada.")

        st.divider()
        st.subheader("📜 Historial")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(str(st.session_state['usuario']), str(st.session_state['usuario']))), use_container_width=True)
        conn.close()