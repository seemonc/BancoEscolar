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
# 1. CONFIGURACIÓN Y ESTILOS (VISUALES RESTAURADOS)
# ==========================================
if os.path.exists("logo.png"):
    st.set_page_config(page_title="Banco Summerhill", page_icon="logo.png", layout="wide")
    archivo_logo = "logo.png"
else:
    st.set_page_config(page_title="Banco Summerhill", page_icon="🏦", layout="wide")
    archivo_logo = None

def cargar_estilos():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap');
        
        :root {
            --primary-color: #0095a3;
            --primary-dark: #007f8b;
            --primary-light: #006b77;
            --bg-light: #f5f7fa;
            --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            --text-dark: #1a1a1a;
            --text-light: #64748b;
            --border-light: #e8eef5;
            --card-bg: #ffffff;
            --card-shadow: 0 8px 24px rgba(0, 149, 163, 0.08);
        }
        
        /* MODO OSCURO */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-light: #0f1419;
                --bg-gradient: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
                --text-dark: #ffffff;
                --text-light: #b0b8c1;
                --border-light: #2d3748;
                --card-bg: #1a2332;
                --card-shadow: 0 8px 24px rgba(0, 149, 163, 0.12);
            }
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body, [class*="css"] { 
            font-family: 'Inter', sans-serif;
            background: var(--bg-gradient);
            min-height: 100vh;
            color: var(--text-dark);
        }
        
        /* TÍTULOS */
        h1 { 
            color: var(--primary-color) !important; 
            font-weight: 700 !important; 
            font-family: 'Poppins', sans-serif !important;
            font-size: 2.8rem !important;
            margin-bottom: 2rem !important;
            letter-spacing: -0.5px;
        }
        h2 { 
            color: var(--primary-color) !important; 
            font-weight: 700 !important; 
            font-family: 'Poppins', sans-serif !important;
            font-size: 1.8rem !important;
            margin-top: 2rem !important;
            margin-bottom: 1.5rem !important;
        }
        h3 { 
            color: var(--primary-color) !important; 
            font-weight: 600 !important; 
            font-family: 'Poppins', sans-serif !important;
            font-size: 1.3rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* CONTENEDOR PRINCIPAL */
        .main .block-container {
            padding-top: 3rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
            margin: 0 auto !important;
        }
        
        /* TARJETAS MÉTRICAS PREMIUM */
        div[data-testid="stMetric"] { 
            background: var(--card-bg) !important;
            border: 1px solid var(--border-light) !important;
            border-left: 6px solid var(--primary-color) !important;
            padding: 2rem !important;
            border-radius: 15px !important;
            box-shadow: var(--card-shadow) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-bottom: 1.5rem !important;
        }
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 12px 32px rgba(0, 149, 163, 0.15) !important;
            transform: translateY(-2px) !important;
        }
        div[data-testid="stMetricValue"] { 
            color: var(--primary-color) !important; 
            font-size: 2.8rem !important; 
            font-weight: 700 !important;
            font-family: 'Poppins', sans-serif !important;
            margin-top: 0.5rem !important;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--text-light) !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.3px;
        }
        
        /* BOTONES CON ESTILO PREMIUM */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 50%, var(--primary-light) 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            padding: 14px 28px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            width: 100% !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 6px 20px rgba(0, 149, 163, 0.25) !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
        }
        .stButton > button:hover { 
            transform: translateY(-3px) !important; 
            box-shadow: 0 10px 28px rgba(0, 149, 163, 0.35) !important;
            opacity: 1 !important;
        }
        .stButton > button:active { 
            transform: translateY(-1px) !important; 
        }
        
        /* INPUTS Y FORMULARIOS */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            border: 1.5px solid var(--border-light) !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            background-color: var(--card-bg) !important;
            color: var(--text-dark) !important;
        }
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(0, 149, 163, 0.1) !important;
            background-color: var(--card-bg) !important;
        }
        
        /* EXPANDERS */
        .stExpander {
            border-radius: 12px !important;
            border: 1px solid var(--border-light) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
            background-color: var(--card-bg) !important;
            margin-bottom: 1.5rem !important;
        }
        .stExpander > div > details > summary {
            padding: 1.2rem !important;
            font-weight: 600 !important;
            color: var(--primary-color) !important;
            font-size: 1.1rem !important;
        }
        
        /* ALERTAS Y TIPS */
        .financial-tip-good { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724; 
            padding: 1.5rem; 
            border-radius: 12px; 
            border-left: 6px solid #28a745; 
            margin-bottom: 1.5rem;
            box-shadow: 0 6px 16px rgba(40, 167, 69, 0.15);
            font-weight: 500;
        }
        .financial-tip-bad { 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24; 
            padding: 1.5rem; 
            border-radius: 12px; 
            border-left: 6px solid #dc3545; 
            margin-bottom: 1.5rem;
            box-shadow: 0 6px 16px rgba(220, 53, 69, 0.15);
            font-weight: 500;
        }
        
        .admin-alert {
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            color: #664d03; 
            padding: 1.5rem; 
            border-radius: 12px; 
            border-left: 6px solid #ff9800;
            text-align: center; 
            font-weight: 700; 
            font-size: 1.1rem; 
            margin-bottom: 2rem; 
            box-shadow: 0 8px 20px rgba(255, 152, 0, 0.2);
        }
        
        /* SIDEBAR */
        [data-testid="stSidebar"] {
            background: var(--card-bg) !important;
            box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08) !important;
        }
        [data-testid="stSidebar"] > div > div {
            padding: 2rem 1.5rem !important;
        }
        
        /* TABS */
        .stTabs > [role="tablist"] {
            background-color: transparent !important;
            border-bottom: 2px solid var(--border-light) !important;
            padding: 0 0 1rem 0 !important;
            gap: 2rem !important;
        }
        .stTabs > [role="tablist"] button {
            font-weight: 600 !important;
            font-size: 1rem !important;
            color: var(--text-light) !important;
            border-bottom: 3px solid transparent !important;
            padding: 0.8rem 0 !important;
            transition: all 0.3s ease !important;
        }
        .stTabs > [role="tablist"] button[aria-selected="true"] {
            color: var(--primary-color) !important;
            border-bottom-color: var(--primary-color) !important;
        }
        .stTabs > [role="tablist"] button:hover {
            color: var(--primary-color) !important;
        }
        
        /* DATAFRAMES */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
            margin: 1.5rem 0 !important;
        }
        
        /* DIVIDER */
        .divider {
            margin: 2rem 0 !important;
            border: none;
            border-top: 2px solid var(--border-light);
        }
        
        /* SUCCESS/ERROR */
        .stSuccess, [data-testid="stAlert"] {
            border-radius: 12px !important;
            padding: 1.2rem !important;
            margin: 1rem 0 !important;
            color: var(--text-dark) !important;
        }
        
        /* COLUMNS SPACING */
        .stColumn { padding: 1rem; }
        
        /* INFO BOX */
        .stInfo, [data-testid="stInfo"] {
            background-color: var(--card-bg) !important;
            color: var(--text-dark) !important;
            border-radius: 12px !important;
            border-left: 6px solid var(--primary-color) !important;
        }
        
        /* TEXT GENERAL */
        p, span, label, div {
            color: var(--text-dark) !important;
        }
        
        /* HIDE FOOTER */
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        .stDeployButton {display:none;}
        
        /* RESPONSIVE */
        @media only screen and (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 2rem !important;
            }
            h1 { font-size: 2rem !important; margin-bottom: 1.5rem !important; }
            h2 { font-size: 1.4rem !important; }
            div[data-testid="stMetricValue"] { font-size: 2rem !important; }
            div[data-testid="stMetric"] { padding: 1.5rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)
