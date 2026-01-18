import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
# --- CÓDIGO TEMPORAL DE DIAGNÓSTICO ---
import os
st.write("📂 ESTOY BUSCANDO EN:", os.getcwd())
st.write("👀 ARCHIVOS QUE VEO AQUÍ:", os.listdir())
st.write("¿EXISTE LOGO.PNG?:", os.path.exists("logo.png"))
# --------------------------------------
import os

# ==========================================
# 1. CONFIGURACIÓN E IMAGEN DE PESTAÑA
# ==========================================
# Intentamos poner el logo en la pestaña del navegador. 
# Si falla (por si acaso), pone un banco normal.
try:
    st.set_page_config(page_title="Banco Escolar SEP", page_icon="logo.png", layout="wide")
except:
    st.set_page_config(page_title="Banco Escolar SEP", page_icon="🏦", layout="wide")

ROLES_ADMINISTRATIVOS = ['admin', 'profesor', 'director', 'administrativo']
CATALOGO_MULTAS = {
    "Incumplimiento de Tarea": 200, "Interrupción de Clase": 150,
    "Falta de Respeto (Verbal)": 500, "Uso de Celular": 100,
    "Área sucia": 50, "Daño a Material": 300
}

# ==========================================
# 2. BASE DE DATOS
# ==========================================
def get_connection():
    return sqlite3.connect('banco_escolar.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabla Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, rol TEXT, saldo REAL, password TEXT, email TEXT,
                  grado TEXT, grupo TEXT)''') 
    
    # Tabla Transacciones
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, tipo TEXT)''')
    
    # Actualizaciones automáticas (por si vienes de una versión vieja)
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN grado TEXT")
        c.execute("ALTER TABLE usuarios ADD COLUMN grupo TEXT")
        c.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
    except:
        pass

    # Crear Admin si no existe
    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  ('admin', 'admin', 1000000, '1234', 'admin@escuela.edu', '', ''))
        conn.commit()
    conn.close()

# ==========================================
# 3. LÓGICA DEL SISTEMA
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

