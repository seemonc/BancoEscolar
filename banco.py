import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import random

# INTENTO DE IMPORTAR PLOTLY
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")

# ESTILOS CSS
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    div[data-testid="stMetric"] {background-color: #f0f2f6; border-radius: 10px; padding: 15px; border-left: 5px solid #0095a3;}
    .admin-alert {padding: 15px; background-color: #ffebee; color: #c62828; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# INICIALIZAR ESTADO (SESSION STATE)
if 'lang' not in st.session_state: st.session_state['lang'] = 'ES'
if 'currency' not in st.session_state: st.session_state['currency'] = 'MXN'

# CONSTANTES
RATES = {'MXN': 1.0, 'USD': 0.05, 'EUR': 0.045}
SYMBOLS = {'MXN': '$', 'USD': 'US$', 'EUR': '€'}
PERMISO_TIENDA = ['admin', 'profesor']

def fmt_money(val): 
    moneda = st.session_state['currency']
    return f"{SYMBOLS[moneda]}{val * RATES[moneda]:,.2f}"

TRANS = {
    'ES': {
        'send_btn': 'Enviar Dinero', 'success_buy': '¡Compra exitosa!', 
        'error_funds': 'Saldo insuficiente', 'no_stock': 'Agotado',
        'ops': 'Operaciones', 'store': 'Tienda', 'hist': 'Historial'
    },
    'EN': {'send_btn': 'Send Money', 'success_buy': 'Success!', 'error_funds': 'Insufficient funds', 'no_stock': 'Out of stock', 'ops': 'Operations', 'store': 'Store', 'hist': 'History'},
    'FR': {'send_btn': 'Envoyer', 'success_buy': 'Succès!', 'error_funds': 'Fonds insuffisants', 'no_stock': 'Épuisé', 'ops': 'Opérations', 'store': 'Boutique', 'hist': 'Historique'}
}

def T(key): 
    result = TRANS.get(st.session_state['lang'], {}).get(key, key)
    return result if result is not None else key

# ==========================================
# 2. BASE DE DATOS (NUEVO NOMBRE PARA FORZAR RESET)
# ==========================================
DB_NAME = 'banco_summerhill_v2.db' # <--- ESTO ARREGLA EL ERROR DE 8 VALUES

def get_connection(): return sqlite3.connect(DB_NAME)
def generar_cuenta(): return str(random.randint(10000000, 99999999))

def init_db():
    conn = get_connection(); c = conn.cursor()
    
    # 1. USUARIOS
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, 
        nombre TEXT UNIQUE, 
        rol TEXT, 
        saldo REAL, 
        password TEXT, 
        email TEXT, 
        grado TEXT, 
        grupo TEXT, 
        cuenta TEXT, 
        saldo_cajita REAL DEFAULT 0
    )''')
    
    # 2. TRANSACCIONES (CON LA COLUMNA DE AUDITORÍA ASEGURADA)
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones (
        id INTEGER PRIMARY KEY, 
        fecha TEXT, 
        remitente TEXT, 
        destinatario TEXT, 
        monto REAL, 
        concepto TEXT, 
        tipo TEXT, 
        estado TEXT DEFAULT 'completado', 
        autorizado_por TEXT DEFAULT 'Sistema'
    )''')
    
    # 3. OTRAS TABLAS
    c.execute('''CREATE TABLE IF NOT EXISTS solicitudes (id INTEGER PRIMARY KEY, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, fecha TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, stock INTEGER, icono TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_ahorro (id INTEGER PRIMARY KEY, tasa REAL, activo INTEGER)''')

    # DATA DEFAULT
    if not c.execute("SELECT * FROM usuarios WHERE nombre='admin'").fetchone():
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, cuenta) VALUES (?, ?, ?, ?, ?)", ('admin', 'admin', 999999, '1234', generar_cuenta()))
    
    if not c.execute("SELECT * FROM config_ahorro").fetchone():
        c.execute("INSERT INTO config_ahorro (tasa, activo) VALUES (5.0, 1)")

    conn.commit(); conn.close()

# ==========================================
# 3. LÓGICA DE NEGOCIO
# ==========================================
def login(u, p):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM usuarios WHERE nombre=? AND password=?", conn, params=(u, p))
    conn.close()
    return df

