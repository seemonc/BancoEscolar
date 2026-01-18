import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
ROLES_ADMINISTRATIVOS = ['admin', 'profesor', 'director', 'administrativo']
CATALOGO_MULTAS = {
    "Incumplimiento de Tarea": 200, "Interrupción de Clase": 150,
    "Falta de Respeto (Verbal)": 500, "Uso de Celular": 100,
    "Área sucia": 50, "Daño a Material": 300
}

st.set_page_config(page_title="Banco Escolar SEP", page_icon="🏦", layout="wide")

# ==========================================
# 2. BASE DE DATOS
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
                  ('admin', 'admin', 1000000, '1234', 'admin@escuela.edu', '', ''))
        conn.commit()
    conn.close()

# ==========================================
# 3. LÓGICA
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
# 4. INTERFAZ GRÁFICA
# ==========================================
init_db()

if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align: center;'>🏦 Banco Escolar</h1>", unsafe_allow_html=True)
        st.info("Sistema de Control Financiero")
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
    # SIDEBAR
    conn = get_connection()
    try:
        saldo_admin = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]['saldo']
    except:
        saldo_admin = 0
    conn.close()

    st.sidebar.markdown(f"## 👤 {st.session_state['usuario']}")
    st.sidebar.caption(f"Rol: {st.session_state['rol'].upper()}")
    st.sidebar.metric("💰 MI SALDO", f"${saldo_admin:,.2f}")
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state['usuario']
        st.rerun()

    # VISTA ADMIN
    if st.session_state['rol'] in ROLES_ADMINISTRATIVOS:
        st.title("Panel de Dirección")
        
        tab1, tab2, tab3 = st.tabs(["⚡ Operaciones (Checklist)", "👥 Gestión de Alumnos", "📊 Historial"])

        # --- TAB 1: OPERACIONES CON CHECKLIST ---
        with tab1:
            st.markdown("### 🔍 Buscador y Selección")
            
            conn = get_connection()
            df_full = pd.read_sql("SELECT nombre, grado, grupo, saldo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()

            if df_full.empty:
                st.warning("⚠️ No hay alumnos registrados. Ve a Gestión.")
            else:
                # === ZONA DE FILTROS ===
                c_fil1, c_fil2, c_fil3 = st.columns(3)
                
                lista_grados = ["Todos"] + sorted([x for x in df_full['grado'].unique() if x])
                lista_grupos = ["Todos"] + sorted([x for x in df_full['grupo'].unique() if x])
                
                filtro_grado = c_fil1.selectbox("Filtrar Grado", lista_grados)
                filtro_grupo = c_fil2.selectbox("Filtrar Grupo", lista_grupos)
                busqueda_txt = c_fil3.text_input("Buscar por Nombre/Apellido", placeholder="Ej. Juan")

                # APLICAR FILTROS
                df_filtrado = df_full.copy()
                if filtro_grado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['grado'] == filtro_grado]
                if filtro_grupo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['grupo'] == filtro_grupo]
                if busqueda_txt:
                    df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(busqueda_txt, case=False)]

                st.divider()

                # === MODO DE OPERACIÓN ===
                op_mode = st.radio("Modo:", ["Individual", "Selección Múltiple (Casillas)"], horizontal=True)

                if op_mode == "Individual":
                    lista_nombres = df_filtrado['nombre'].tolist()
                    if lista_nombres:
                        col_ind_1, col_ind_2 = st.columns(2)
                        with col_ind_1:
                            st.error("🚨 Cobrar Multa")
                            u_sanc = st.selectbox("Alumno", lista_nombres, key="u_ind_m")
                            m_sanc = st.selectbox("Motivo", list(CATALOGO_MULTAS.keys()), key="m_ind")
                            if st.button("Cobrar Individual"):
                                ejecutar_transaccion(u_sanc, st.session_state['usuario'], CATALOGO_MULTAS[m_sanc], m_sanc, "multa")
                                st.toast("Cobrado", icon="✅")
                                time.sleep(1)
                                st.rerun()
                        with col_ind_2:
                            st.success("💵 Pagar")
                            u_pay = st.selectbox("Alumno", lista_nombres, key="u_ind_p")
                            a_pay = st.number_input("Monto", 50, key="a_ind")
                            if st.button("Pagar Individual"):
                                ejecutar_transaccion(st.session_state['usuario'], u_pay, a_pay, "Pago", "ingreso")
                                st.toast("Pagado", icon="✅")
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.warning("Sin resultados.")

                else: # MODO SELECCIÓN MÚLTIPLE (CHECKLIST)
                    st.info("👇 Marca las casillas de los alumnos a los que quieras aplicar la acción.")
                    
                    # Agregar columna de checklist
                    df_filtrado.insert(0, "Seleccionar", False)
                    
                    # Mostrar tabla editable con checkboxes
                    edited_df = st.data_editor(
                        df_filtrado,
                        column_config={
                            "Seleccionar": st.column_config.CheckboxColumn(
                                "Elegir",
                                help="Marca para seleccionar",
                                default=False,
                            ),
                            "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                            "grado": st.column_config.TextColumn("Grado", disabled=True),
                            "grupo": st.column_config.TextColumn("Grupo", disabled=True),
                            "saldo": st.column_config.NumberColumn("Saldo", disabled=True),
                        },
                        disabled=["nombre", "grado", "grupo", "saldo"],
                        hide_index=True,
                        key="editor_seleccion"
                    )

                    # Obtener solo los seleccionados
                    alumnos_seleccionados = edited_df[edited_df["Seleccionar"] == True]["nombre"].tolist()
                    
                    st.write(f"Has seleccionado a: **{len(alumnos_seleccionados)} alumnos**")

                    if alumnos_seleccionados:
                        c_mass_1, c_mass_2 = st.columns(2)
                        
                        with c_mass_1:
                            st.error("🚨 Multar a los SELECCIONADOS")
                            m_mass = st.selectbox("Motivo", list(CATALOGO_MULTAS.keys()), key="m_mass")
                            if st.button("🔥 APLICAR MULTA"):
                                bar = st.progress(0)
                                for i, user in enumerate(alumnos_seleccionados):
                                    ejecutar_transaccion(user, st.session_state['usuario'], CATALOGO_MULTAS[m_mass], m_mass, "multa")
                                    bar.progress((i+1)/len(alumnos_seleccionados))
                                st.success("¡Listo!")
                                time.sleep(1)
                                st.rerun()

                        with c_mass_2:
                            st.success("💵 Pagar a los SELECCIONADOS")
                            r_mass = st.text_input("Motivo", "Beca", key="r_mass")
                            a_mass = st.number_input("Monto", 50, key="a_mass")
                            if st.button("🔥 APLICAR PAGO"):
                                bar = st.progress(0)
                                for i, user in enumerate(alumnos_seleccionados):
                                    ejecutar_transaccion(st.session_state['usuario'], user, a_mass, r_mass, "ingreso")
                                    bar.progress((i+1)/len(alumnos_seleccionados))
                                st.success("¡Listo!")
                                time.sleep(1)
                                st.rerun()

        # --- TAB 2: GESTIÓN ---
        with tab2:
            st.header("🗂️ Gestión de Alumnos")
            with st.expander("➕ Registro Manual", expanded=False):
                with st.form("alta"):
                    c1, c2, c3 = st.columns(3)
                    n = c1.text_input("Usuario")
                    p = c2.text_input("Contraseña", value="1234")
                    e = c3.text_input("Email")
                    c4, c5, c6 = st.columns(3)
                    r = c4.selectbox("Rol", ["alumno", "profesor"])
                    g_grado = c5.text_input("Grado")
                    g_grupo = c6.text_input("Grupo")
                    if st.form_submit_button("Crear"):
                        crear_usuario(n, r, p, e, g_grado, g_grupo)
                        st.rerun()

            with st.expander("📂 Carga Masiva", expanded=False):
                up = st.file_uploader("CSV", type="csv")
                if up:
                    df = pd.read_csv(up)
                    if st.button("Procesar"):
                        for _, row in df.iterrows():
                            mail = row.get('email', '')
                            gr = row.get('grado', '')
                            gp = row.get('grupo', '')
                            crear_usuario(row['nombre'], row['rol'], str(row['password']), mail, str(gr), str(gp))
                        st.success("Cargado")
                        st.rerun()
            
            conn = get_connection()
            df_users = pd.read_sql("SELECT id, nombre, rol, password, grado, grupo FROM usuarios", conn)
            conn.close()
            df_edit = st.data_editor(df_users, hide_index=True, key="edit_users")
            
            c_save, c_del = st.columns([3,1])
            with c_save:
                if st.button("💾 Guardar Cambios"):
                    conn = get_connection()
                    c = conn.cursor()
                    for _, row in df_edit.iterrows():
                        c.execute("UPDATE usuarios SET nombre=?, password=?, rol=?, grado=?, grupo=? WHERE id=?",
                                  (row['nombre'], row['password'], row['rol'], row['grado'], row['grupo'], row['id']))
                    conn.commit()
                    conn.close()
                    st.success("Guardado")
                    st.rerun()
            with c_del:
                conn = get_connection()
                lista_borrar = pd.read_sql("SELECT nombre FROM usuarios WHERE nombre != 'admin'", conn)['nombre'].tolist()
                conn.close()
                if lista_borrar:
                    u_del = st.selectbox("Borrar usuario:", lista_borrar)
                    if st.button("💀 Eliminar"):
                        eliminar_usuario(u_del)
                        st.rerun()

        # --- TAB 3: HISTORIAL ---
        with tab3:
            st.subheader("📜 Historial")
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()
            
            st.divider()
            if st.button("🗑️ BORRAR TODO EL HISTORIAL", type="primary"):
                limpiar_historial_completo()
                st.success("Historial eliminado.")
                time.sleep(1)
                st.rerun()

    else:
        # VISTA ALUMNO
        conn = get_connection()
        data = pd.read_sql("SELECT saldo, grado, grupo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
        conn.close()
        st.metric(f"Mi Saldo ({data['grado']}{data['grupo']})", f"${data['saldo']:,.2f}")
        
        st.subheader("Movimientos")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario'])), use_container_width=True)
        conn.close()