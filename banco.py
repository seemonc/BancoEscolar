import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import os
import random

# INTENTO DE IMPORTAR PLOTLY (Si falla por configuración de VS Code, la app sigue viva)
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
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
        
        h1, h2, h3 { color: #0095a3 !important; font-weight: 700 !important; }
        
        .stButton > button {
            background-image: linear-gradient(to right, #0095a3 0%, #007f8b 51%, #0095a3 100%);
            border: none; border-radius: 8px; color: white; padding: 10px 20px; text-transform: uppercase; font-weight: bold; width: 100%; transition: 0.3s;
        }
        .stButton > button:hover { transform: scale(1.02); opacity: 0.9; color: white; }
        
        div[data-testid="stMetric"] { background-color: #ffffff !important; border: 1px solid #e0e0e0; border-left: 8px solid #0095a3 !important; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
        div[data-testid="stMetric"] * { color: #000000 !important; }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { color: #0095a3 !important; font-size: 2.8rem !important; font-weight: 700 !important; }
        
        .stExpander { border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        
        .financial-tip-good { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-bottom: 20px; }
        .financial-tip-bad { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 20px; }
        
        .admin-alert {
            background-color: #ffcccc; color: #cc0000; padding: 20px; border-radius: 10px; border: 2px solid #cc0000; text-align: center; font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(200,0,0,0.2);
        }

        #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
        
        @media only screen and (max-width: 600px) {
            .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
            h1 { font-size: 1.8rem !important; }
            div[data-testid="stMetricValue"] { font-size: 2.2rem !important; }
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

def fmt_money(amount):
    curr = st.session_state['currency']
    val = amount * RATES[curr]
    return f"{SYMBOLS[curr]}{val:,.2f}"

TRANS = {
    'ES': {
        'title': 'Banco Summerhill', 'user': 'Usuario', 'pass': 'Contraseña', 'login': 'Entrar',
        'role': 'Rol', 'account': 'Cuenta', 'exit': 'Salir', 'balance_user': 'SALDO DISPONIBLE',
        'home': '🏠 Inicio', 'store': '🛍️ Tienda', 'hist': '📊 Historial', 'analytics': '📈 Analytics', 'savings': '💰 Cajita',
        'buy': 'Comprar', 'price': 'Precio', 'stock': 'Disponibles', 'add_prod': 'Agregar Producto',
        'prod_name': 'Nombre del Producto', 'prod_price': 'Precio', 'prod_stock': 'Cantidad Inicial', 'prod_icon': 'Emoji/Icono',
        'create': 'Crear', 'no_stock': 'Agotado', 'success_buy': '¡Compra exitosa!', 'error_funds': 'Saldo insuficiente',
        'ops': '⚡ Operaciones', 'manage': '👥 Gestión', 'my_hist': 'Mis Movimientos',
        'auth': '🛡️ Autorizaciones', 'pending': 'Pendientes', 'deliveries': '📦 Entregas',
        'mark_delivered': 'Entregar', 'confirm_dlv': '⚠️ CONFIRMAR ENTREGA', 'new_buy': 'Nueva Compra', 'admin_store': '🛍️ Tienda (Admin)',
        'confirm_auth': '⚠️ CONFIRMAR APROBACIÓN', 'sure': '¿Seguro?',
        'selected_list': '📋 Lista de Alumnos', 'action': 'Acción', 'reason': 'Motivo',
        'charge_verb': '🔴 COBRAR MULTA', 'pay_verb': '🟢 PAGAR PREMIO', 'exec_btn': 'EJECUTAR',
        'send_to': 'Destinatario', 'amount': 'Monto', 'bulk_upload': '📂 Carga Masiva (CSV)',
        'upload_btn': 'Procesar Archivo', 'db_view': '📝 Base de Datos', 'save_db': '💾 Guardar Cambios',
        'backup': '💾 Respaldos',
        'search': '🔎 Buscar y Filtrar', 'filters': 'Filtros', 'grade': 'Grado', 'group': 'Grupo', 'name': 'Nombre',
        'add_filtered': '⬇️ Agregar todos los filtrados', 'add_manual': '⬇️ Agregar seleccionados', 'clear_list': '🗑️ Vaciar Lista',
        'all': 'Todos', 'results': 'Resultados',
        'select_detail': '📝 Selección Detallada (Click para abrir)', 'mark_add': '⬇️ Agregar Marcados', 'select_col': 'Seleccionar',
        'mark_all': '✅ Marcar/Desmarcar Todos',
        'chart_expenses': '💸 Mis Gastos por Categoría', 'chart_trend': '📈 Evolución de mi Saldo', 'total_in': 'Ingresos Totales', 'total_out': 'Gastos Totales',
        'fin_health': '🏥 Salud Financiera',
        'tip_good_title': '¡Tus finanzas están sanas! 🚀',
        'tip_good_desc': 'Tus ingresos superan a tus gastos. Es un gran momento para ahorrar para un premio grande en la tienda.',
        'tip_bad_title': '¡Cuidado con los gastos! 📉',
        'tip_bad_desc': 'Al día de hoy, tus gastos (multas/compras) superan tus ingresos. Intenta portarte bien esta semana y cumplir tareas extra.',
        'savings_bal': 'EN CAJITA', 'deposit': '📥 Depositar', 'withdraw': '📤 Retirar',
        'rate_info': 'Tasa de Rendimiento', 'central_bank': '🏦 Banco Central',
        'set_rate': 'Configurar Tasa (%)', 'pay_yields': '💸 Pagar Rendimientos', 'yield_paid': 'Rendimientos Pagados',
        'total_earned': '🤑 Rendimiento Ganado', 'send_btn': 'Enviar Dinero',
        'audit': '🕵️‍♂️ Auditoría Global', 'audit_desc': 'Revisión completa de movimientos.'
    },
    'EN': {
        'title': 'Summerhill Bank', 'user': 'Username', 'pass': 'Password', 'login': 'Login',
        'role': 'Role', 'account': 'Account', 'exit': 'Logout', 'balance_user': 'AVAILABLE BALANCE',
        'home': '🏠 Home', 'store': '🛍️ Store', 'hist': '📊 History', 'analytics': '📈 Analytics', 'savings': '💰 Savings Box',
        'buy': 'Buy', 'price': 'Price', 'stock': 'In Stock', 'add_prod': 'Add Product',
        'prod_name': 'Product Name', 'prod_price': 'Price', 'prod_stock': 'Initial Stock', 'prod_icon': 'Emoji/Icon',
        'create': 'Create', 'no_stock': 'Out of Stock', 'success_buy': 'Purchase successful!', 'error_funds': 'Insufficient funds',
        'ops': '⚡ Operations', 'manage': '👥 Manage', 'my_hist': 'My History',
        'auth': '🛡️ Approvals', 'pending': 'Pending', 'deliveries': '📦 Deliveries',
        'mark_delivered': 'Deliver', 'confirm_dlv': '⚠️ CONFIRM DELIVERY', 'new_buy': 'New Purchase', 'admin_store': '🛍️ Store (Admin)',
        'confirm_auth': '⚠️ CONFIRM APPROVAL', 'sure': 'Are you sure?',
        'selected_list': '📋 Student List', 'action': 'Action', 'reason': 'Reason',
        'charge_verb': '🔴 CHARGE FINE', 'pay_verb': '🟢 PAY REWARD', 'exec_btn': 'EXECUTE',
        'send_to': 'Recipient', 'amount': 'Amount', 'bulk_upload': '📂 Bulk Upload (CSV)',
        'upload_btn': 'Process File', 'db_view': '📝 Database', 'save_db': '💾 Save Changes',
        'backup': '💾 Backups',
        'search': '🔎 Search & Filter', 'filters': 'Filters', 'grade': 'Grade', 'group': 'Group', 'name': 'Name',
        'add_filtered': '⬇️ Add all filtered', 'add_manual': '⬇️ Add selected', 'clear_list': '🗑️ Clear List',
        'all': 'All', 'results': 'Results',
        'select_detail': '📝 Detailed Selection (Click to open)', 'mark_add': '⬇️ Add Checked', 'select_col': 'Select',
        'mark_all': '✅ Check/Uncheck All',
        'chart_expenses': '💸 My Expenses by Category', 'chart_trend': '📈 My Balance Trend', 'total_in': 'Total Income', 'total_out': 'Total Expenses',
        'fin_health': '🏥 Financial Health',
        'tip_good_title': 'Your finances are healthy! 🚀',
        'tip_good_desc': 'Your income exceeds your expenses. Great time to save up for a big prize.',
        'tip_bad_title': 'Watch your spending! 📉',
        'tip_bad_desc': 'As of today, your expenses exceed your income. Try to avoid fines and ask for extra tasks.',
        'savings_bal': 'IN SAVINGS', 'deposit': '📥 Deposit', 'withdraw': '📤 Withdraw',
        'rate_info': 'Yield Rate', 'central_bank': '🏦 Central Bank',
        'set_rate': 'Set Rate (%)', 'pay_yields': '💸 Pay Yields', 'yield_paid': 'Yields Paid',
        'total_earned': '🤑 Interest Earned', 'send_btn': 'Send Money',
        'audit': '🕵️‍♂️ Global Audit', 'audit_desc': 'Complete review.'
    },
    'FR': {
        'title': 'Banque Summerhill', 'user': 'Utilisateur', 'pass': 'Mot de passe', 'login': 'Entrer',
        'role': 'Rôle', 'account': 'Compte', 'exit': 'Sortir', 'balance_user': 'SOLDE DISPONIBLE',
        'home': '🏠 Accueil', 'store': '🛍️ Boutique', 'hist': '📊 Historique', 'analytics': '📈 Analytique', 'savings': '💰 Coffre-fort',
        'buy': 'Acheter', 'price': 'Prix', 'stock': 'En stock', 'add_prod': 'Ajouter Produit',
        'prod_name': 'Nom du produit', 'prod_price': 'Prix', 'prod_stock': 'Quantité', 'prod_icon': 'Emoji/Icône',
        'create': 'Créer', 'no_stock': 'Épuisé', 'success_buy': 'Achat réussi!', 'error_funds': 'Fonds insuffisants',
        'ops': '⚡ Opérations', 'manage': '👥 Gestion', 'my_hist': 'Mon historique',
        'auth': '🛡️ Autorisations', 'pending': 'En attente', 'deliveries': '📦 Livraisons',
        'mark_delivered': 'Livrer', 'confirm_dlv': '⚠️ CONFIRMER LIVRAISON', 'new_buy': 'Nouvel Achat', 'admin_store': '🛍️ Boutique (Admin)',
        'confirm_auth': '⚠️ CONFIRMER APPROBATION', 'sure': 'Êtes-vous sûr?',
        'selected_list': '📋 Liste d\'étudiants', 'action': 'Action', 'reason': 'Motif',
        'charge_verb': '🔴 APPLIQUER AMENDE', 'pay_verb': '🟢 PAYER PRIX', 'exec_btn': 'EXÉCUTER',
        'send_to': 'Destinataire', 'amount': 'Montant', 'bulk_upload': '📂 Chargement en masse (CSV)',
        'upload_btn': 'Traiter le fichier', 'db_view': '📝 Base de données', 'save_db': '💾 Enregistrer',
        'backup': '💾 Sauvegardes',
        'search': '🔎 Rechercher et filtrer', 'filters': 'Filtres', 'grade': 'Niveau', 'group': 'Groupe', 'name': 'Nom',
        'add_filtered': '⬇️ Ajouter tous les filtrés', 'add_manual': '⬇️ Ajouter sélectionnés', 'clear_list': '🗑️ Vider la liste',
        'all': 'Tous', 'results': 'Résultats',
        'select_detail': '📝 Sélection détaillée (Cliquer pour ouvrir)', 'mark_add': '⬇️ Ajouter cochés', 'select_col': 'Sélectionner',
        'mark_all': '✅ Tout cocher/décocher',
        'chart_expenses': '💸 Mes dépenses par catégorie', 'chart_trend': '📈 Évolution de mon solde', 'total_in': 'Revenus totaux', 'total_out': 'Dépenses totales',
        'fin_health': '🏥 Santé financière',
        'tip_good_title': 'Vos finances sont saines! 🚀',
        'tip_good_desc': 'Vos revenus dépassent vos dépenses. C\'est le moment d\'économiser pour un gros prix.',
        'tip_bad_title': 'Attention aux dépenses! 📉',
        'tip_bad_desc': 'À ce jour, vos dépenses dépassent vos revenus. Essayez d\'éviter les amendes.',
        'savings_bal': 'DANS LE COFFRE', 'deposit': '📥 Dépôt', 'withdraw': '📤 Retrait',
        'rate_info': 'Taux de rendement', 'central_bank': '🏦 Banque Centrale',
        'set_rate': 'Taux (%)', 'pay_yields': '💸 Payer Intérêts', 'yield_paid': 'Intérêts payés',
        'total_earned': '🤑 Intérêts gagnés', 'send_btn': 'Envoyer',
        'audit': '🕵️‍♂️ Audit Global', 'audit_desc': 'Revue complète.'
    }
}

def T(key): 
    val = TRANS[st.session_state['lang']].get(key, key)
    return val if val is not None else str(key)

OPCIONES_MULTAS = {"---": 0, "Celular": 50, "No Tarea": 100, "Falta Respeto": 500}
OPCIONES_PAGOS = {"---": 0, "Tarea": 100, "Proyecto": 200, "Participación": 20}

# ==========================================
# 3. BASE DE DATOS
# ==========================================
def get_connection(): return sqlite3.connect('banco_escolar.db')
def generar_cuenta(): return str(random.randint(10000000, 99999999))

def init_db():
    conn = get_connection(); c = conn.cursor()
    # TABLAS BASE
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, rol TEXT, saldo REAL, password TEXT, email TEXT, grado TEXT, grupo TEXT, cuenta TEXT, saldo_cajita REAL DEFAULT 0)''') 
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones (id INTEGER PRIMARY KEY, fecha TEXT, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, tipo TEXT, estado TEXT DEFAULT 'completado')''') 
    c.execute('''CREATE TABLE IF NOT EXISTS solicitudes (id INTEGER PRIMARY KEY, remitente TEXT, destinatario TEXT, monto REAL, concepto TEXT, fecha TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, stock INTEGER, icono TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_ahorro (id INTEGER PRIMARY KEY, tasa REAL, activo INTEGER)''')
    
    # MIGRACIONES ROBUSTAS
    def add_col(table, col, type_def):
        try: c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {type_def}")
        except: pass

    add_col('usuarios', 'cuenta', 'TEXT')
    add_col('usuarios', 'saldo_cajita', 'REAL DEFAULT 0')
    add_col('transacciones', 'estado', "TEXT DEFAULT 'completado'")
    add_col('transacciones', 'autorizado_por', "TEXT DEFAULT 'Sistema'")
    
    c.execute("SELECT * FROM config_ahorro")
    if not c.fetchone(): c.execute("INSERT INTO config_ahorro (tasa, activo) VALUES (5.0, 1)") 
    
    c.execute("SELECT id FROM usuarios WHERE cuenta IS NULL OR cuenta = ''")
    for usr in c.fetchall(): c.execute("UPDATE usuarios SET cuenta = ? WHERE id = ?", (generar_cuenta(), usr[0]))
    c.execute("SELECT * FROM usuarios WHERE nombre='admin'")
    if not c.fetchone(): c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, cuenta) VALUES (?, ?, ?, ?, ?)", ('admin', 'admin', 1000000, '1234', generar_cuenta()))
    conn.commit(); conn.close()

# ==========================================
# 4. LÓGICA (CALLBACKS PARA BOTONES SEGUROS)
# ==========================================
def login(u, p):
    conn = get_connection(); df = pd.read_sql_query("SELECT * FROM usuarios WHERE nombre=? AND password=?", conn, params=(u, p)); conn.close(); return df

def crud_usuario(accion, nombre, rol=None, pwd=None, grado="", grupo=""):
    conn = get_connection(); c = conn.cursor()
    try:
        if accion == "crear":
            saldo = 1000000 if rol in (ROLES_ADMIN + ROLES_DOCENTE) else 0
            c.execute("INSERT INTO usuarios (nombre, rol, saldo, password, grado, grupo, cuenta, saldo_cajita) VALUES (?, ?, ?, ?, ?, ?, ?, 0)", (str(nombre), str(rol), saldo, str(pwd), str(grado), str(grupo), generar_cuenta()))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def transaccion(origen, destino, monto, concepto, tipo, estado="completado", operador="Sistema"):
    # GUARDA FECHA CON SEGUNDOS PARA EVITAR ERROR 'MIXED'
    conn = get_connection(); c = conn.cursor(); f = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (monto, origen))
        c.execute("UPDATE usuarios SET saldo=saldo+? WHERE nombre=?", (monto, destino))
        c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)", (f, origen, destino, monto, concepto, tipo, estado, operador))
        conn.commit(); return True
    except: return False
    finally: conn.close()

# --- CALLBACK COMPRA (TIENDA) ---
def cb_comprar_producto(usuario, id_prod):
    conn = get_connection(); c = conn.cursor()
    try:
        p = c.execute("SELECT * FROM productos WHERE id=?", (int(id_prod),)).fetchone()
        if not p: return
        nombre_prod, precio, stock = p[1], float(p[2]), int(p[3])
        saldo_data = c.execute("SELECT saldo FROM usuarios WHERE nombre=?", (usuario,)).fetchone()
        saldo = float(saldo_data[0])
        
        if stock > 0:
            if saldo >= precio:
                c.execute("UPDATE usuarios SET saldo=saldo-? WHERE nombre=?", (precio, usuario))
                c.execute("UPDATE productos SET stock=stock-1 WHERE id=?", (int(id_prod),))
                f = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, estado, autorizado_por) VALUES (?,?,?,?,?,?,?,?)", 
                          (f, usuario, "TIENDA", precio, f"{nombre_prod}", "compra", "pendiente", "TIENDA"))
                conn.commit()
                st.session_state['msg_tienda'] = {'tipo': 'success', 'texto': f"¡Felicidades! 🎉 Compraste {nombre_prod}."}
                st.session_state['show_balloons'] = True
            else:
                st.session_state['msg_tienda'] = {'tipo': 'error', 'texto': T('error_funds')}
        else:
            st.session_state['msg_tienda'] = {'tipo': 'error', 'texto': T('no_stock')}
    except Exception as e:
        st.session_state['msg_tienda'] = {'tipo': 'error', 'texto': str(e)}
    finally: conn.close()

