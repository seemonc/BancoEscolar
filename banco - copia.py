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
# 2. BASE DE DATOS (AUTO-ACTUALIZABLE)
# ==========================================
def get_connection():
    return sqlite3.connect('banco_escolar.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Estructura base con GRADO y GRUPO
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, rol TEXT, saldo REAL, password TEXT, email TEXT,
                  grado TEXT, grupo TEXT)''') 
    
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, tipo TEXT)''')
    
    # MIGRACIÓN AUTOMÁTICA (Agrega columnas si faltan en tu archivo actual)
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN grado TEXT")
        c.execute("ALTER TABLE usuarios ADD COLUMN grupo TEXT")
    except:
        pass # Si ya existen, no pasa nada
    
    # Migración de Email (por si acaso)
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
    except:
        pass

    # Admin por defecto
    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, email, grado, grupo) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  ('admin', 'admin', 1000000, '1234', 'admin@escuela.edu', '', ''))
        conn.commit()
    conn.close()

# ==========================================
# 3. LÓGICA DE NEGOCIO
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

# --- LOGIN ---
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
    # --- SIDEBAR ---
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
        
        tab1, tab2, tab3 = st.tabs(["⚡ Operaciones (Individual/Masivo)", "👥 Gestión de Alumnos", "📊 Historial"])

        # --- TAB 1: OPERACIONES CON FILTROS ---
        with tab1:
            st.write("Selecciona cómo quieres trabajar hoy:")
            tipo_op = st.radio("Modo de Operación:", ["Individual (Uno por uno)", "Masiva (Por Grupo/Grado)"], horizontal=True)
            
            conn = get_connection()
            # Traemos todos los datos necesarios para filtrar
            df_alumnos = pd.read_sql("SELECT nombre, grado, grupo FROM usuarios WHERE rol='alumno'", conn)
            conn.close()

            if df_alumnos.empty:
                st.warning("⚠️ No hay alumnos registrados.")
            else:
                # === MODO INDIVIDUAL ===
                if "Individual" in tipo_op:
                    c_multa, c_pago = st.columns(2)
                    lista_nombres = df_alumnos['nombre'].tolist()
                    
                    with c_multa:
                        st.error("🚨 Cobrar Multa")
                        u_sanc = st.selectbox("Alumno", lista_nombres, key="sanc")
                        m_sanc = st.selectbox("Motivo", list(CATALOGO_MULTAS.keys()), key="m_sanc")
                        v_sanc = CATALOGO_MULTAS[m_sanc]
                        st.write(f"Cobrar: **${v_sanc}**")
                        if st.button("Cobrar Multa"):
                            ejecutar_transaccion(u_sanc, st.session_state['usuario'], v_sanc, m_sanc, "multa")
                            st.toast(f"Cobrado a {u_sanc}", icon="✅")
                            time.sleep(1)
                            st.rerun()

                    with c_pago:
                        st.success("💵 Pagar Estímulo")
                        u_pay = st.selectbox("Alumno", lista_nombres, key="pay")
                        reason = st.text_input("Motivo")
                        amount = st.number_input("Monto", min_value=10, value=50)
                        if st.button("Pagar"):
                            ejecutar_transaccion(st.session_state['usuario'], u_pay, amount, reason, "ingreso")
                            st.toast(f"Pagado a {u_pay}", icon="✅")
                            time.sleep(1)
                            st.rerun()

                # === MODO MASIVO (LO NUEVO) ===
                else:
                    st.markdown("### 📢 Operaciones Masivas")
                    st.info("Usa los filtros para seleccionar a todo un salón.")
                    
                    # 1. BARRA DE FILTROS
                    c_fil1, c_fil2, c_fil3 = st.columns(3)
                    
                    # Obtener listas únicas para los filtros, ignorando vacíos
                    grados = [x for x in df_alumnos['grado'].unique() if x]
                    grupos = [x for x in df_alumnos['grupo'].unique() if x]
                    
                    filtro_grado = c_fil1.multiselect("Filtrar por Grado", grados)
                    filtro_grupo = c_fil2.multiselect("Filtrar por Grupo", grupos)
                    search_name = c_fil3.text_input("Buscar por nombre (Opcional)")
                    
                    # Aplicar filtros
                    df_filtered = df_alumnos.copy()
                    if filtro_grado:
                        df_filtered = df_filtered[df_filtered['grado'].isin(filtro_grado)]
                    if filtro_grupo:
                        df_filtered = df_filtered[df_filtered['grupo'].isin(filtro_grupo)]
                    if search_name:
                        df_filtered = df_filtered[df_filtered['nombre'].str.contains(search_name, case=False)]
                    
                    st.write(f"Usuarios seleccionados: **{len(df_filtered)}**")
                    st.dataframe(df_filtered, use_container_width=True)
                    
                    # 2. ACCIONES MASIVAS
                    st.divider()
                    col_mass_multa, col_mass_pago = st.columns(2)
                    
                    # MULTA MASIVA
                    with col_mass_multa:
                        st.error("🚨 Multar a TODOS los filtrados")
                        reason_mass_m = st.selectbox("Infracción Masiva", list(CATALOGO_MULTAS.keys()), key="mass_m")
                        val_mass_m = CATALOGO_MULTAS[reason_mass_m]
                        
                        if st.button("Aplicar Multa Masiva"):
                            if not df_filtered.empty:
                                progress = st.progress(0)
                                for idx, row in enumerate(df_filtered.iterrows()):
                                    _, row = row
                                    ejecutar_transaccion(row['nombre'], st.session_state['usuario'], val_mass_m, reason_mass_m, "multa")
                                    # Actualizar barra de progreso
                                    progress.progress((idx + 1) / len(df_filtered))
                                st.success(f"¡Listo! Se cobró a {len(df_filtered)} alumnos.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("No hay alumnos en la lista filtrada.")

                    # PAGO MASIVO
                    with col_mass_pago:
                        st.success("💵 Pagar a TODOS los filtrados")
                        reason_mass_p = st.text_input("Motivo del Pago Masivo", "Beca Grupal")
                        val_mass_p = st.number_input("Monto por alumno", min_value=10, value=50, key="mass_p")
                        
                        if st.button("Realizar Pago Masivo"):
                            if not df_filtered.empty:
                                progress = st.progress(0)
                                for idx, row in enumerate(df_filtered.iterrows()):
                                    _, row = row
                                    ejecutar_transaccion(st.session_state['usuario'], row['nombre'], val_mass_p, reason_mass_p, "ingreso")
                                    progress.progress((idx + 1) / len(df_filtered))
                                st.success(f"¡Listo! Se pagó a {len(df_filtered)} alumnos.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("No hay alumnos en la lista filtrada.")

        # --- TAB 2: GESTIÓN CON GRADO Y GRUPO ---
        with tab2:
            st.header("🗂️ Directorio Escolar")
            
            # REGISTRO MANUAL (ACTUALIZADO CON GRADO Y GRUPO)
            with st.expander("➕ Registro Manual", expanded=False):
                with st.form("alta"):
                    c1, c2, c3 = st.columns(3)
                    n = c1.text_input("Usuario (ID)")
                    p = c2.text_input("Contraseña", value="1234")
                    e = c3.text_input("Email")
                    
                    c4, c5, c6 = st.columns(3)
                    r = c4.selectbox("Rol", ["alumno", "profesor"])
                    g_grado = c5.text_input("Grado (Ej. 1, 2, 3)")
                    g_grupo = c6.text_input("Grupo (Ej. A, B, C)")
                    
                    if st.form_submit_button("Crear"):
                        if crear_usuario(n, r, p, e, g_grado, g_grupo):
                            st.success(f"Creado: {n}")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Ya existe")

            # CARGA MASIVA (ACTUALIZADO)
            with st.expander("📂 Carga Masiva (Excel/CSV)", expanded=False):
                st.markdown("Columnas: `nombre`, `rol`, `password`, `email`, `grado`, `grupo`")
                up = st.file_uploader("CSV", type="csv")
                if up:
                    df = pd.read_csv(up)
                    if st.button("Procesar"):
                        count = 0
                        for _, row in df.iterrows():
                            # Validar campos opcionales
                            mail = row['email'] if 'email' in row else ''
                            gr = row['grado'] if 'grado' in row else ''
                            gp = row['grupo'] if 'grupo' in row else ''
                            
                            if crear_usuario(row['nombre'], row['rol'], str(row['password']), mail, str(gr), str(gp)):
                                count += 1
                        st.success(f"{count} importados.")
                        time.sleep(1)
                        st.rerun()

            st.divider()

            # EDITOR
            st.subheader("📝 Editar Datos")
            conn = get_connection()
            df_users = pd.read_sql("SELECT id, nombre, rol, password, email, grado, grupo, saldo FROM usuarios", conn)
            conn.close()

            df_editado = st.data_editor(
                df_users,
                key="editor",
                column_config={
                    "id": st.column_config.NumberColumn(disabled=True),
                    "saldo": st.column_config.NumberColumn(disabled=True),
                    "password": st.column_config.TextColumn("Contraseña"),
                    "grado": st.column_config.TextColumn("Grado"),
                    "grupo": st.column_config.TextColumn("Grupo"),
                },
                hide_index=True
            )

            c_save, c_del = st.columns([3,1])
            with c_save:
                if st.button("💾 Guardar Cambios"):
                    conn = get_connection()
                    c = conn.cursor()
                    for i, row in df_editado.iterrows():
                        c.execute("UPDATE usuarios SET nombre=?, password=?, email=?, rol=?, grado=?, grupo=? WHERE id=?",
                                  (row['nombre'], row['password'], row['email'], row['rol'], row['grado'], row['grupo'], row['id']))
                    conn.commit()
                    conn.close()
                    st.success("Guardado.")
                    time.sleep(0.5)
                    st.rerun()
            
            with c_del:
                conn = get_connection()
                lista = pd.read_sql("SELECT nombre FROM usuarios WHERE nombre != 'admin'", conn)['nombre'].tolist()
                conn.close()
                if lista:
                    u_del = st.selectbox("Borrar:", lista)
                    if st.button("💀 Confirmar"):
                        eliminar_usuario(u_del)
                        st.warning("Eliminado")
                        time.sleep(0.5)
                        st.rerun()

        # --- TAB 3: HISTORIAL ---
        with tab3:
            conn = get_connection()
            st.dataframe(pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn), use_container_width=True)
            conn.close()

    # VISTA ALUMNO
    else:
        conn = get_connection()
        data = pd.read_sql("SELECT saldo, grado, grupo FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
        conn.close()
        
        st.markdown(f"""
        <div style="background-color: #2ecc7120; padding: 15px; border-radius: 10px; border: 2px solid #2ecc71; text-align: center;">
            <h4 style="margin:0;">{data['grado']}° {data['grupo']}</h4>
            <h1 style="color: #27ae60; margin:0;">${data['saldo']:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("Transferir")
        conn = get_connection()
        # Filtro: Los alumnos solo ven compañeros de su mismo grupo para transferir (opcional)
        dests = pd.read_sql("SELECT nombre FROM usuarios WHERE rol='alumno' AND nombre!=?", conn, params=(st.session_state['usuario'],))['nombre'].tolist()
        conn.close()
        
        with st.form("tr"):
            d = st.selectbox("Para:", dests) if dests else None
            m = st.number_input("Monto", min_value=1.0)
            c = st.text_input("Concepto")
            if st.form_submit_button("Enviar"):
                if d and data['saldo'] >= m:
                    ejecutar_transaccion(st.session_state['usuario'], d, m, c, "transferencia")
                    st.success("Enviado")
                    st.rerun()
                else:
                    st.error("Error")
        
        st.subheader("Movimientos")
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT fecha, concepto, monto, tipo FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario'])), use_container_width=True)
        conn.close()