cargar_estilos()

# ==========================================
# 2. DEFINICIÓN DE ROLES Y PERMISOS
# ==========================================
ROLES_ADMIN = ['admin', 'director']
ROLES_DOCENTE = ['profesor']
ROLES_STAFF = ['administrativo']

PERMISO_TIENDA = ROLES_ADMIN + ROLES_DOCENTE      
PERMISO_AUTORIZAR = ROLES_ADMIN + ROLES_STAFF     
PERMISO_OPERAR = ROLES_ADMIN + ROLES_DOCENTE + ROLES_STAFF 

if 'lang' not in st.session_state: st.session_state['lang'] = 'ES'
if 'currency' not in st.session_state: st.session_state['currency'] = 'MXN'

RATES = {'MXN': 1.0, 'USD': 0.05, 'EUR': 0.045}
SYMBOLS = {'MXN': '$', 'USD': 'US$', 'EUR': '€'}

def fmt_money(val): 
    moneda = st.session_state['currency']
    return f"{SYMBOLS[moneda]}{val * RATES[moneda]:,.2f}"

TRANS = {
    'ES': {'send_btn': 'Enviar Dinero', 'success_buy': '¡Compra exitosa!', 'error_funds': 'Saldo insuficiente', 'no_stock': 'Agotado'},
    'EN': {'send_btn': 'Send Money', 'success_buy': 'Success!', 'error_funds': 'Insufficient funds', 'no_stock': 'Out of stock'},
    'FR': {'send_btn': 'Envoyer', 'success_buy': 'Succès!', 'error_funds': 'Fonds insuffisants', 'no_stock': 'Épuisé'}
}
# FIX PYLANCE: Asegurar que siempre devuelve string
def T(key): return str(TRANS.get(st.session_state['lang'], {}).get(key, key))

OPCIONES_MULTAS = {"---": 0, "Celular": 50, "No Tarea": 100, "Falta Respeto": 500}
OPCIONES_PAGOS = {"---": 0, "Tarea": 100, "Proyecto": 200, "Participación": 20}

# ==========================================
# 3. BASE DE DATOS (NUEVA VERSIÓN v4 - LIMPIA)
# ==========================================
DB_NAME = 'banco_summerhill_v4.db' # CAMBIO DE NOMBRE PARA ARREGLAR "8 VALUES"

def get_connection(): return sqlite3.connect(DB_NAME)
def generar_cuenta(): return str(random.randint(10000000, 99999999))

def init_db():
    conn = get_connection(); c = conn.cursor()
    
    # 1. USUARIOS
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, rol TEXT, saldo REAL, 
        password TEXT, email TEXT, grado TEXT, grupo TEXT, 
        cuenta TEXT, saldo_cajita REAL DEFAULT 0
    )''')
    
    # 2. TRANSACCIONES (Con columna 'autorizado_por' desde el inicio)
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones (
        id INTEGER PRIMARY KEY, fecha TEXT, remitente TEXT, destinatario TEXT, 
        monto REAL, concepto TEXT, tipo TEXT, estado TEXT DEFAULT 'completado', 
        autorizado_por TEXT DEFAULT 'Sistema'
    )''')
    
    # 3. OTRAS
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
# 4. LÓGICA (CALLBACKS + AUDITORÍA)
# ==========================================
def login(u, p):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM usuarios WHERE nombre=? AND password=?", conn, params=(u, p))
    conn.close()
    return df

def crud_usuario_bulk(df_csv):
    conn = get_connection(); c = conn.cursor()
    count = 0
    try:
        for _, row in df_csv.iterrows():
            if not c.execute("SELECT * FROM usuarios WHERE nombre=?", (row['nombre'],)).fetchone():
                c.execute("""
                    INSERT INTO usuarios (nombre, rol, saldo, password, grado, grupo, cuenta, saldo_cajita) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """, (row['nombre'], row['rol'], 0, str(row['password']), str(row.get('grado','')), str(row.get('grupo','')), generar_cuenta()))
                count += 1
        conn.commit()
        return count
    except Exception as e:
        st.error(f"Error en CSV: {e}")
        return 0
    finally: conn.close()

def crud_usuario_manual(nombre, rol, pwd, grado="", grupo=""):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, grado, grupo, cuenta, saldo_cajita) VALUES (?, ?, ?, ?, ?, ?, ?, 0)", 
                  (nombre, rol, 0, pwd, grado, grupo, generar_cuenta()))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def transaccion_core(origen, destino, monto, concepto, tipo, estado="completado", operador="Sistema"):
    conn = get_connection(); c = conn.cursor()
    f = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (monto, origen))
        c.execute("UPDATE usuarios SET saldo=saldo+? WHERE nombre=?", (monto, destino))
        c.execute("""
            INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) 
            VALUES (?,?,?,?,?,?,?,?)
        """, (f, origen, destino, monto, concepto, tipo, estado, operador))
        conn.commit(); return True
    except: return False
    finally: conn.close()