# --- CALLBACK ENTREGA (ADMIN) ---
def cb_entregar_producto(id_trans):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE transacciones SET estado='entregado' WHERE id=?", (id_trans,))
    conn.commit(); conn.close()
    st.session_state['msg_admin'] = "Entrega marcada correctamente ✅"

def gestion_solicitud(accion, remitente=None, destinatario=None, monto=0.0, concepto="", id_sol=None, operador="Sistema"):
    conn = get_connection(); c = conn.cursor()
    try:
        if accion == "crear":
            s = c.execute("SELECT saldo FROM usuarios WHERE nombre=?", (remitente,)).fetchone()
            if s is None: return False, "Usuario no encontrado"
            s = s[0]
            if s >= monto:
                c.execute("INSERT INTO solicitudes (remitente, destinatario, monto, concepto, fecha) VALUES (?,?,?,?,?)", (remitente, destinatario, monto, concepto, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); return True, "OK"
            return False, "Saldo"
        elif accion == "aprobar":
            sol = c.execute("SELECT * FROM solicitudes WHERE id=?", (id_sol,)).fetchone()
            if sol is None: return False, "Solicitud no encontrada"
            s_rem = c.execute("SELECT saldo FROM usuarios WHERE nombre=?", (sol[1],)).fetchone()
            if s_rem is None: return False, "Remitente no encontrado"
            s_rem = s_rem[0]
            if s_rem >= sol[3]:
                transaccion(sol[1], sol[2], sol[3], sol[4], "transferencia", operador=operador)
                c.execute("DELETE FROM solicitudes WHERE id=?", (id_sol,)); conn.commit(); return True, "OK"
            else:
                c.execute("DELETE FROM solicitudes WHERE id=?", (id_sol,)); conn.commit(); return False, "No funds"
        elif accion == "rechazar":
            c.execute("DELETE FROM solicitudes WHERE id=?", (id_sol,)); conn.commit(); return True, "OK"
        return False, "Acción no válida"
    except Exception as e: return False, f"Error: {e}"
    finally: conn.close()

def marking_entregado(id_trans): # Mantenido por compatibilidad
    cb_entregar_producto(id_trans)

def get_config_ahorro():
    conn = get_connection(); conf = pd.read_sql("SELECT * FROM config_ahorro", conn).iloc[0]; conn.close()
    return conf

def set_config_ahorro(tasa, activo):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE config_ahorro SET tasa=?, activo=?", (tasa, 1 if activo else 0))
    conn.commit(); conn.close()

def mover_cajita(usuario, monto, direccion):
    conn = get_connection(); c = conn.cursor()
    try:
        user_data = c.execute("SELECT saldo, saldo_cajita FROM usuarios WHERE nombre=?", (usuario,)).fetchone()
        saldo_disp = user_data[0]
        saldo_caj = user_data[1]
        
        if direccion == 'in':
            if saldo_disp >= monto:
                c.execute("UPDATE usuarios SET saldo=saldo-?, saldo_cajita=saldo_cajita+? WHERE nombre=?", (monto, monto, usuario))
                conn.commit(); return True, "OK"
            return False, "Saldo insuficiente"
        else: # out
            if saldo_caj >= monto:
                c.execute("UPDATE usuarios SET saldo=saldo+?, saldo_cajita=saldo_cajita-? WHERE nombre=?", (monto, monto, usuario))
                conn.commit(); return True, "OK"
            return False, "Fondos insuficientes"
    except Exception as e: return False, str(e)
    finally: conn.close()

def pagar_rendimientos():
    conn = get_connection(); c = conn.cursor()
    try:
        conf = pd.read_sql("SELECT * FROM config_ahorro", conn).iloc[0]
        tasa = conf['tasa'] / 100.0
        if conf['activo']:
            users = c.execute("SELECT nombre, saldo_cajita FROM usuarios WHERE saldo_cajita > 0").fetchall()
            count = 0; total_pagado = 0; f = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for u in users:
                nombre = u[0]; saldo_c = u[1]; ganancia = saldo_c * tasa
                if ganancia > 0:
                    c.execute("UPDATE usuarios SET saldo_cajita=saldo_cajita+? WHERE nombre=?", (ganancia, nombre))
                    c.execute("INSERT INTO transacciones (fecha, remitente, destinatario, monto, concepto, tipo, autorizado_por) VALUES (?,?,?,?,?,?,?,?)", (f, "BANCO", nombre, ganancia, f"Rendimiento {conf['tasa']}%", "interes", "BANCO CENTRAL"))
                    count += 1; total_pagado += ganancia
            conn.commit(); return True, f"Pagado a {count} usuarios. Total: {total_pagado:.2f}"
        return False, "Sistema inactivo"
    except Exception as e: return False, str(e)
    finally: conn.close()

# ==========================================
# 5. UI PRINCIPAL
# ==========================================
init_db()

if 'usuario' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        if archivo_logo: st.image(archivo_logo, width=200)
        st.markdown(f"<h3 style='text-align:center; color:#0095a3'>{T('title')}</h3>", unsafe_allow_html=True)
        # KEY UNIQUE PARA LOGIN
        u = st.text_input(T('user') or "Usuario", key="login_user")
        p = st.text_input(T('pass') or "Contraseña", type="password", key="login_pass")
        
        idx_lang = ['ES', 'EN', 'FR'].index(st.session_state['lang'])
        nl = st.selectbox("Language", ['ES', 'EN', 'FR'], index=idx_lang, key="login_lang")
        if nl != st.session_state['lang']: 
            st.session_state['lang'] = nl
            if nl == 'ES': st.session_state['currency'] = 'MXN'
            elif nl == 'EN': st.session_state['currency'] = 'USD'
            elif nl == 'FR': st.session_state['currency'] = 'EUR'
            st.rerun()

        if st.button(T('login') or "Entrar", key="btn_login"):
            ud = login(u, p)
            if not ud.empty: st.session_state['usuario'] = u; st.session_state['rol'] = ud.iloc[0]['rol']; st.rerun()
            else: st.error("Error")

else:
    conn = get_connection()
    ud = pd.read_sql("SELECT saldo, cuenta, saldo_cajita FROM usuarios WHERE nombre=?", conn, params=(st.session_state['usuario'],)).iloc[0]
    saldo_actual = ud['saldo']; mi_cuenta = ud['cuenta']; saldo_cajita = ud['saldo_cajita']
    
    rol_user = st.session_state['rol']
    
    # ALERTAS
    count_sol = 0
    label_auth = T('auth')
    if rol_user in PERMISO_AUTORIZAR:
        count_sol = len(pd.read_sql("SELECT id FROM solicitudes", conn))
        if count_sol > 0: label_auth = f"{T('auth')} ({count_sol}) 🔴"
    
    count_entregas = 0
    label_store = T('admin_store')
    entregas_pendientes = pd.DataFrame()
    if rol_user in PERMISO_TIENDA:
        entregas_pendientes = pd.read_sql("SELECT * FROM transacciones WHERE tipo='compra' AND estado='pendiente'", conn)
        count_entregas = len(entregas_pendientes)
        if count_entregas > 0: label_store = f"{T('admin_store')} ({count_entregas}) 🔴"
    
    conn.close()

    with st.sidebar:
        if archivo_logo: st.image(archivo_logo, width=80)
        st.write(f"**{st.session_state['usuario']}** ({st.session_state['rol'].upper()})")
        st.write(f"💳 `{mi_cuenta}`")
        if count_sol > 0: st.error(f"{count_sol} {T('pending')} Auth")
        if count_entregas > 0: st.error(f"🚨 {count_entregas} {T('deliveries')}")
        
        with st.expander("⚙️ Config"):
            nl = st.selectbox("🌐", ['ES', 'EN', 'FR'], index=['ES','EN','FR'].index(st.session_state['lang']), key="sb_lang")
            if nl != st.session_state['lang']: 
                st.session_state['lang'] = nl
                if nl == 'ES': st.session_state['currency'] = 'MXN'
                elif nl == 'EN': st.session_state['currency'] = 'USD'
                elif nl == 'FR': st.session_state['currency'] = 'EUR'
                st.rerun()
            nc = st.selectbox("💱", ['MXN', 'USD', 'EUR'], index=['MXN','USD','EUR'].index(st.session_state['currency']), key="sb_curr")
            if nc != st.session_state['currency']: st.session_state['currency'] = nc; st.rerun()
            
        if st.button(T('exit') or "Salir", key="btn_exit"): del st.session_state['usuario']; st.rerun()

    if rol_user in PERMISO_OPERAR:
        st.title(T('title'))
        
        if rol_user in PERMISO_TIENDA and count_entregas > 0:
            st.markdown(f"""<div class="admin-alert">🚨 ATENCIÓN: Tienes {count_entregas} productos por entregar.</div>""", unsafe_allow_html=True)

        st.metric("🏦 RESERVAS", fmt_money(saldo_actual))
        
        if 'carrito_alumnos' not in st.session_state: st.session_state['carrito_alumnos'] = []
        
        mis_tabs = []; nombres_tabs = []
        nombres_tabs.append(T('ops'))
        if rol_user in PERMISO_TIENDA: nombres_tabs.append(label_store)
        if rol_user in PERMISO_AUTORIZAR: nombres_tabs.append(label_auth)
        if rol_user in ROLES_ADMIN: 
            nombres_tabs.append(T('manage'))
            nombres_tabs.append(T('central_bank'))
            nombres_tabs.append(T('audit'))
        
        tabs = st.tabs(nombres_tabs)
        
        with tabs[0]: 
            conn = get_connection(); df_alumnos = pd.read_sql("SELECT nombre, grado, grupo FROM usuarios WHERE rol='alumno'", conn); conn.close()
            c_izq, c_der = st.columns([1, 1])
            with c_izq:
                st.markdown(f"### {T('search')}")
                with st.expander(T('filters'), expanded=True):
                    c1, c2 = st.columns(2)
                    grados = [T('all')] + sorted([x for x in df_alumnos['grado'].unique() if x])
                    grupos = [T('all')] + sorted([x for x in df_alumnos['grupo'].unique() if x])
                    f_grado = c1.selectbox(T('grade'), grados, key="filter_grade")
                    f_grupo = c2.selectbox(T('group'), grupos, key="filter_group")
                    f_nombre = st.text_input(T('name'), key="filter_name")
                    df_filtrado = df_alumnos.copy()
                    if f_grado != T('all'): df_filtrado = df_filtrado[df_filtrado['grado'] == f_grado]
                    if f_grupo != T('all'): df_filtrado = df_filtrado[df_filtrado['grupo'] == f_grupo]
                    if f_nombre: df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(f_nombre, case=False)]
                
                st.write(f"**{T('results')}: {len(df_filtrado)}**")
                if st.button(f"{T('add_filtered')} ({len(df_filtrado)})", use_container_width=True, key="btn_add_filtered"):
                    for n in df_filtrado['nombre'].tolist():
                        if n not in st.session_state['carrito_alumnos']: st.session_state['carrito_alumnos'].append(n)
                    st.toast(f"Agregados", icon="🛒")

                with st.expander(f"{T('select_detail')} ({len(df_filtrado)})", expanded=False):
                    chk_all = st.checkbox(T('mark_all'), value=False, key="master_check_all")
                    df_display = df_filtrado[['nombre', 'grado', 'grupo']].copy()
                    df_display[T('select_col')] = chk_all 
                    edited_df = st.data_editor(df_display, column_config={T('select_col'): st.column_config.CheckboxColumn(T('select_col'), default=False)}, disabled=["nombre", "grado", "grupo"], hide_index=True, key="editor_alumnos")
                    if st.button(T('mark_add'), use_container_width=True, key="btn_add_checked"):
                        seleccionados = edited_df[edited_df[T('select_col')] == True]['nombre'].tolist()
                        for s in seleccionados:
                            if s not in st.session_state['carrito_alumnos']: st.session_state['carrito_alumnos'].append(s)
                        st.toast(f"Agregados", icon="🛒")

            with c_der:
                st.markdown(f"### {T('selected_list')} ({len(st.session_state['carrito_alumnos'])})")
                with st.expander("Ver Lista"): st.write(st.session_state['carrito_alumnos'])
                if st.button(T('clear_list'), use_container_width=True, key="btn_clear_cart"): st.session_state['carrito_alumnos'] = []; st.rerun()
                st.divider()
                st.markdown("### " + T('action'))
                op_visual = st.selectbox(T('action'), [T('charge_verb'), T('pay_verb')], key="sel_action")
                cat = OPCIONES_MULTAS if op_visual == T('charge_verb') else OPCIONES_PAGOS
                mot = st.selectbox(T('reason'), list(cat.keys()), key="sel_reason")
                
                # PRECIO DINAMICO
                monto = st.number_input(f"{T('amount')} ({st.session_state['currency']})", value=cat[mot], key=f"num_amount_{mot}")
                
                if st.button(T('exec_btn'), type="primary", use_container_width=True, key="btn_exec"):
                    if not st.session_state['carrito_alumnos']: st.warning("Lista vacía")
                    else:
                        rate = RATES[st.session_state['currency']]; base = monto / rate; bar = st.progress(0)
                        ex_cnt = 0
                        for i, a in enumerate(st.session_state['carrito_alumnos']):
                            t = "multa" if op_visual == T('charge_verb') else "ingreso"
                            # AUDITORIA: PROFE/ADMIN
                            op = st.session_state['usuario']
                            res = False
                            if op_visual == T('charge_verb'): res = transaccion(a, op, base, mot, t, operador=op)
                            else: res = transaccion(op, a, base, mot, t, operador=op)
                            if res: ex_cnt +=1
                            bar.progress((i+1)/len(st.session_state['carrito_alumnos']))
                        
                        if ex_cnt > 0:
                            st.session_state['carrito_alumnos'] = []
                            st.success(f"Éxito: {ex_cnt} operaciones."); time.sleep(1); st.rerun()

        if rol_user in PERMISO_TIENDA:
            idx_t = nombres_tabs.index(label_store)
            with tabs[idx_t]:
                if 'msg_admin' in st.session_state:
                    st.success(st.session_state['msg_admin']); del st.session_state['msg_admin']

                if not entregas_pendientes.empty:
                    st.error(f"📦 **{T('deliveries')} ({count_entregas})**")
                    for _, row in entregas_pendientes.iterrows():
                        with st.container():
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            col_a.write(f"**{row['remitente']}** compró: {row['concepto']}")
                            col_a.caption(f"Fecha: {row['fecha']}")
                            col_c.button(T('mark_delivered'), key=f"btn_dlv_{row['id']}", on_click=cb_entregar_producto, args=(row['id'],))
                    st.divider()
                else: st.info("✅ OK"); st.divider()

                if rol_user in ROLES_ADMIN:
                    st.write("### Agregar Producto")
                    with st.form("add_prod"):
                        c1, c2 = st.columns(2)
                        p_nom = c1.text_input(T('prod_name'))
                        p_ico = c2.text_input(T('prod_icon'), "🍔")
                        c3, c4 = st.columns(2)
                        p_prec = c3.number_input(T('prod_price'), min_value=1.0)
                        p_stock = c4.number_input(T('prod_stock'), min_value=1, value=10)
                        if st.form_submit_button(T('create')):
                            conn = get_connection(); c = conn.cursor()
                            c.execute("INSERT INTO productos (nombre, precio, stock, icono) VALUES (?,?,?,?)", (p_nom, p_prec, p_stock, p_ico))
                            conn.commit(); conn.close(); st.success("Creado"); st.rerun()
                    st.write("---")
                    conn = get_connection(); prods = pd.read_sql("SELECT * FROM productos", conn); conn.close()
                    st.dataframe(prods, use_container_width=True)

        if rol_user in PERMISO_AUTORIZAR:
            idx_a = nombres_tabs.index(label_auth)
            with tabs[idx_a]:
                conn = get_connection(); sol = pd.read_sql("SELECT * FROM solicitudes", conn); conn.close()
                if sol.empty: st.info("✅ OK")
                else:
                    for _, r in sol.iterrows():
                        rate = RATES[st.session_state['currency']]; monto_visual = r['monto'] * rate; str_monto = f"{SYMBOLS[st.session_state['currency']]}{monto_visual:,.2f}"
                        with st.expander(f"{str_monto} | {r['remitente']} -> {r['destinatario']}"):
                            c1,c2 = st.columns(2); k_auth_pre = f"pre_auth_{r['id']}"; k_auth_real = f"real_auth_{r['id']}"
                            if k_auth_pre not in st.session_state:
                                if c1.button("✅ Aprobar", key=k_auth_pre): st.session_state[k_auth_pre] = True; st.rerun()
                            else:
                                st.warning(T('sure'))
                                if st.button(T('confirm_auth'), key=k_auth_real): 
                                    gestion_solicitud("aprobar", id_sol=r['id'], operador=st.session_state['usuario']); 
                                    del st.session_state[k_auth_pre]; st.rerun()
                                if st.button("Cancelar", key=f"canc_auth_{r['id']}"): del st.session_state[k_auth_pre]; st.rerun()
                            if c2.button("❌ Rechazar", key=f"r{r['id']}"): gestion_solicitud("rechazar", id_sol=r['id']); st.rerun()

        if rol_user in ROLES_ADMIN:
            idx_m = nombres_tabs.index(T('manage'))
            with tabs[idx_m]:
                st.write(T('manage'))
                with st.expander("➕ Crear"):
                    # KEY ÚNICA (SOLUCIÓN A ERROR 1)
                    n = st.text_input("Nombre", key="admin_create_nombre"); p = st.text_input("Pass", key="admin_create_pass"); r = st.selectbox("Rol", ["alumno", "profesor", "administrativo"], key="admin_create_role")
                    if st.button("Crear", key="btn_create_user"): 
                        if n and p:
                            if crud_usuario("crear", n, r, p): st.success("OK")
                            else: st.error("Error")
                        else: st.error("Faltan datos")
                
                with st.expander(T('db_view')):
                    conn = get_connection(); df_u = pd.read_sql("SELECT * FROM usuarios", conn); conn.close()
                    ed = st.data_editor(df_u, num_rows="dynamic", use_container_width=True, key="editor_db_users")
                    if st.button(T('save_db'), key="btn_save_db"): st.success("Guardado") 

                with st.expander(T('bulk_upload')):
                    st.info("CSV: nombre, rol, password, grado, grupo"); up_csv = st.file_uploader("CSV", type="csv", key="file_upload_csv")
                    if up_csv and st.button(T('upload_btn'), key="btn_process_csv"):
                        try:
                            df = pd.read_csv(up_csv)
                            for _, row in df.iterrows(): crud_usuario("crear", row['nombre'], row['rol'], str(row['password']), str(row.get('grado','')), str(row.get('grupo','')))
                            st.success("OK")
                        except: st.error("Error CSV")
                
                with st.expander(T('backup')):
                    with open("banco_escolar.db", "rb") as f: st.download_button("Download DB", f, "backup.db", key="btn_download_db")

        if rol_user in ROLES_ADMIN:
            idx_b = nombres_tabs.index(T('central_bank'))
            with tabs[idx_b]:
                st.header(T('central_bank'))
                conf = get_config_ahorro()
                c1, c2 = st.columns(2)
                new_rate = c1.number_input(T('set_rate'), value=float(conf['tasa']), step=0.5, key="admin_rate")
                is_active = c2.checkbox("Sistema Activo", value=bool(conf['activo']), key="admin_active")
                if st.button("💾 Guardar Config", key="btn_save_conf"):
                    set_config_ahorro(new_rate, is_active); st.success("Guardado"); st.rerun()
                st.divider(); st.subheader("💰 " + T('pay_yields'))
                st.warning("Esto depositará dinero real a los alumnos basado en la tasa actual.")
                if 'confirm_pay_yields' not in st.session_state:
                    if st.button(T('pay_yields'), type="primary", key="btn_pay_start"): st.session_state['confirm_pay_yields'] = True; st.rerun()
                else:
                    st.error(T('sure'))
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("✅ SÍ, PAGAR A TODOS", key="btn_pay_yes"):
                        ok, msg = pagar_rendimientos()
                        if ok: st.balloons(); st.success(msg)
                        else: st.error(msg)
                        del st.session_state['confirm_pay_yields']
                    if col_no.button("Cancelar", key="btn_pay_no"): del st.session_state['confirm_pay_yields']; st.rerun()

        # === AUDITORÍA ===
        if rol_user in ROLES_ADMIN:
            idx_au = nombres_tabs.index(T('audit'))
            with tabs[idx_au]:
                st.subheader(f"🕵️‍♂️ {T('audit')}")
                st.write(T('audit_desc'))
                conn = get_connection()
                
                c_a1, c_a2, c_a3 = st.columns(3)
                tipos_disp = pd.read_sql("SELECT DISTINCT tipo FROM transacciones", conn)['tipo'].tolist()
                filtro_tipo_aud = c_a1.multiselect("Filtrar Tipo", tipos_disp)
                filtro_alumno = c_a2.text_input("Buscar Alumno")
                filtro_fecha_aud = c_a3.date_input("Fecha Específica", value=None)
                
                query = "SELECT * FROM transacciones WHERE 1=1"
                params = []
                
                if filtro_tipo_aud:
                    placeholders = ','.join(['?']*len(filtro_tipo_aud))
                    query += f" AND tipo IN ({placeholders})"
                    params.extend(filtro_tipo_aud)
                
                if filtro_alumno:
                    query += " AND (remitente LIKE ? OR destinatario LIKE ?)"
                    params.extend([f"%{filtro_alumno}%", f"%{filtro_alumno}%"])
                    
                df_aud = pd.read_sql(query + " ORDER BY id DESC", conn, params=params)
                conn.close()
                
                if not df_aud.empty and filtro_fecha_aud:
                    # SOLUCIÓN ERROR FECHA: format='mixed'
                    df_aud['dt_temp'] = pd.to_datetime(df_aud['fecha'], format='mixed', dayfirst=False)
                    df_aud = df_aud[df_aud['dt_temp'].apply(lambda x: x.date() if pd.notna(x) else None) == filtro_fecha_aud]
                    df_aud.drop(columns=['dt_temp'], inplace=True)

                if not df_aud.empty:
                    rate = RATES[st.session_state['currency']]
                    total_movido = df_aud['monto'].sum() * rate
                    k1, k2 = st.columns(2)
                    k1.metric("Movimientos", len(df_aud))
                    k2.metric("Volumen Total", f"{SYMBOLS[st.session_state['currency']]}{total_movido:,.2f}")
                    
                    df_aud['monto_visual'] = df_aud['monto'] * rate
                    df_display = df_aud[['id', 'fecha', 'remitente', 'destinatario', 'monto_visual', 'concepto', 'tipo', 'autorizado_por']].copy()
                    df_display.rename(columns={'monto_visual': f'Monto ({st.session_state["currency"]})'}, inplace=True)
                    st.dataframe(df_display, use_container_width=True)
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button("💾 Descargar Reporte (CSV)", data=csv, file_name="auditoria_completa.csv", mime="text/csv")
                else: st.warning("No se encontraron transacciones.")

    else:
        tabs_alu = st.tabs([T('home'), T('store'), T('savings'), T('hist'), T('analytics')]) 
        with tabs_alu[0]:
            st.markdown(f"## {T('title')}")
            st.metric(label=T('balance_user'), value=fmt_money(saldo_actual))
            st.markdown(f"### {T('transf')}")
            conn = get_connection(); df_al = pd.read_sql("SELECT nombre FROM usuarios WHERE rol='alumno'", conn); conn.close()
            dst = st.selectbox(T('send_to'), df_al['nombre'].tolist(), key="alu_send_to")
            c1, c2 = st.columns(2)
            mnt = c1.number_input(f"{T('amount')} ({st.session_state['currency']})", min_value=1.0, key="alu_amount")
            mot = c2.text_input(T('reason'), key="alu_reason")
            # SOLUCIÓN TRADUCCIÓN BOTÓN
            if st.button(T('send_btn'), key="alu_btn_send"):
                rate = RATES[st.session_state['currency']]; base = mnt / rate
                # AUDITORIA: ALUMNO
                ok, msg = gestion_solicitud("crear", remitente=st.session_state['usuario'], destinatario=dst, monto=base, concepto=mot, operador=st.session_state['usuario'])
                if ok: st.success("OK")
                else: st.error(msg)

        with tabs_alu[1]:
            st.markdown(f"### {T('store')}")
            if 'msg_tienda' in st.session_state:
                m = st.session_state['msg_tienda']
                if m['tipo'] == 'success':
                    st.success(m['texto'])
                    if 'show_balloons' in st.session_state: st.balloons(); del st.session_state['show_balloons']
                else: st.error(m['texto'])
                del st.session_state['msg_tienda']

            conn = get_connection(); prods = pd.read_sql("SELECT * FROM productos WHERE stock > 0", conn); conn.close()
            if prods.empty: st.info("No hay productos 😢")
            else:
                cols = st.columns(3)
                for i, (_, row) in enumerate(prods.iterrows()):
                    with cols[i % 3]: 
                        st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{row['icono']}</div>", unsafe_allow_html=True)
                        st.markdown(f"**{row['nombre']}**")
                        st.caption(f"{T('stock')}: {row['stock']}")
                        st.markdown(f"<h4 style='color:#0095a3; text-align: center;'>{fmt_money(row['precio'])}</h4>", unsafe_allow_html=True)
                        # SOLUCIÓN: CALLBACK
                        st.button(f"{T('buy')}", key=f"btn_buy_{row['id']}", use_container_width=True, on_click=cb_comprar_producto, args=(st.session_state['usuario'], row['id']))

        with tabs_alu[2]:
            st.markdown(f"### {T('savings')}")
            conf = get_config_ahorro()
            conn = get_connection()
            ganancia_total = conn.execute("SELECT SUM(monto) FROM transacciones WHERE destinatario=? AND tipo='interes'", (st.session_state['usuario'],)).fetchone()[0]
            conn.close()
            if ganancia_total is None: ganancia_total = 0.0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 " + T('balance_user'), fmt_money(saldo_actual))
            c2.metric("🏦 " + T('savings_bal'), fmt_money(saldo_cajita))
            c3.metric("🤑 " + T('total_earned'), fmt_money(ganancia_total))
            
            st.info(f"**{T('rate_info')}:** {conf['tasa']}%")
            
            if conf['activo']:
                with st.expander(T('deposit')):
                    dep_amount = st.number_input("Monto a depositar", min_value=1.0, key="dep_val")
                    if st.button("📥 " + T('deposit'), use_container_width=True, key="btn_dep"):
                        rate = RATES[st.session_state['currency']]; base = dep_amount / rate
                        ok, msg = mover_cajita(st.session_state['usuario'], base, 'in')
                        if ok: st.success("Guardado!"); time.sleep(1); st.rerun()
                        else: st.error(msg)
                        
                with st.expander(T('withdraw')):
                    ret_amount = st.number_input("Monto a retirar", min_value=1.0, key="ret_val")
                    if st.button("📤 " + T('withdraw'), use_container_width=True, key="btn_ret"):
                        rate = RATES[st.session_state['currency']]; base = ret_amount / rate
                        ok, msg = mover_cajita(st.session_state['usuario'], base, 'out')
                        if ok: st.success("Retirado!"); time.sleep(1); st.rerun()
                        else: st.error(msg)
            else:
                st.warning("⚠️ La caja de ahorro está cerrada temporalmente.")

        with tabs_alu[3]:
            st.write(f"### {T('hist')}")
            conn = get_connection()
            c_hist_1, c_hist_2, c_hist_3 = st.columns([1,1,1])
            filtro_tipo = c_hist_1.selectbox("Filtrar por", ["Todo", "Mes", "Día"], key="alu_hist_mode")
            f_fecha = None; f_mes = None; f_anio = None
            if filtro_tipo == "Día": f_fecha = c_hist_2.date_input("Fecha", datetime.datetime.now(), key="alu_hist_date")
            elif filtro_tipo == "Mes":
                f_mes = c_hist_2.selectbox("Mes", range(1,13), index=datetime.datetime.now().month-1, key="alu_hist_month")
                f_anio = c_hist_3.number_input("Año", value=datetime.datetime.now().year, step=1, key="alu_hist_year")
            
            df = pd.read_sql("SELECT fecha, remitente, destinatario, monto, concepto, autorizado_por FROM transacciones WHERE remitente=? OR destinatario=? ORDER BY id DESC", conn, params=(st.session_state['usuario'], str(st.session_state['usuario'])))
            conn.close()
            
            if not df.empty:
                # SOLUCIÓN ERROR FECHA: format='mixed'
                df['dt'] = pd.to_datetime(df['fecha'], format='mixed', dayfirst=False)
                def get_date(x):
                    if isinstance(x, datetime):
                        return x.date()
                    return None
                def get_month(x):
                    if isinstance(x, datetime):
                        return x.month
                    return None
                def get_year(x):
                    if isinstance(x, datetime):
                        return x.year
                    return None
                if filtro_tipo == "Día" and f_fecha: df = df[df['dt'].apply(get_date) == f_fecha]
                elif filtro_tipo == "Mes" and f_mes and f_anio: df = df[(df['dt'].apply(get_month) == f_mes) & (df['dt'].apply(get_year) == f_anio)]
                
                rate = RATES[st.session_state['currency']]
                st.info(f"Mostrando {len(df)} movimientos. Total: {SYMBOLS[st.session_state['currency']]}{(df['monto'].sum() * rate):,.2f}")
                df['monto'] = df['monto'] * rate
                df['monto'] = df['monto'].map(lambda x: f"{SYMBOLS[st.session_state['currency']]}{x:,.2f}")
                df = df.rename(columns={"fecha": "Fecha", "remitente": "De", "destinatario": "Para", "monto": "Monto", "concepto": "Concepto", "autorizado_por": "👮 Autorizado Por"})
                st.dataframe(df[["Fecha", "De", "Para", "Monto", "Concepto", "👮 Autorizado Por"]], use_container_width=True)
            else: st.info("Sin datos.")

        with tabs_alu[4]: # ANALYTICS
            st.write(T('analytics'))
            conn = get_connection()
            df_hist = pd.read_sql("SELECT * FROM transacciones WHERE remitente=? OR destinatario=?", conn, params=(st.session_state['usuario'], str(st.session_state['usuario'])))
            conn.close()
            if df_hist.empty: st.info("No data")
            else:
                user = st.session_state['usuario']
                # SOLUCIÓN ERROR FECHA: format='mixed'
                df_hist['fecha_dt'] = pd.to_datetime(df_hist['fecha'], format='mixed', dayfirst=False)
                def get_real_val(row):
                    if row['destinatario'] == user: return row['monto']
                    else: return -row['monto']
                df_hist['real_val'] = df_hist.apply(get_real_val, axis=1)
                total_in = df_hist[df_hist['real_val'] > 0]['real_val'].sum()
                total_out = df_hist[df_hist['real_val'] < 0]['real_val'].abs().sum()
                st.markdown(f"### {T('fin_health')}")
                if total_in >= total_out: st.markdown(f"""<div class="financial-tip-good"><h4>{T('tip_good_title')}</h4><p>{T('tip_good_desc')}</p></div>""", unsafe_allow_html=True)
                else: st.markdown(f"""<div class="financial-tip-bad"><h4>{T('tip_bad_title')}</h4><p>{T('tip_bad_desc')}</p></div>""", unsafe_allow_html=True)
                
                if HAS_PLOTLY:
                    df_hist['cumulative_balance'] = df_hist['real_val'].cumsum()
                    rate = RATES[st.session_state['currency']]
                    df_hist['visual_balance'] = df_hist['cumulative_balance'] * rate
                    fig_line = px.line(df_hist, x='fecha_dt', y='visual_balance', title=T('chart_trend'), markers=True)
                    fig_line.update_traces(line_color='#0095a3')
                    st.plotly_chart(fig_line, use_container_width=True)
                    df_expenses = df_hist[df_hist['real_val'] < 0].copy()
                    if not df_expenses.empty:
                        df_expenses['abs_val'] = df_expenses['real_val'].abs() * rate
                        fig_pie = px.pie(df_expenses, values='abs_val', names='tipo', title=T('chart_expenses'), color_discrete_sequence=px.colors.sequential.Teal)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    c1, c2 = st.columns(2)
                    c1.metric(T('total_in'), f"{SYMBOLS[st.session_state['currency']]}{total_in * rate:,.2f}")
                    c2.metric(T('total_out'), f"{SYMBOLS[st.session_state['currency']]}{total_out * rate:,.2f}")
                else: st.warning("⚠️ Instala 'plotly' para ver gráficas.")