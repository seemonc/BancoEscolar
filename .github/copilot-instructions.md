# Copilot Instructions for Banco Summerhill

## Project Overview
- **Banco Summerhill** is una app Streamlit para gestión bancaria escolar (usuarios, transacciones, tienda, cajita de ahorro).
- Toda la lógica y UI está en el archivo banco.py (carpeta raíz).
- Los datos se guardan en el SQLite local banco_summerhill_v4.db.
- Soporta roles: admin, profesor, staff, alumno (cada uno con permisos distintos).

## Componentes y Flujo de Datos
- UI: Pestañas Streamlit para login, dashboard, tienda, operaciones, historial, analytics y administración.
- Base de datos: Tablas usuarios, transacciones, productos, config_ahorro, solicitudes (ver función init_db en banco.py).
- Permisos: El rol del usuario determina qué pestañas y acciones ve.
- Tienda: Admins crean/gestionan productos, alumnos compran y confirman entrega.
- Cajita: Alumnos depositan/retiran, admins pagan intereses a todos los ahorradores.
- Multi-idioma: ES/EN/FR, con conversión de moneda.

## Flujo de trabajo para desarrolladores
- Ejecutar: `streamlit run banco.py`
- Instalar dependencias: `pip install -r requirements.txt` (streamlit, pandas, plotly)
- Reset DB: Borra banco_summerhill_v4.db. Usa el sidebar para backup/restore.
- No hay tests automáticos, solo pruebas manuales vía UI.
- Debug: Usa rerun de Streamlit y el sidebar para resetear estado.

## Patrones del proyecto
- Toda la lógica y UI está en banco.py (carpeta raíz).
- Uso intensivo de st.session_state para manejo de sesión y usuario.
- CSS personalizado para look premium y dark mode.
- Los checks de permisos/roles están centralizados al inicio del archivo.
- Multi-idioma con el diccionario TRANS y función T().
- Gestión de productos/usuarios vía expanders y forms de Streamlit.
- Acceso a base de datos solo por helpers (get_connection, transaccion_core, etc).

## Integraciones
- Plotly: Para analytics (opcional, recomendado).
- Importar usuarios por CSV (solo admin, vía UI).
- Subida/descarga de respaldo DB desde el sidebar.

## Ejemplos
- Para features solo admin: verifica `st.session_state['rol'] == 'admin'` antes de mostrar UI.
- Para nuevo tipo de transacción: agrega en la tabla transacciones y los forms correspondientes.
- Para nuevo idioma: extiende el diccionario TRANS y el selector de idioma.

## Referencias
- Lógica principal: banco.py (carpeta raíz)
- Dependencias: requirements.txt (carpeta raíz)
- Esquema DB: función init_db en banco.py

---
Para dudas o mejoras, revisa banco.py (carpeta raíz), es la única fuente de verdad.