def transaccion_core(origen, destino, monto, concepto, tipo, estado="completado", operador="Sistema"):
    conn = get_connection(); c = conn.cursor()
    f = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # FORMATO ESTÁNDAR
    try:
        c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (monto, origen))
        c.execute("UPDATE usuarios SET saldo=saldo+? WHERE nombre=?", (monto, destino))
        # INSERT CON 8 VALORES EXACTOS
        c.execute("""
            INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) 
            VALUES (?,?,?,?,?,?,?,?)
        """, (f, origen, destino, monto, concepto, tipo, estado, operador))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error DB: {e}")
        return False
    finally: conn.close()

# CALLBACKS (PARA QUE LOS BOTONES FUNCIONEN SÍ O SÍ)
def cb_comprar(usuario, id_prod):
    conn = get_connection(); c = conn.cursor()
    p = c.execute("SELECT * FROM productos WHERE id=?", (id_prod,)).fetchone()
    if p:
        nombre, precio, stock = p[1], p[2], p[3]
        saldo = c.execute("SELECT saldo FROM usuarios WHERE nombre=?", (usuario,)).fetchone()[0]
        if stock > 0 and saldo >= precio:
            # RESTAR DINERO Y STOCK
            c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (precio, usuario))
            c.execute("UPDATE productos SET stock=stock-1 WHERE id=?", (id_prod,))
            # REGISTRAR
            f = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)",
                      (f, usuario, "TIENDA", precio, f"Compra: {nombre}", "compra", "pendiente", "TIENDA"))
            conn.commit()
            st.session_state['msg'] = {'tipo': 'success', 'texto': f"Compraste {nombre}"}
            st.session_state['balloons'] = True
        else:
            st.session_state['msg'] = {'tipo': 'error', 'texto': "Saldo insuficiente o sin stock"}
    conn.close()

def crud_usuario(operacion, nombre, rol, pwd="1234"):
    conn = get_connection(); c = conn.cursor()
    try:
        if operacion == "crear":
            c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, cuenta) VALUES (?, ?, ?, ?, ?)", 
                      (nombre, rol, 0, pwd, generar_cuenta()))
            conn.commit(); conn.close(); return True
        return False
    except Exception as e:
        print(f"Error CRUD: {e}"); conn.close(); return False

def cb_pagar_rendimientos(tasa):
    conn = get_connection(); c = conn.cursor()
    f = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = c.execute("SELECT nombre, saldo_cajita FROM usuarios WHERE saldo_cajita > 0").fetchall()
    count = 0
    for u in users:
        nombre, saldo_c = u[0], u[1]
        ganancia = saldo_c * (tasa / 100.0)
        if ganancia > 0:
            c.execute("UPDATE usuarios SET saldo_cajita=saldo_cajita+? WHERE nombre=?", (ganancia, nombre))
            c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)",
                      (f, "BANCO", nombre, ganancia, f"Rendimiento {tasa}%", "interes", "completado", "BANCO CENTRAL"))
            count += 1
    conn.commit(); conn.close()
    st.session_state['msg'] = {'tipo': 'success', 'texto': f"Pagado a {count} usuarios"}

# ==========================================
# 4. INTERFAZ (UI)
# ==========================================
init_db()

# GESTIÓN DE MENSAJES GLOBAL
if 'msg' in st.session_state:
    m = st.session_state['msg']
    if m['tipo'] == 'success': st.success(m['texto'])
    else: st.error(m['texto'])
    del st.session_state['msg']
if 'balloons' in st.session_state:
    st.balloons(); del st.session_state['balloons']

# LOGIN
if 'usuario' not in st.session_state:
    col1, col2 = st.columns([1,2])
    archivo_logo = "logo.png" if os.path.exists("logo.png") else None
    if archivo_logo: col1.image(archivo_logo, width=150)
    col2.title("Banco Summerhill")
    
    u = st.text_input("Usuario", key="login_u")
    p = st.text_input("Contraseña", type="password", key="login_p")
    
    # SELECTOR DE IDIOMA EN LOGIN (SOLUCIONADO CAMBIO INSTANTANEO)
    lang_code = st.selectbox("Idioma / Language", ['ES', 'EN', 'FR'])
    if lang_code != st.session_state['lang']:
        st.session_state['lang'] = lang_code
        if lang_code == 'ES': st.session_state['currency'] = 'MXN'
        elif lang_code == 'EN': st.session_state['currency'] = 'USD'
        else: st.session_state['currency'] = 'EUR'
        st.rerun()

    if st.button("Entrar"):
        ud = login(u, p)
        if not ud.empty:
            st.session_state['usuario'] = u
            st.session_state['rol'] = ud.iloc[0]['rol']
            st.rerun()
        else: st.error("Acceso denegado")

