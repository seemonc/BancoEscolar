import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os

# ==========================================
# 1. FUERZA BRUTA PARA EL LOGO (SIN TOCAR)
# ==========================================
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

if os.path.exists("logo.png"):
    st.set_page_config(page_title="Banco Summerhill", page_icon="logo.png", layout="wide")
    archivo_logo = "logo.png"
else:
    st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")
    archivo_logo = None

# ==========================================
# 2. LISTAS DE SUGERENCIAS (SIN TOCAR)
# ==========================================
OPCIONES_MULTAS = {
    "--- Escribir Manualmente ---": 0,
    "Uso de Celular": 100,
    "Falta de Respeto": 500,
    "Tarea No Entregada": 200,
    "Uniforme Incompleto": 50,
    "Comer en clase": 50,
    "Dañar material": 300
}

OPCIONES_PAGOS = {
    "--- Escribir Manualmente ---": 0,
    "Tarea Cumplida": 50,
    "Participación": 20,
    "Proyecto Extra": 200,
    "Apoyo a Docente": 30,
    "Buena Conducta": 50
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
        if archivo_logo:
            st.image(archivo_logo, width=200)
        else:
            st.markdown("<h1>🏦</h1>", unsafe_allow_html=True)
            
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
                
                # ZONA DE COBRO
                with c_op1:
                    st.error("🚨 COBROS / MULTAS")
                    if lista_nombres:
                        target_cobro = st.selectbox("Alumno", lista_nombres, key="u_cobro")
                        opcion_rapida_c = st.selectbox("Opciones Rápidas (Opcional)", list(OPCIONES_MULTAS.keys()), key="sel_rap_c")
                        
                        val_m_c = OPCIONES_MULTAS[opcion_rapida_c]
                        val_t_c = opcion_rapida_c if val_m_c > 0 else ""
                        
                        if 'last_sel_c' not in st.session_state or st.session_state['last_sel_c'] != opcion_rapida_c:
                            st.session_state['m_cob_val'] = val_m_c
                            st.session_state['t_cob_val'] = val_t_c
                            st.session_state['last_sel_c'] = opcion_rapida_c

                        monto_final_c = st.number_input("Monto ($)", min_value=0, key="m_cob", value=st.session_state.get('m_cob_val', 0))
                        motivo_final_c = st.text_input("Motivo", key="t_cob", value=st.session_state.get('t_cob_val', ""))

                        if st.button("Aplicar Multa"):
                            if monto_final_c > 0 and motivo_final_c:
                                transaccion(target_cobro, st.session_state['usuario'], monto_final_c, motivo_final_c, "multa")
                                st.toast("Cobro aplicado", icon="✅")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("Escribe un motivo y monto válido")

                # ZONA DE PAGO
                with c_op2:
                    st.success("💵 PAGOS / PREMIOS")
                    if lista_nombres:
                        target_pago = st.selectbox("Alumno", lista_nombres, key="u_pago")
                        opcion_rapida_p = st.selectbox("Opciones Rápidas (Opcional)", list(OPCIONES_PAGOS.keys()), key="sel_rap_p")
                        
                        val_m_p = OPCIONES_PAGOS[opcion_rapida_p]
                        val_t_p = opcion_rapida_p if val_m_p > 0 else ""
                        
                        if 'last_sel_p' not in st.session_state or st.session_state['last_sel_p'] != opcion_rapida_p:
                            st.session_state['m_pag_val'] = val_m_p
                            st.session_state['t_pag_val'] = val_t_p
                            st.session_state['last_sel_p'] = opcion_rapida_p
                        
                        monto_final_p = st.number_input("Monto ($)", min_value=0, key="m_pag", value=st.session_state.get('m_pag_val', 0))
                        motivo_final_p = st.text_input("Motivo", key="t_pag", value=st.session_state.get('t_pag_val', ""))
                        
                        if st.button("Aplicar Pago"):
                            if monto_final_p > 0 and motivo_final_p:
                                transaccion(st.session_state['usuario'], target_pago, monto_final_p, motivo_final_p, "ingreso")
                                st.toast("Pago aplicado", icon="✅")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("Escribe un motivo y monto válido")

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

        # TAB 3: GESTIÓN (AQUÍ ESTÁ LO NUEVO QUE PEDISTE)
        with tabs[2]:
            st.markdown("### 📝 EDITOR TOTAL DE USUARIOS")
            st.info("Edita cualquier celda y dale a 'Guardar Cambios' para actualizar la base de datos.")
            
            conn = get_connection()
            # Traemos todos los usuarios
            df_usuarios = pd.read_sql("SELECT * FROM usuarios", conn)
            conn.close()

            # Editor interactivo
            df_editado = st.data_editor(df_usuarios, num_rows="dynamic", key="editor_usuarios")

            if st.button("💾 GUARDAR CAMBIOS EN LA TABLA"):
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    # Recorremos el dataframe editado y actualizamos
                    for index, row in df_editado.iterrows():
                        # Usamos el ID para saber a cual actualizar
                        c.execute("""UPDATE usuarios SET 
                                     nombre=?, rol=?, password=?, grado=?, grupo=?, saldo=?, email=? 
                                     WHERE id=?""",
                                  (str(row['nombre']), str(row['rol']), str(row['password']), 
                                   str(row['grado']), str(row['grupo']), float(row['saldo']), 
                                   str(row['email']), row['id']))
                    conn.commit()
                    conn.close()
                    st.success("✅ Base de datos actualizada correctamente.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

            st.divider()
            
            # (El resto de cosas: Respaldo y Carga CSV, lo dejé abajo por si acaso)
            st.markdown("---")
            st.markdown("### Herramientas Extra")
            c1, c2 = st.columns(2)
            with c1:
                with open("banco_escolar.db", "rb") as f:
                    st.download_button("Descargar Respaldo DB", f, "respaldo.db")
            with c2:
                up_db = st.file_uploader("Restaurar Respaldo", type="db")
                if up_db and st.button("Restaurar"):
                    with open("banco_escolar.db", "wb") as f: f.write(up_db.getbuffer())
                    st.success("Listo"); st.rerun()

            st.markdown("### Carga Masiva CSV")
            up_csv = st.file_uploader("Cargar CSV", type="csv")
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
            if not data_alu.empty:
                info = f"{data_alu.iloc[0]['grado']} {data_alu.iloc[0]['grupo']}"
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