# CALLBACKS (ESTO ARREGLA LA TIENDA Y ENTREGAS)
def cb_comprar(usuario, id_prod):
    conn = get_connection(); c = conn.cursor()
    p = c.execute("SELECT * FROM productos WHERE id=?", (id_prod,)).fetchone()
    if p:
        nombre, precio, stock = p[1], p[2], p[3]
        saldo = c.execute("SELECT saldo FROM usuarios WHERE nombre=?", (usuario,)).fetchone()[0]
        if stock > 0 and saldo >= precio:
            c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (precio, usuario))
            c.execute("UPDATE productos SET stock=stock-1 WHERE id=?", (id_prod,))
            f = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)",
                      (f, usuario, "TIENDA", precio, f"Compra: {nombre}", "compra", "pendiente", "TIENDA"))
            conn.commit()
            st.session_state['msg'] = {'type': 'success', 'text': f"¡Felicidades! 🎉 Compraste {nombre}"}
            st.session_state['balloons'] = True
        else:
            st.session_state['msg'] = {'type': 'error', 'text': T('error_funds') if saldo < precio else T('no_stock')}
    conn.close()

def cb_entregar(id_tx):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE transacciones SET estado='entregado' WHERE id=?", (id_tx,))
    conn.commit(); conn.close()
    st.session_state['msg'] = {'type': 'success', 'text': "Producto entregado ✅"}

def mover_cajita_logic(usuario, monto, direccion):
    conn = get_connection(); c = conn.cursor()
    try:
        row = c.execute("SELECT saldo, saldo_cajita FROM usuarios WHERE nombre=?", (usuario,)).fetchone()
        saldo, cajita = row[0], row[1]
        if direccion == 'in': 
            if saldo >= monto:
                c.execute("UPDATE usuarios SET saldo=saldo-?, saldo_cajita=saldo_cajita+? WHERE nombre=?", (monto, monto, usuario))
                conn.commit(); return True, "Depósito exitoso 💰"
            return False, "Saldo insuficiente"
        elif direccion == 'out': 
            if cajita >= monto:
                c.execute("UPDATE usuarios SET saldo=saldo+?, saldo_cajita=saldo_cajita-? WHERE nombre=?", (monto, monto, usuario))
                conn.commit(); return True, "Retiro exitoso 💸"
            return False, "Fondos insuficientes"
    except: return False, "Error DB"
    finally: conn.close()
    return False, "Error desconocido"

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
    st.session_state['msg'] = {'type': 'success', 'text': f"Rendimientos pagados a {count} usuarios 🚀"}

# ==========================================
# 4.5 FUNCIONES ADICIONALES DE GESTIÓN
# ==========================================

def normalizar_grado(grado):
    """Convierte grado a formato ordinal: 1° 2° 3°"""
    grados_map = {'1': '1°', '2': '2°', '3': '3°', '1°': '1°', '2°': '2°', '3°': '3°'}
    return grados_map.get(str(grado), grado)

def normalizar_grupo(grupo):
    """Convierte grupo a letra mayúscula: A B"""
    return str(grupo).upper() if grupo else ""

def obtener_grados():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT grado FROM usuarios WHERE grado IS NOT NULL AND grado != ''", conn)
    conn.close()
    grados = df['grado'].tolist() if not df.empty else []
    return [normalizar_grado(g) for g in sorted(set(grados))]

def obtener_grupos():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT grupo FROM usuarios WHERE grupo IS NOT NULL AND grupo != ''", conn)
    conn.close()
    grupos = df['grupo'].tolist() if not df.empty else []
    return sorted(set([normalizar_grupo(g) for g in grupos]))

def obtener_usuarios_filtrados(filtro_grado="", filtro_grupo="", filtro_nombre=""):
    conn = get_connection()
    query = "SELECT nombre, grado, grupo, saldo FROM usuarios WHERE rol='alumno'"
    if filtro_grado:
        query += f" AND grado='{filtro_grado}'"
    if filtro_grupo:
        query += f" AND grupo='{filtro_grupo}'"
    if filtro_nombre:
        query += f" AND nombre LIKE '%{filtro_nombre}%'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def crear_producto(nombre, precio, stock, icono):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO productos (nombre, precio, stock, icono) VALUES (?, ?, ?, ?)",
                  (nombre, precio, stock, icono))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def actualizar_producto(id_prod, nombre, precio, stock, icono):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("UPDATE productos SET nombre=?, precio=?, stock=?, icono=? WHERE id=?",
                  (nombre, precio, stock, icono, id_prod))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def eliminar_producto(id_prod):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("DELETE FROM productos WHERE id=?", (id_prod,))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def editar_usuario(nombre, nuevo_nombre, saldo, grado, grupo):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("UPDATE usuarios SET nombre=?, saldo=?, grado=?, grupo=? WHERE nombre=?",
                  (nuevo_nombre, saldo, grado, grupo, nombre))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def eliminar_usuario(nombre):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("DELETE FROM usuarios WHERE nombre=?", (nombre,))
        conn.commit(); return True
    except: return False
    finally: conn.close()

# ==========================================
# 5. UI PRINCIPAL
# ==========================================
init_db()

# GESTIÓN DE MENSAJES GLOBAL
if 'msg' in st.session_state:
    m = st.session_state['msg']
    if m['type'] == 'success': st.success(m['text'])
    else: st.error(m['text'])
    del st.session_state['msg']
if 'balloons' in st.session_state: st.balloons(); del st.session_state['balloons']

# PANTALLA DE LOGIN
if 'usuario' not in st.session_state:
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 3, 2], gap="large")
    with c2:
        if archivo_logo: st.image(archivo_logo, width=180)
        st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='margin-bottom: 0.5rem;'>🏦 Banco Summerhill</h1>
                <p style='color: #64748b; font-size: 1.1rem; font-weight: 500;'>Tu banco escolar de confianza</p>
            </div>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown("### 🔐 Iniciar Sesión", unsafe_allow_html=True)
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
            u = st.text_input("👤 Usuario", key="login_u", placeholder="Ingresa tu usuario")
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            p = st.text_input("🔑 Contraseña", type="password", key="login_p", placeholder="Ingresa tu contraseña")
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            l = st.selectbox("🌐 Idioma / Language", ['ES', 'EN', 'FR'])
            if l != st.session_state['lang']:
                st.session_state['lang'] = l
                if l == 'ES': st.session_state['currency'] = 'MXN'
                elif l == 'EN': st.session_state['currency'] = 'USD'
                else: st.session_state['currency'] = 'EUR'
                st.rerun()
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Entrar", use_container_width=True):
                ud = login(u, p)
                if not ud.empty:
                    st.session_state['usuario'] = u
                    st.session_state['rol'] = ud.iloc[0]['rol']
                    st.rerun()
                else: st.error("❌ Usuario o contraseña incorrectos")