else:
    # DATA USUARIO ACTUAL
    conn = get_connection()
    user_row = pd.read_sql("SELECT * FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
    
    # ALERTAS ADMIN
    pending_delivery = 0
    if st.session_state['rol'] in PERMISO_TIENDA:
        pending_delivery = len(pd.read_sql("SELECT * FROM transacciones WHERE tipo='compra' AND estado='pendiente'", conn))
    conn.close()

    # SIDEBAR
    with st.sidebar:
        archivo_logo = "logo.png" if os.path.exists("logo.png") else None
        if archivo_logo: st.image(archivo_logo, width=80)
        st.write(f"Hola, **{st.session_state['usuario']}**")
        st.caption(f"Rol: {st.session_state['rol']}")
        
        if pending_delivery > 0:
            st.error(f"🚨 {pending_delivery} Entregas pendientes")
        
        st.divider()
        
        # CONFIGURACIÓN (MONEDA)
        st.write("⚙️ Configuración")
        sel_lang = st.selectbox("Idioma", ['ES', 'EN', 'FR'], index=['ES', 'EN', 'FR'].index(st.session_state['lang']), key="sb_lang")
        
        # LOGICA DE CAMBIO DE MONEDA ARREGLADA
        if sel_lang != st.session_state['lang']:
            st.session_state['lang'] = sel_lang
            if sel_lang == 'ES': st.session_state['currency'] = 'MXN'
            elif sel_lang == 'EN': st.session_state['currency'] = 'USD'
            elif sel_lang == 'FR': st.session_state['currency'] = 'EUR'
            st.rerun()
            
        st.caption(f"Moneda: {st.session_state['currency']}")
        
        if st.button("Cerrar Sesión"):
            del st.session_state['usuario']
            st.rerun()

    # TABS
    pestanas = ["Inicio", "Tienda", "Cajita", "Historial", "Analytics"]
    if st.session_state['rol'] == 'admin': pestanas += ["Gestión", "Banco Central", "Auditoría"]
    
    tabs = st.tabs(pestanas)

    # --- 1. INICIO (TRANSFERENCIAS) ---
    with tabs[0]:
        st.metric("Saldo Disponible", fmt_money(user_row['saldo']))
        st.write("#### 💸 Enviar Dinero")
        
        col_a, col_b = st.columns(2)
        # BUSCAR DESTINATARIO
        conn = get_connection()
        all_users = pd.read_sql("SELECT nombre FROM usuarios WHERE nombre != ?", conn, params=(st.session_state['usuario'],))['nombre'].tolist()
        conn.close()
        
        dest = col_a.selectbox("Destinatario", all_users)
        monto = col_b.number_input("Monto", min_value=1.0)
        motivo = st.text_input("Motivo / Concepto")
        
        if st.button(T('send_btn') or 'Send Money', type="primary"):
            real_monto = monto / RATES[st.session_state['currency']] # CONVERTIR A BASE (MXN)
            if user_row['saldo'] >= real_monto:
                if transaccion_core(st.session_state['usuario'], dest, real_monto, motivo, "transferencia", operador=st.session_state['usuario']):
                    st.success("Enviado con éxito")
                    time.sleep(1); st.rerun()
                else: st.error("Error en DB")
            else: st.error(T('error_funds'))

    # --- 2. TIENDA ---
    with tabs[1]:
        conn = get_connection()
        prods = pd.read_sql("SELECT * FROM productos WHERE stock > 0", conn)
        conn.close()
        
        if prods.empty: st.info(T('no_stock'))
        else:
            for i, row in prods.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1,3,2])
                    c1.markdown(f"<h1 style='text-align:center;'>{row['icono']}</h1>", unsafe_allow_html=True)
                    c2.write(f"**{row['nombre']}**")
                    c2.caption(f"Stock: {row['stock']}")
                    c3.write(f"**{fmt_money(row['precio'])}**")
                    # BOTÓN SEGURO CON CALLBACK
                    c3.button("Comprar", key=f"shop_{row['id']}", on_click=cb_comprar, args=(st.session_state['usuario'], row['id']))
                    st.divider()

    # --- 3. CAJITA ---
    with tabs[2]:
        st.metric("Ahorrado en Cajita", fmt_money(user_row['saldo_cajita']))
        
        c1, c2 = st.columns(2)
        m_cajita = c1.number_input("Monto Cajita", min_value=1.0, key="val_cajita")
        
        real_monto_cajita = m_cajita / RATES[st.session_state['currency']]
        
        if c2.button("📥 Depositar"):
            # RESTAR DE SALDO, SUMAR A CAJITA
            conn = get_connection(); c = conn.cursor()
            if user_row['saldo'] >= real_monto_cajita:
                c.execute("UPDATE usuarios SET saldo=saldo-?, saldo_cajita=saldo_cajita+? WHERE nombre=?", (real_monto_cajita, real_monto_cajita, st.session_state['usuario']))
                conn.commit(); conn.close()
                st.success("Guardado"); time.sleep(1); st.rerun()
            else:
                st.error("No tienes suficiente saldo disponible")
                conn.close()

        if c2.button("📤 Retirar"):
            # RESTAR DE CAJITA, SUMAR A SALDO
            conn = get_connection(); c = conn.cursor()
            if user_row['saldo_cajita'] >= real_monto_cajita:
                c.execute("UPDATE usuarios SET saldo=saldo+?, saldo_cajita=saldo_cajita-? WHERE nombre=?", (real_monto_cajita, real_monto_cajita, st.session_state['usuario']))
                conn.commit(); conn.close()
                st.success("Retirado"); time.sleep(1); st.rerun()
            else:
                st.error("No tienes eso en la cajita")
                conn.close()

    # --- 4. HISTORIAL ---
    with tabs[3]:
        st.write("#### Movimientos")
        conn = get_connection()
        # LEER CON FORMAT='MIXED' PARA EVITAR EL ERROR DE FECHAS
        df = pd.read_sql("SELECT * FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario']))
        conn.close()
        
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'], format='mixed')
            # AJUSTAR MONEDA VISUAL
            rate = RATES[st.session_state['currency']]
            df['monto_visual'] = df['monto'] * rate
            df_show = df[['fecha', 'remitente', 'destinatario', 'monto_visual', 'concepto', 'tipo', 'autorizado_por']]
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Sin movimientos")

    # --- 5. ANALYTICS ---
    with tabs[4]:
        if HAS_PLOTLY:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM transacciones WHERE remitente=? OR destinatario=?", conn, params=(st.session_state['usuario'], st.session_state['usuario']))
            conn.close()
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], format='mixed')
                fig = px.line(df, x='fecha', y='monto', title="Historial")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 Analytics: Instala 'plotly' en requirements.txt")

    # === PESTAÑAS ADMIN ===
    if st.session_state['rol'] == 'admin':
        
        # --- GESTION ---
        with tabs[5]:
            st.write("### Crear Usuario")
            nu = st.text_input("Nuevo Usuario", key="new_u")
            np = st.text_input("Nueva Contraseña", key="new_p")
            nr = st.selectbox("Rol", ["alumno", "profesor", "administrativo"])
            if st.button("Crear Usuario"):
                if crud_usuario("crear", nu, nr, pwd=np): st.success("Creado")
                else: st.error("Error al crear")

        # --- BANCO CENTRAL (PAGAR RENDIMIENTOS) ---
        with tabs[6]:
            st.write("### 🏦 Banco Central")
            conn = get_connection()
            conf = pd.read_sql("SELECT * FROM config_ahorro", conn).iloc[0]
            conn.close()
            
            st.info(f"Tasa Actual: {conf['tasa']}%")
            if st.button("💸 PAGAR RENDIMIENTOS A TODOS"):
                cb_pagar_rendimientos(conf['tasa']) # USA CALLBACK
        
        # --- AUDITORIA ---
        with tabs[7]:
            st.write("### 🕵️‍♂️ Auditoría Total")
            conn = get_connection()
            df_audit = pd.read_sql("SELECT * FROM transacciones ORDER BY id DESC", conn)
            conn.close()
            st.dataframe(df_audit)