# --- PANTALLA DE INICIO DE SESIÓN ---
if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        # AQUÍ PONEMOS EL LOGO GRANDE
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>🏦</h1>", unsafe_allow_html=True)
            
        st.markdown("<h1 style='text-align: center;'>Banco Escolar</h1>", unsafe_allow_html=True)
        st.info("Ingresa tus credenciales para acceder.")
        
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", use_container_width=True):
            df = login(user, pw)
            if not df.empty:
                st.session_state['usuario'] = user
                st.session_state['rol'] = df.iloc[0]['rol']
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# --- DENTRO DEL SISTEMA ---
else:
    # BARRA LATERAL (SIDEBAR)
    conn = get_connection()
    try:
        saldo_admin = pd.read_sql("SELECT saldo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]['saldo']
    except:
        saldo_admin = 0
    conn.close()

    with st.sidebar:
        # LOGO PEQUEÑO EN EL MENÚ
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
            
        st.markdown(f"## 👤 {st.session_state['usuario']}")
        st.caption(f"Rol: {st.session_state['rol'].upper()}")
        st.metric("💰 MI SALDO", f"${saldo_admin:,.2f}")
        st.divider()
        if st.button("Cerrar Sesión", type="primary"):
            del st.session_state['usuario']
            st.rerun()

    # === VISTA DE PROFESOR / DIRECTOR ===
    if st.session_state['rol'] in ROLES_ADMINISTRATIVOS:
        st.title("Panel de Control Escolar")
        
        tab1, tab2, tab3 = st.tabs(["⚡ Operaciones (Cobros/Pagos)", "👥 Gestión de Alumnos", "📊 Historial"])

        # --- TAB 1: OPERACIONES ---
        with tab1:
            st.markdown("### 🔍 Buscador de Alumnos")
            
            conn = get_connection()
            df_full = pd.read_sql("SELECT nombre, grado, grupo, saldo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()

            if df_full.empty:
                st.warning("⚠️ No hay alumnos registrados. Ve a la pestaña 'Gestión' para agregar uno.")
            else:
                # FILTROS
                c_fil1, c_fil2, c_fil3 = st.columns(3)
                lista_grados = ["Todos"] + sorted([x for x in df_full['grado'].unique() if x])
                lista_grupos = ["Todos"] + sorted([x for x in df_full['grupo'].unique() if x])
                
                filtro_grado = c_fil1.selectbox("Filtrar Grado", lista_grados)
                filtro_grupo = c_fil2.selectbox("Filtrar Grupo", lista_grupos)
                busqueda_txt = c_fil3.text_input("Buscar por Nombre", placeholder="Ej. Juan Pérez")

                # APLICAR FILTROS
                df_filtrado = df_full.copy()
                if filtro_grado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['grado'] == filtro_grado]
                if filtro_grupo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['grupo'] == filtro_grupo]
                if busqueda_txt:
                    df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(busqueda_txt, case=False)]

                st.divider()

                # SELECCIÓN DE MODO
                op_mode = st.radio("Modo de Operación:", ["Individual", "Selección Múltiple (Checklist)"], horizontal=True)

                # --- MODO 1: INDIVIDUAL ---
                if op_mode == "Individual":
                    lista_nombres = df_filtrado['nombre'].tolist()
                    if lista_nombres:
                        col_ind_1, col_ind_2 = st.columns(2)
                        with col_ind_1:
                            st.error("🚨 COBRAR MULTA")
                            u_sanc = st.selectbox("Alumno a multar", lista_nombres, key="u_ind_m")
                            m_sanc = st.selectbox("Motivo de la multa", list(CATALOGO_MULTAS.keys()), key="m_ind")
                            if st.button("Aplicar Multa Individual"):
                                ejecutar_transaccion(u_sanc, st.session_state['usuario'], CATALOGO_MULTAS[m_sanc], m_sanc, "multa")
                                st.toast(f"Multa aplicada a {u_sanc}", icon="✅")
                                time.sleep(1)
                                st.rerun()
                        with col_ind_2:
                            st.success("💵 PAGAR ESTÍMULO")
                            u_pay = st.selectbox("Alumno a pagar", lista_nombres, key="u_ind_p")
                            a_pay = st.number_input("Cantidad ($)", 50, key="a_ind")
                            r_pay = st.text_input("Motivo del pago", "Participación", key="r_ind_p")
                            if st.button("Realizar Pago Individual"):
                                ejecutar_transaccion(st.session_state['usuario'], u_pay, a_pay, r_pay, "ingreso")
                                st.toast(f"Pago enviado a {u_pay}", icon="✅")
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.warning("No se encontraron alumnos con esos filtros.")

                # --- MODO 2: CHECKLIST (SELECCIÓN MÚLTIPLE) ---
                else: 
                    st.info("👇 Marca las casillas de los alumnos a los que quieras aplicar la acción.")
                    
                    # Insertamos columna para el checkbox
                    df_filtrado.insert(0, "Seleccionar", False)
                    
                    # Tabla editable
                    edited_df = st.data_editor(
                        df_filtrado,
                        column_config={
                            "Seleccionar": st.column_config.CheckboxColumn("Elegir", default=False),
                            "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                            "grado": st.column_config.TextColumn("Grado", disabled=True),
                            "grupo": st.column_config.TextColumn("Grupo", disabled=True),
                            "saldo": st.column_config.NumberColumn("Saldo Actual", disabled=True),
                        },
                        disabled=["nombre", "grado", "grupo", "saldo"],
                        hide_index=True,
                        key="editor_seleccion",
                        use_container_width=True
                    )

                    # Obtener seleccionados
                    alumnos_seleccionados = edited_df[edited_df["Seleccionar"] == True]["nombre"].tolist()
                    st.write(f"Has seleccionado a: **{len(alumnos_seleccionados)} alumnos**")

                    if alumnos_seleccionados:
                        c_mass_1, c_mass_2 = st.columns(2)
                        with c_mass_1:
                            st.error("🚨 Multar a TODOS los seleccionados")
                            m_mass = st.selectbox("Motivo Masivo", list(CATALOGO_MULTAS.keys()), key="m_mass")
                            if st.button("🔥 EJECUTAR MULTAS"):
                                bar = st.progress(0)
                                for i, user in enumerate(alumnos_seleccionados):
                                    ejecutar_transaccion(user, st.session_state['usuario'], CATALOGO_MULTAS[m_mass], m_mass, "multa")
                                    bar.progress((i+1)/len(alumnos_seleccionados))
                                st.success("¡Operación completada!")
                                time.sleep(1)
                                st.rerun()

                        with c_mass_2:
                            st.success("💵 Pagar a TODOS los seleccionados")
                            r_mass = st.text_input("Motivo Pago", "Beca", key="r_mass")
                            a_mass = st.number_input("Monto por alumno", 50, key="a_mass")
                            if st.button("🔥 EJECUTAR PAGOS"):
                                bar = st.progress(0)
                                for i, user in enumerate(alumnos_seleccionados):
                                    ejecutar_transaccion(st.session_state['usuario'], user, a_mass, r_mass, "ingreso")
                                    bar.progress((i+1)/len(alumnos_seleccionados))
                                st.success("¡Operación completada!")
                                time.sleep(1)
                                st.rerun()

        # --- TAB 2: GESTIÓN ---
        with tab2:
            st.header("🗂️ Gestión de Alumnos")
            
            with st.expander("➕ Registro Manual", expanded=False):
                with st.form("alta"):
                    c1, c2, c3 = st.columns(3)
                    n = c1.text_input("Nombre Usuario")
                    p = c2.text_input("Contraseña", value="1234")
                    e = c3.text_input("Email")
                    c4, c5, c6 = st.columns(3)
                    r = c4.selectbox("Rol", ["alumno", "profesor"])
                    g_grado = c5.text_input("Grado")
                    g_grupo = c6.text_input("Grupo")
                    if st.form_submit_button("Crear Usuario"):
                        if crear_usuario(n, r, p, e, g_grado, g_grupo):
                            st.success("Usuario creado.")
                            st.rerun()
                        else:
                            st.error("Error: El usuario ya existe.")

            with st.expander("📂 Carga Masiva (CSV)", expanded=False):
                up = st.file_uploader("Subir archivo CSV", type="csv")
                if up:
                    df = pd.read_csv(up)
                    if st.button("Procesar Archivo"):
                        for _, row in df.iterrows():
                            # Asegura que existan las columnas o pone vacío
                            mail = row.get('email', '')
                            gr = row.get('grado', '')
                            gp = row.get('grupo', '')
                            crear_usuario(row['nombre'], row['rol'], str(row['password']), mail, str(gr), str(gp))
                        st.success("Usuarios cargados exitosamente.")
                        st.rerun()
            
            st.divider()
            st.subheader("Editar Base de Datos")
            conn = get_connection()
            df_users = pd.read_sql("SELECT id, nombre, rol, password, grado, grupo FROM usuarios", conn)
            conn.close()
            
            # Tabla editable de usuarios
            df_edit = st.data_editor(df_users, hide_index=True, key="edit_users", use_container_width=True)
            
            c_save, c_del = st.columns([3,1])
            with c_save:
                if st.button("💾 Guardar Cambios en Tabla"):
                    conn = get_connection()
                    c = conn.cursor()
                    for _, row in df_edit.iterrows():
                        c.execute("UPDATE usuarios SET nombre=?, password=?, rol=?, grado=?, grupo=? WHERE id=?",
                                  (row['nombre'], row['password'], row['rol'], row['grado'], row['grupo'], row['id']))
                    conn.commit()
                    conn.close()
                    st.success("Cambios guardados.")
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
            st.subheader("📜 Historial de Transacciones")
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()
            
            st.divider()
            st.markdown("### ⚠️ Zona de Peligro")
            st.info("Utiliza este botón antes de empezar la presentación para borrar pruebas anteriores.")
            if st.button("🗑️ BORRAR TODO EL HISTORIAL", type="primary"):
                limpiar_historial_completo()
                st.success("Historial eliminado completamente.")
                time.sleep(1)
                st.rerun()

    # === VISTA DE ALUMNO ===
    else:
        conn = get_connection()
        data = pd.read_sql("SELECT saldo, grado, grupo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
        conn.close()
        st.metric(f"Mi Saldo ({data['grado']} {data['grupo']})", f"${data['saldo']:,.2f}")
        
        st.subheader("Mis Movimientos")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario'])), use_container_width=True)
        conn.close()