# PANTALLA PRINCIPAL (DENTRO)
else:
    conn = get_connection()
    user_row = pd.read_sql("SELECT * FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
    
    # ALERTAS ADMIN
    pending_delivery = 0
    if st.session_state['rol'] in PERMISO_TIENDA:
        pending_delivery = len(pd.read_sql("SELECT * FROM transacciones WHERE tipo='compra' AND estado='pendiente'", conn))
    conn.close()

    # SIDEBAR
    with st.sidebar:
        if archivo_logo: st.image(archivo_logo, width=100)
        st.write(f"Hola, **{st.session_state['usuario']}**")
        st.caption(f"Rol: {st.session_state['rol'].upper()}")
        st.info(f"💳 {user_row['cuenta']}")
        
        if pending_delivery > 0:
            st.error(f"🚨 {pending_delivery} Entregas pendientes")
        
        st.divider()
        
        # ENGRANE DE OPCIONES
        with st.expander("⚙️ Opciones"):
            st.markdown("### 🌐 Idioma")
            idiomas_map = {'Español': 'ES', 'English': 'EN', 'Français': 'FR'}
            idioma_actual = {v: k for k, v in idiomas_map.items()}[st.session_state['lang']]
            nuevo_idioma = st.selectbox("Selecciona idioma", list(idiomas_map.keys()), 
                                        index=list(idiomas_map.values()).index(st.session_state['lang']))
            
            if idiomas_map[nuevo_idioma] != st.session_state['lang']:
                st.session_state['lang'] = idiomas_map[nuevo_idioma]
                if idiomas_map[nuevo_idioma] == 'ES': st.session_state['currency'] = 'MXN'
                elif idiomas_map[nuevo_idioma] == 'EN': st.session_state['currency'] = 'USD'
                else: st.session_state['currency'] = 'EUR'
                st.rerun()
            
            st.markdown(f"**Moneda:** {SYMBOLS[st.session_state['currency']]} ({st.session_state['currency']})")
        
        st.divider()
        with st.expander("🗂️ Respaldo y Restauración", expanded=False):
            respaldo_opcion = st.selectbox("Selecciona una opción", ["Descargar Respaldo", "Subir Respaldo"], key="sidebar_respaldo_opcion")
            if respaldo_opcion == "Descargar Respaldo":
                with open(DB_NAME, "rb") as db_file:
                    st.download_button(
                        label="📥 Descargar Respaldo",
                        data=db_file,
                        file_name="respaldo_banco.db",
                        mime="application/octet-stream"
                    )
            elif respaldo_opcion == "Subir Respaldo":
                uploaded_file = st.file_uploader("📤 Subir Respaldo", type=["db"], key="sidebar_file_uploader")
                if uploaded_file:
                    if st.button("🔄 Restaurar Base de Datos", key="sidebar_restore_btn"):
                        with open(DB_NAME, "wb") as db_file:
                            db_file.write(uploaded_file.read())
                        st.success("✅ Base de datos restaurada correctamente. Recarga la página.")
                        st.stop()
        st.divider()

        if st.button("🚪 Cerrar Sesión", width='stretch'):
            del st.session_state['usuario']
            st.rerun()

    # TABS (CON PERMISOS)
    pestanas = ["Inicio", "Tienda", "Historial", "Analytics"]
    if st.session_state['rol'] == 'alumno': pestanas.insert(2, "Cajita")
    if st.session_state['rol'] in PERMISO_OPERAR: pestanas.insert(1, "Operaciones")
    if st.session_state['rol'] == 'admin': pestanas += ["Gestión", "Banco Central", "Auditoría"]
    
    tabs = st.tabs(pestanas)

    # --- 1. INICIO ---
    with tabs[0]:
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 3, 2], gap="large")
        with c2:
            st.metric("💰 Saldo Disponible", fmt_money(user_row['saldo']))

        # SOLO ADMIN: PAGAR PREMIOS Y COBRAR MULTAS
        if st.session_state['rol'] == 'admin':
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 🏅 Pagar Premios y Cobrar Multas")
            cpr, cmu = st.columns(2)
            # --- FILTROS DE ALUMNOS ---
            conn = get_connection()
            grados = obtener_grados()
            grupos = obtener_grupos()
            conn.close()
            filtro_grado = st.selectbox("Filtrar por grado", ["Todos"] + grados, key="filtro_grado_inicio")
            filtro_grupo = st.selectbox("Filtrar por grupo", ["Todos"] + grupos, key="filtro_grupo_inicio")
            conn = get_connection()
            query = "SELECT nombre FROM usuarios WHERE rol='alumno'"
            params = []
            if filtro_grado != "Todos":
                query += " AND grado=?"
                if filtro_grado:
                    params.append(str(filtro_grado).replace("°", ""))
            if filtro_grupo != "Todos":
                query += " AND grupo=?"
                params.append(filtro_grupo)
            df_alumnos = pd.read_sql(query, conn, params=params)
            conn.close()
            alumnos_lista = df_alumnos['nombre'].tolist() if not df_alumnos.empty else []
            # PAGAR PREMIO
            with cpr:
                st.markdown("#### 🟢 Pagar Premio")
                opciones_premio = list(OPCIONES_PAGOS.keys()) + ["Personalizado"]
                premio_sel = st.selectbox("Premio", opciones_premio, key="premio_sel")
                if premio_sel == "Personalizado":
                    premio_text = st.text_input("Descripción Premio", key="premio_text")
                    premio_monto = st.number_input("Monto Premio", min_value=1.0, step=1.0, key="premio_monto")
                else:
                    premio_text = premio_sel
                    premio_monto = OPCIONES_PAGOS.get(premio_sel, 0)
                alumnos = st.multiselect("Seleccionar alumnos", alumnos_lista, key="premio_alumnos")
                if st.button("Pagar Premio", key="btn_premio", use_container_width=True):
                    if alumnos and premio_text and premio_monto > 0:
                        for alu in alumnos:
                            transaccion_core("BANCO", alu, premio_monto, premio_text, "ingreso", operador=st.session_state['usuario'])
                        st.success(f"Premio pagado a {len(alumnos)} alumno(s)")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("Selecciona alumnos y completa los campos")
            # COBRAR MULTA
            with cmu:
                st.markdown("#### 🔴 Cobrar Multa")
                opciones_multa = list(OPCIONES_MULTAS.keys()) + ["Personalizado"]
                multa_sel = st.selectbox("Multa", opciones_multa, key="multa_sel")
                if multa_sel == "Personalizado":
                    multa_text = st.text_input("Descripción Multa", key="multa_text")
                    multa_monto = st.number_input("Monto Multa", min_value=1.0, step=1.0, key="multa_monto")
                else:
                    multa_text = multa_sel
                    multa_monto = OPCIONES_MULTAS.get(multa_sel, 0)
                alumnos_m = st.multiselect("Seleccionar alumnos", alumnos_lista, key="multa_alumnos")
                if st.button("Cobrar Multa", key="btn_multa", use_container_width=True):
                    if alumnos_m and multa_text and multa_monto > 0:
                        for alu in alumnos_m:
                            transaccion_core(alu, "BANCO", multa_monto, multa_text, "multa", operador=st.session_state['usuario'])
                        st.success(f"Multa cobrada a {len(alumnos_m)} alumno(s)")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("Selecciona alumnos y completa los campos")

    # --- TIENDA (OPTIMIZADA) ---
    idx_shop = pestanas.index("Tienda")
    with tabs[idx_shop]:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        if st.session_state['rol'] in PERMISO_TIENDA and pending_delivery > 0:
            st.markdown(f"<div class='admin-alert'>📦 {pending_delivery} entregas pendientes - ¡Atiéndelas!</div>", unsafe_allow_html=True)
            with st.expander("📦 Ver Entregas Pendientes", expanded=True):
                conn = get_connection()
                pend = pd.read_sql("SELECT * FROM transacciones WHERE tipo='compra' AND estado='pendiente'", conn)
                conn.close()
                for i, row in pend.iterrows():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"👤 **{row['remitente']}** | {row['concepto']}")
                    with c2:
                        st.button("✅ Entregar", key=f"dlv_{row['id']}", on_click=cb_entregar, args=(row['id'],), width='stretch')

        # GESTIÓN DE PRODUCTOS (SOLO ADMIN)
        if st.session_state['rol'] == 'admin':
            with st.expander("🛠️ Gestionar Productos", expanded=False):
                st.markdown("#### ➕ Crear Nuevo Producto")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    pnombre = st.text_input("Nombre", key="pnombre_new")
                with c2:
                    pprecio = st.number_input("Precio", min_value=1.0, key="pprecio_new")
                with c3:
                    pstock = st.number_input("Stock", min_value=1, value=10, key="pstock_new")
                with c4:
                    picono = st.text_input("Ícono", "🎁", key="picono_new")
                
                if st.button("➕ Crear Producto", width='stretch'):
                    if pnombre and pprecio > 0:
                        if crear_producto(pnombre, pprecio, pstock, picono):
                            st.success("✅ Producto creado")
                            time.sleep(1); st.rerun()
                        else:
                            st.error("❌ Error al crear producto")
                    else:
                        st.warning("⚠️ Completa todos los campos")
                
                st.divider()
                with st.expander("📋 Productos Existentes", expanded=False):
                    conn = get_connection()
                    prods_all = pd.read_sql("SELECT * FROM productos", conn)
                    conn.close()
                    
                    if not prods_all.empty:
                        for _, row in prods_all.iterrows():
                            with st.expander(f"{row['icono']} {row['nombre']} | ${row['precio']} | Stock: {row['stock']}", expanded=False):
                                ec1, ec2, ec3, ec4 = st.columns(4)
                                with ec1:
                                    epnombre = st.text_input("Nombre", value=row['nombre'], key=f"epn_{row['id']}")
                                with ec2:
                                    epprecio = st.number_input("Precio", value=row['precio'], key=f"epp_{row['id']}")
                                with ec3:
                                    epstock = st.number_input("Stock", value=row['stock'], key=f"eps_{row['id']}")
                                with ec4:
                                    epicono = st.text_input("Ícono", value=row['icono'], key=f"epi_{row['id']}")
                                
                                c_save, c_del = st.columns(2)
                                with c_save:
                                    if st.button("💾 Guardar", key=f"save_p_{row['id']}", width='stretch'):
                                        if actualizar_producto(row['id'], epnombre, epprecio, epstock, epicono):
                                            st.success("✅ Actualizado")
                                            time.sleep(1); st.rerun()
                                        else:
                                            st.error("❌ Error")
                                    if st.button("🗑️ Eliminar", key=f"del_p_{row['id']}", width='stretch'):
                                        if eliminar_producto(row['id']):
                                            st.success("✅ Eliminado")
                                            time.sleep(1); st.rerun()
                    else:
                        st.info("ℹ️ No hay productos")

        # TIENDA PARA ALUMNOS
        with st.expander("🛍️ Productos Disponibles", expanded=True):
            conn = get_connection()
            prods = pd.read_sql("SELECT * FROM productos WHERE stock > 0", conn)
            conn.close()
            
            if prods.empty: 
                st.info("ℹ️ Tienda vacía")
            else:
                cols = st.columns(3, gap="medium")
                for i, (_, row) in enumerate(prods.iterrows()):
                    with cols[i % 3]: 
                        st.markdown(f"""
                            <div style='background: var(--card-bg); padding: 2rem; border-radius: 15px; border: 1px solid var(--border-light); text-align: center; box-shadow: var(--card-shadow); transition: all 0.3s;'>
                                <div style='font-size: 4rem; margin-bottom: 1rem;'>{row['icono']}</div>
                                <p style='font-size: 1.2rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.5rem;'>{row['nombre']}</p>
                                <p style='color: var(--text-light); font-size: 0.9rem; margin-bottom: 1rem;'>Stock: {row['stock']}</p>
                                <p style='font-size: 1.4rem; font-weight: 700; color: var(--primary-color);'>{fmt_money(row['precio'])}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.button("🛒 Comprar", key=f"buy_{row['id']}", on_click=cb_comprar, args=(st.session_state['usuario'], row['id']), width='stretch')

    # --- OPERACIONES (OPTIMIZADO) ---
    if "Operaciones" in pestanas:
        idx_ops = pestanas.index("Operaciones")
        with tabs[idx_ops]:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown("### ⚡ Panel de Control Avanzado")
            
            with st.expander("🔍 Filtrar & Seleccionar", expanded=True):
                # FILTROS
                c1, c2, c3 = st.columns(3)
                with c1:
                    filtro_grado = st.selectbox("📚 Grado", ["Todos"] + obtener_grados(), key="fg_ops")
                with c2:
                    filtro_grupo = st.selectbox("👥 Grupo", ["Todos"] + obtener_grupos(), key="fg_ops2")
                with c3:
                    filtro_nombre = st.text_input("🔎 Nombre", key="fn_ops")
                
                grado_f = None if filtro_grado == "Todos" else str(filtro_grado).replace("°", "") if filtro_grado else None
                grupo_f = None if filtro_grupo == "Todos" else (str(filtro_grupo) if filtro_grupo else None)
                df_alumnos_filt = obtener_usuarios_filtrados(grado_f or "", grupo_f or "", filtro_nombre)
                
                st.markdown(f"**Alumnos encontrados: {len(df_alumnos_filt)}**")
                
                # SELECCIÓN
                c1, c2 = st.columns([2, 1])
                with c1:
                    if st.button("✔️ Seleccionar Todos", width='stretch'):
                        st.session_state['selected_ops'] = df_alumnos_filt['nombre'].tolist()
                    if st.button("❌ Deseleccionar Todos", width='stretch'):
                        st.session_state['selected_ops'] = []
                
                with c2:
                    st.markdown(f"**Seleccionados:** {len(st.session_state.get('selected_ops', []))}")
                
                selected = st.multiselect("👫 Alumnos", df_alumnos_filt['nombre'].tolist(),
                                         default=st.session_state.get('selected_ops', []),
                                         key="multi_select_ops")
                st.session_state['selected_ops'] = selected
            
            # ACCIÓN
            with st.expander("⚙️ Ejecutar Acción", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    tipo_op = st.selectbox("Tipo", ["Cobrar Multa 🔴", "Pagar Premio 🟢"])
                    cat = OPCIONES_MULTAS if "Multa" in tipo_op else OPCIONES_PAGOS
                    motivo_op = st.selectbox("Motivo", list(cat.keys()))
                with c2:
                    monto_op = st.number_input("Monto", value=float(cat[motivo_op]), min_value=0.0, key=f"m_ops_{motivo_op}")
                
                if st.button("🚀 EJECUTAR", width='stretch'):
                    if not selected: 
                        st.warning("⚠️ Selecciona alumnos")
                    else:
                        real_monto_op = monto_op / RATES[st.session_state['currency']]
                        tipo_tx = "multa" if "Multa" in tipo_op else "ingreso"
                        ok_count = 0
                        for alu in selected:
                            op = st.session_state['usuario']
                            conn = get_connection(); c = conn.cursor()
                            if tipo_tx == "multa": 
                                c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (real_monto_op, alu))
                            else: 
                                c.execute("UPDATE usuarios SET saldo=saldo+? WHERE nombre=?", (real_monto_op, alu))
                        
                            c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                       alu if tipo_tx=="multa" else "BANCO", 
                                       "BANCO" if tipo_tx=="multa" else alu, 
                                       real_monto_op, motivo_op, tipo_tx, "completado", op))
                            conn.commit(); conn.close()
                            ok_count += 1
                        st.success(f"✅ Aplicado a {ok_count} alumnos")
                        time.sleep(1); st.rerun()

    # --- HISTORIAL (OPTIMIZADO) ---
    idx_hist = pestanas.index("Historial")
    with tabs[idx_hist]:
        with st.expander("📋 Historial de Transacciones", expanded=True):
            conn = get_connection()
            df = pd.read_sql("SELECT fecha, remitente, destinatario, monto, concepto, autorizado_por FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], st.session_state['usuario']))
            conn.close()
            
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], format='mixed')
                rate = RATES[st.session_state['currency']]
                df['monto'] = df['monto'] * rate
                df['monto'] = df['monto'].map(lambda x: f"{SYMBOLS[st.session_state['currency']]}{x:,.2f}")
                st.dataframe(df, width='stretch', hide_index=True)
            else: st.info("Sin movimientos")

    # --- ANALYTICS ---
    idx_ana = pestanas.index("Analytics")
    with tabs[idx_ana]:
        if HAS_PLOTLY:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM transacciones WHERE remitente=? OR destinatario=?", conn, params=(st.session_state['usuario'], st.session_state['usuario']))
            conn.close()
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'], format='mixed')
                fig = px.bar(df, x='fecha', y='monto', color='tipo', title="Mis Movimientos")
                st.plotly_chart(fig, width=True)
        else:
            st.warning("⚠️ Instala 'plotly' en requirements.txt")

    # === ADMIN TABS ===
    if st.session_state['rol'] == 'admin':
        
        # GESTION - OPTIMIZADO CON MENÚS
        with tabs[pestanas.index("Gestión")]:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 👥 Gestión de Usuarios")
            
            # TAB 1: CREAR MANUAL
            with st.expander("➕ Crear Usuario Individual", expanded=False):
                st.markdown("#### Crear Usuario")
                c1, c2 = st.columns(2)
                with c1:
                    nu = st.text_input("Nombre", key="adm_nu_new")
                    nr = st.selectbox("Rol", ["alumno", "profesor", "administrativo"], key="adm_nr_new")
                    grados_list = ["---", "1°", "2°", "3°", "Nuevo"]
                    ng = st.selectbox("Grado", grados_list, key="adm_ng_new") or "---"
                    if ng == "Nuevo":
                        ng_custom = st.selectbox("Selecciona nuevo grado", ["1°", "2°", "3°"], key="adm_ng_custom")
                        ng = ng_custom if ng_custom else ""
                with c2:
                    np = st.text_input("Password", type="password", key="adm_np_new")
                    grupos_list = ["---", "A", "B", "Nuevo"]
                    ngr = st.selectbox("Grupo", grupos_list, key="adm_ngr_new") or "---"
                    if ngr == "Nuevo":
                        ngr_custom = st.selectbox("Selecciona nuevo grupo", ["A", "B"], key="adm_ngr_custom")
                        ngr = ngr_custom if ngr_custom else ""
    
                if st.button("✅ Crear Usuario", width='stretch'):
                    if nu and np:
                        if crud_usuario_manual(nu, nr, np, ng if ng != "---" else "", ngr if ngr != "---" else ""):
                            st.success("✅ Usuario creado exitosamente")
                            time.sleep(1); st.rerun()
                        else:
                            st.error("❌ El usuario ya existe")
                    else:
                        st.warning("⚠️ Nombre y contraseña requeridos")
            
            # TAB 2: VER/EDITAR
            with st.expander("📋 Ver/Editar Usuarios", expanded=False):
                st.markdown("#### Listado de Usuarios")
                conn = get_connection()
                all_users = pd.read_sql("SELECT nombre, rol, saldo, grado, grupo FROM usuarios", conn)
                conn.close()
                
                if not all_users.empty:
                    # FILTROS
                    fc1, fc2, fc3 = st.columns(3)
                    with fc1:
                        filtro_user = st.text_input("🔎 Buscar usuario", key="filt_user")
                    with fc2:
                        filtro_rol = st.selectbox("Rol", ["Todos"] + list(all_users['rol'].unique()), key="filt_rol_adm")
                    with fc3:
                        filtro_grado = st.selectbox("Grado", ["Todos"] + obtener_grados(), key="filt_grado_adm")
                    
                    all_users_filt = all_users.copy()
                    if filtro_user:
                        all_users_filt = all_users_filt[all_users_filt['nombre'].str.contains(filtro_user, case=False)]
                    if filtro_rol != "Todos":
                        all_users_filt = all_users_filt[all_users_filt['rol'] == filtro_rol]
                    if filtro_grado and filtro_grado != "Todos":
                        all_users_filt = all_users_filt[all_users_filt['grado'] == filtro_grado.replace("°", "")]
                    
                    st.markdown(f"**Total: {len(all_users_filt)} usuarios**")
                    
                    for _, row in all_users_filt.iterrows():
                        grado_norm = normalizar_grado(row['grado'])
                        grupo_norm = normalizar_grupo(row['grupo'])
                        with st.expander(f"👤 {row['nombre']} | {row['rol']} | {grado_norm}/{grupo_norm}", expanded=False):
                            ec1, ec2, ec3, ec4 = st.columns(4)
                            with ec1:
                                enum = st.text_input("Nombre", value=row['nombre'], key=f"enum_{row['nombre']}")
                            with ec2:
                                esaldo = st.number_input("Saldo", value=float(row['saldo']), key=f"esal_{row['nombre']}")
                            with ec3:
                                grados_options = ["---", "1°", "2°", "3°"]
                                grado_norm_actual = normalizar_grado(row['grado'])
                                egrado_idx = grados_options.index(grado_norm_actual) if grado_norm_actual in grados_options else 0
                                egrado = st.selectbox("Grado", grados_options, index=egrado_idx, key=f"egr_{row['nombre']}")
                            with ec4:
                                grupos_options = ["---", "A", "B"]
                                grupo_norm_actual = normalizar_grupo(row['grupo'])
                                egrupo_idx = grupos_options.index(grupo_norm_actual) if grupo_norm_actual in grupos_options else 0
                                egrupo = st.selectbox("Grupo", grupos_options, index=egrupo_idx, key=f"egru_{row['nombre']}")
                            
                            c_save, c_del = st.columns(2)
                            with c_save:
                                if st.button("💾 Guardar", key=f"save_u_{row['nombre']}", width='stretch'):
                                    egrado_clean = str(egrado).replace("°", "") if egrado and egrado != "---" else ""
                                    if editar_usuario(row['nombre'], enum, esaldo, egrado_clean, egrupo if egrupo != "---" else ""):
                                        st.success("✅ Usuario actualizado")
                                        time.sleep(1); st.rerun()
                                    else:
                                        st.error("❌ Error al actualizar")
                            
                            with c_del:
                                if st.button("🗑️ Eliminar", key=f"del_u_{row['nombre']}", width='stretch'):
                                    if eliminar_usuario(row['nombre']):
                                        st.success("✅ Usuario eliminado")
                                        time.sleep(1); st.rerun()
                                    else:
                                        st.error("❌ Error al eliminar")
                else:
                    st.info("ℹ️ No hay usuarios")
            
            # TAB 3: CARGA MASIVA
            with st.expander("📂 Importar desde CSV", expanded=False):
                st.markdown("#### Importar Usuarios")
                st.info("Formato: nombre, rol, password, grado (1/2/3), grupo (A/B)")
                up_file = st.file_uploader("Archivo CSV", type=['csv'], key="csv_upload_final")
                if up_file:
                    df_prev = pd.read_csv(up_file)
                    with st.expander("Vista previa", expanded=False):
                        st.dataframe(df_prev.head(5), width='stretch')
                    
                    if st.button("✅ Procesar Archivo", width='stretch'):
                        n = crud_usuario_bulk(df_prev)
                        st.success(f"✅ Se crearon {n} usuarios exitosamente")
                        time.sleep(1); st.rerun()

        # BANCO CENTRAL - MEJORADO
        with tabs[pestanas.index("Banco Central")]:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 🏦 Banco Central - Control de Ahorro")
            
            conn = get_connection()
            conf = pd.read_sql("SELECT * FROM config_ahorro", conn).iloc[0]
            
            # SECCIÓN 1: CONFIGURACIÓN
            with st.expander("⚙️ Configuración de Tasa", expanded=False):
                st.markdown("#### Tasa de Rendimiento")
                nueva_tasa = st.number_input("Tasa (%)", value=conf['tasa'], min_value=0.0, max_value=100.0, step=0.1, key="nueva_tasa")
                
                if st.button("💾 Actualizar Tasa", width='stretch'):
                    c = conn.cursor()
                    c.execute("UPDATE config_ahorro SET tasa=? WHERE id=?", (nueva_tasa, conf['id']))
                    conn.commit()
                    st.success(f"✅ Tasa actualizada a {nueva_tasa}%")
                    time.sleep(1); st.rerun()
            
            # SECCIÓN 2: ESTADÍSTICAS
            with st.expander("📊 Estadísticas de Ahorro", expanded=True):
                st.markdown("#### Información General")
                
                # OBTENER DATOS
                total_cajita = conn.execute("SELECT SUM(saldo_cajita) FROM usuarios WHERE saldo_cajita > 0").fetchone()[0] or 0.0
                usuarios_ahorro = conn.execute("SELECT COUNT(*) FROM usuarios WHERE saldo_cajita > 0").fetchone()[0]
                total_ganancias = conn.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='interes'").fetchone()[0] or 0.0
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("🏦 Total en Cajitas", fmt_money(total_cajita))
                with c2:
                    st.metric("👥 Usuarios Ahorrando", usuarios_ahorro)
                with c3:
                    st.metric("📈 Ganancias Generadas", fmt_money(total_ganancias))
                with c4:
                    st.metric("💹 Tasa Actual", f"{conf['tasa']}%")
                
                # TABLA DE TOP AHORRADORES
                st.markdown("#### Top 10 Ahorradores")
                top_ahorradores = pd.read_sql(
                    "SELECT nombre, saldo_cajita FROM usuarios WHERE saldo_cajita > 0 ORDER BY saldo_cajita DESC LIMIT 10",
                    conn
                )
                if not top_ahorradores.empty:
                    top_ahorradores['saldo_cajita'] = top_ahorradores['saldo_cajita'].apply(lambda x: fmt_money(x))
                    st.dataframe(top_ahorradores, width='stretch', hide_index=True)
                else:
                    st.info("ℹ️ No hay usuarios con saldo en cajita")
            
            # SECCIÓN 3: PAGAR RENDIMIENTOS
            with st.expander("💸 Pagar Rendimientos", expanded=False):
                st.markdown("#### Ejecutar Pago de Intereses")
                st.warning(f"⚠️ Se pagará {conf['tasa']}% a todos los usuarios con saldo en cajita")
                
                if st.button("🚀 PAGAR RENDIMIENTOS A TODOS", width='stretch'):
                    cb_pagar_rendimientos(conf['tasa'])
                    st.rerun()
            
            # SECCIÓN 4: HISTORIAL DE RENDIMIENTOS
            with st.expander("📋 Historial de Rendimientos", expanded=False):
                st.markdown("#### Últimas Transacciones de Intereses")
                historial_interes = pd.read_sql(
                    "SELECT fecha, destinatario, monto, concepto FROM transacciones WHERE tipo='interes' ORDER BY fecha DESC LIMIT 20",
                    conn
                )
                if not historial_interes.empty:
                    historial_interes['monto'] = historial_interes['monto'].apply(lambda x: fmt_money(x))
                    st.dataframe(historial_interes, width='stretch', hide_index=True)
                else:
                    st.info("ℹ️ No hay historial de rendimientos")
            
            conn.close()

        # AUDITORIA
        with tabs[pestanas.index("Auditoría")]:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 🕵️‍♂️ Auditoría Total")
            conn = get_connection()
            
            with st.expander("🔍 Filtros de Búsqueda", expanded=True):
                c1, c2 = st.columns(2)
                filtro_u = c1.text_input("Buscar Usuario")
                filtro_t = c2.multiselect("Tipo de Transacción", ["compra", "multa", "ingreso", "transferencia", "interes"])
                
                query = "SELECT * FROM transacciones WHERE 1=1"
                params = []
                if filtro_u:
                    query += " AND (remitente LIKE ? OR destinatario LIKE ?)"
                    params += [f"%{filtro_u}%", f"%{filtro_u}%"]
                if filtro_t and len(filtro_t) < 5:
                    query += " AND tipo IN ({})".format(",".join("?"*len(filtro_t)))
                    params += filtro_t
                
                st.markdown(f"**Resultados:**")
                df_auditoria = pd.read_sql(query, conn, params=params)
                conn.close()
                
                if not df_auditoria.empty:
                    df_auditoria['fecha'] = pd.to_datetime(df_auditoria['fecha'], format='mixed')
                    df_auditoria['monto'] = df_auditoria['monto'] * RATES[st.session_state['currency']]
                    df_auditoria['monto'] = df_auditoria['monto'].map(lambda x: f"{SYMBOLS[st.session_state['currency']]}{x:,.2f}")
                    st.dataframe(df_auditoria, width='stretch', hide_index=True)
                else:
                    st.info("Sin resultados")
    
    # --- CAJITA (AHORRO) PARA ALUMNOS ---
    if st.session_state['rol'] == 'alumno' and 'Cajita' in pestanas:
        idx_cajita = pestanas.index('Cajita')
        with tabs[idx_cajita]:
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
            st.markdown("### 🏦 Mi Cajita de Ahorro")
            saldo_cajita = user_row['saldo_cajita']
            saldo_main = user_row['saldo']
            st.metric("💰 Saldo en Cajita", fmt_money(saldo_cajita))
            st.metric("💳 Saldo Principal", fmt_money(saldo_main))
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ➕ Depositar a Cajita")
                monto_in = st.number_input("Monto a depositar", min_value=1.0, max_value=float(saldo_main), step=1.0, key="cajita_in")
                if st.button("Depositar", key="btn_cajita_in", use_container_width=True):
                    ok, msg = mover_cajita_logic(st.session_state['usuario'], monto_in, 'in')
                    if ok:
                        st.success(msg)
                        time.sleep(1); st.rerun()
                    else:
                        st.error(msg)
            with c2:
                st.markdown("#### ➖ Retirar de Cajita")
                monto_out = st.number_input("Monto a retirar", min_value=1.0, max_value=float(saldo_cajita), step=1.0, key="cajita_out")
                if st.button("Retirar", key="btn_cajita_out", use_container_width=True):
                    ok, msg = mover_cajita_logic(st.session_state['usuario'], monto_out, 'out')
                    if ok:
                        st.success(msg)
                        time.sleep(1); st.rerun()
                    else:
                        st.error(msg)
            st.divider()
            st.markdown("#### 📝 Historial de Cajita")
            conn = get_connection()
            df_cajita = pd.read_sql("SELECT fecha, tipo, monto, concepto FROM transacciones WHERE (remitente=? OR destinatario=?) AND (tipo='interes' OR concepto LIKE '%Cajita%') ORDER BY fecha DESC LIMIT 10", conn, params=(st.session_state['usuario'], st.session_state['usuario']))
            conn.close()
            if not df_cajita.empty:
                df_cajita['monto'] = df_cajita['monto'].map(lambda x: fmt_money(x))
                st.dataframe(df_cajita, width='stretch', hide_index=True)
            else:
                st.info("Sin movimientos en cajita")