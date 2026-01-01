import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
import time
import unicodedata

# ========== CONFIGURACIÓN GLOBAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"
TELEFONO_LOCAL = "+595 982 627824"
DIRECCION_LOCAL = "Avenida 1ro. de Mayo &, Carlos Antonio López, Capiatá"
LOGO_PATH = "logo_bds.png" 
# ==========================================

# Configuración de la página
st.set_page_config(
    page_title=f"{NOMBRE_LOCAL} - Gestión",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SEGURIDAD Y USUARIOS (SECRETS) ==========
def verificar_login(usuario, password):
    # En producción usar st.secrets. Aquí hardcodeamos para demo funcional inmediata
    # Si tienes st.secrets configurado, úsalo.
    creds = {
        "Rosana": "bdse1975",
        "vendedor": "ventas123"
    }
    roles = {"Rosana": "admin", "vendedor": "vendedor"}
    nombres = {"Rosana": "Rosana Da Silva", "vendedor": "Vendedor Turno"}
    
    # Intento de usar secrets si existen, sino fallback al diccionario local
    try:
        pass_db = st.secrets["passwords"]
    except:
        pass_db = creds

    if usuario in pass_db and pass_db[usuario] == password:
        return {
            "valido": True,
            "rol": roles.get(usuario, "vendedor"),
            "nombre": nombres.get(usuario, usuario)
        }
    
    time.sleep(1) # Anti fuerza bruta
    return {"valido": False}

# ========== UTILIDADES ==========
def formato_guaranies(valor):
    try:
        valor_int = int(float(valor))
        return f"{valor_int:,}".replace(",", ".")
    except:
        return "0"

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return str(texto).lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def fuzzy_match(query, text, threshold=0.7):
    """Búsqueda difusa real usando SequenceMatcher"""
    if not query or not text:
        return False
    
    q_norm = normalizar_texto(query)
    t_norm = normalizar_texto(text)
    
    # 1. Coincidencia directa (substring)
    if q_norm in t_norm:
        return True
    
    # 2. Coincidencia difusa (levenshtein/ratio)
    ratio = SequenceMatcher(None, q_norm, t_norm).ratio()
    if ratio >= threshold:
        return True
        
    return False

def busqueda_inteligente(df, query, categoria=None, marca=None):
    df_resultado = df.copy()
    
    if categoria and categoria != 'Todas las categorías':
        df_resultado = df_resultado[df_resultado['CATEGORIA'] == categoria]
    
    if marca and marca != 'Todas las marcas':
        df_resultado = df_resultado[df_resultado['MARCA'] == marca]
    
    if query:
        # Aplicamos fuzzy match fila por fila
        mascara = df_resultado.apply(
            lambda row: fuzzy_match(query, str(row['PRODUCTO'])) or 
                        fuzzy_match(query, str(row['MARCA'])),
            axis=1
        )
        df_resultado = df_resultado[mascara]
    
    return df_resultado

# ========== ESTILOS CSS ==========
st.markdown("""
<style>
    :root { --primary: #E53935; --bg-card: #FFFFFF; --border: #E5E7EB; }
    .stButton > button { border-radius: 8px; font-weight: 700; text-transform: uppercase; }
    .stButton > button[kind="primary"] { background: var(--primary); color: white; }
    .producto-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stock-badge { padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; background: #eee; }
    .stock-bajo { background: #FEE2E2; color: #DC2626; }
    .stock-alto { background: #D1FAE5; color: #059669; }
</style>
""", unsafe_allow_html=True)

# ========== DATA MANAGER ==========
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=30)
def leer_productos():
    conn = get_connection()
    try:
        df = conn.read(worksheet="PRODUCTOS")
        # Aseguramos que el índice sea único y limpio si viene sucio
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def leer_ventas():
    conn = get_connection()
    try:
        return conn.read(worksheet="VENTAS").dropna(how='all')
    except:
        return pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])

def guardar_productos(df):
    # Validaciones críticas
    if 'CONTADO' in df.columns and (df['CONTADO'] < 0).any():
        st.error("⛔ Error: Precios negativos detectados.")
        return False
    
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()
    return True

def registrar_venta(vendedor, producto, cantidad, tipo_pago, monto_total):
    conn = get_connection()
    df_ventas = leer_ventas()
    nueva_venta = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': vendedor, 'PRODUCTO': producto,
        'CANTIDAD': cantidad, 'TIPO_PAGO': tipo_pago, 'MONTO_TOTAL': monto_total
    }])
    df_ventas = pd.concat([df_ventas, nueva_venta], ignore_index=True)
    conn.update(worksheet="VENTAS", data=df_ventas)
    st.cache_data.clear()

def actualizar_stock(df_productos, producto_nombre, cantidad_vendida):
    mask = df_productos['PRODUCTO'] == producto_nombre
    if not mask.any(): return False
    
    idx = df_productos[mask].index[0]
    stock_actual = df_productos.at[idx, 'STOCK']
    
    if stock_actual < cantidad_vendida:
        st.error("⛔ Stock insuficiente.")
        return False
    
    df_productos.at[idx, 'STOCK'] = stock_actual - cantidad_vendida
    return guardar_productos(df_productos)

# ========== UI COMPONENTS ==========
def render_logo():
    try:
        st.sidebar.image(LOGO_PATH, use_container_width=True)
    except:
        st.sidebar.markdown(f"## {NOMBRE_LOCAL}")

def renderizar_tarjeta_venta(row, idx):
    stock = int(row['STOCK'])
    color = "stock-bajo" if stock < 3 else "stock-alto"
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{row['PRODUCTO']}**")
        c1.caption(f"{row['MARCA']}")
        c2.markdown(f"<span class='stock-badge {color}'>{stock}</span>", unsafe_allow_html=True)
        
        st.write(f"💰 **₲ {formato_guaranies(row['CONTADO'])}**")
        
        if stock > 0:
            if st.button("🛒 Vender", key=f"v_{idx}", use_container_width=True):
                st.session_state[f'selling_{idx}'] = True
                st.rerun()
            
            if st.session_state.get(f'selling_{idx}', False):
                with st.container():
                    cant = st.number_input("Cant", 1, stock, 1, key=f"q_{idx}")
                    pago = st.selectbox("Pago", ["Contado", "6 Cuotas", "12 Cuotas"], key=f"p_{idx}")
                    
                    precio = float(row['CONTADO']) if pago == "Contado" else (float(row['6 CUOTAS']) if pago == "6 Cuotas" else float(row['12 CUOTAS']))
                    total = precio * cant
                    st.write(f"Total: ₲ {formato_guaranies(total)}")
                    
                    c_ok, c_cancel = st.columns(2)
                    if c_ok.button("✅", key=f"ok_{idx}", use_container_width=True):
                        df_fresh = leer_productos()
                        if actualizar_stock(df_fresh, row['PRODUCTO'], cant):
                            registrar_venta(st.session_state.username, row['PRODUCTO'], cant, pago, total)
                            st.success("Vendido!")
                            st.session_state[f'selling_{idx}'] = False
                            time.sleep(1)
                            st.rerun()
                    
                    if c_cancel.button("❌", key=f"no_{idx}", use_container_width=True):
                        st.session_state[f'selling_{idx}'] = False
                        st.rerun()

# ========== PÁGINAS ==========
def panel_admin():
    st.title("Panel Administrador")
    
    tab_prod, tab_rep = st.tabs(["Inventario", "Reportes"])
    
    with tab_prod:
        # Cargar BD Maestra
        df_master = leer_productos()
        
        col_s, col_v = st.columns([3, 1])
        query = col_s.text_input("🔍 Buscar producto...")
        mobile_mode = col_v.toggle("Modo Móvil", value=True)
        
        # Filtrar (Mantiene índices originales del master)
        if query:
            df_view = busqueda_inteligente(df_master, query)
        else:
            df_view = df_master.copy()
            
        if not mobile_mode:
            # --- DESKTOP: DATA EDITOR ---
            st.info("💡 Modifica y guarda. (Filtros respetados)")
            df_edited = st.data_editor(
                df_view,
                num_rows="dynamic",
                use_container_width=True,
                height=500,
                key="desktop_editor"
            )
            
            if st.button("💾 Guardar Cambios (Desktop)", type="primary"):
                try:
                    # FIX CRÍTICO 1: Actualizar usando índices para respetar filtros
                    df_master.loc[df_edited.index] = df_edited
                    
                    # Manejo de filas nuevas (si se agregaron en el editor)
                    # data_editor usa índices nuevos para filas agregadas, hay que concatenar
                    nuevos_indices = df_edited.index.difference(df_master.index)
                    if not nuevos_indices.empty:
                        filas_nuevas = df_edited.loc[nuevos_indices]
                        df_master = pd.concat([df_master, filas_nuevas])
                    
                    if guardar_productos(df_master):
                        st.success("✅ BD Actualizada Correctamente")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    
        else:
            # --- MOBILE: CARDS ---
            if df_view.empty:
                st.warning("No hay resultados.")
            
            # Estado temporal para cambios móviles
            if 'mobile_buffer' not in st.session_state:
                st.session_state.mobile_buffer = {}

            # Renderizar tarjetas
            for idx, row in df_view.iterrows():
                # Usamos el índice original (idx) como clave única
                has_changes = idx in st.session_state.mobile_buffer
                bg_color = "#f0f2f6" if has_changes else "white"
                
                with st.expander(f"{'✏️ ' if has_changes else ''}{row['PRODUCTO']} (Stock: {row['STOCK']})"):
                    with st.form(key=f"mform_{idx}"):
                        n_prod = st.text_input("Producto", row['PRODUCTO'])
                        c1, c2 = st.columns(2)
                        n_stock = c1.number_input("Stock", min_value=0, value=int(row['STOCK']))
                        n_precio = c2.number_input("Contado", min_value=0, value=int(row['CONTADO']))
                        
                        if st.form_submit_button("Aplicar"):
                            # Guardamos en buffer usando el índice original
                            st.session_state.mobile_buffer[idx] = {
                                'PRODUCTO': n_prod,
                                'STOCK': n_stock,
                                'CONTADO': n_precio,
                                # Aseguramos mantener otras columnas vitales si es necesario
                                'MARCA': row['MARCA'], 
                                'CATEGORIA': row['CATEGORIA'],
                                '6 CUOTAS': row['6 CUOTAS'],
                                '12 CUOTAS': row['12 CUOTAS']
                            }
                            st.success("Cambio en cola. Guarda arriba.")
                            st.rerun()
            
            # Botón de Guardado Móvil
            if st.session_state.mobile_buffer:
                st.warning(f"Tienes {len(st.session_state.mobile_buffer)} cambios sin guardar.")
                if st.button("💾 GUARDAR TODO (MÓVIL)", type="primary"):
                    try:
                        df_fresh = leer_productos() # Cargar BD fresca
                        
                        # Aplicar cambios por índice
                        for idx, data in st.session_state.mobile_buffer.items():
                            if idx in df_fresh.index:
                                for col, val in data.items():
                                    df_fresh.at[idx, col] = val
                        
                        if guardar_productos(df_fresh):
                            st.session_state.mobile_buffer = {} # Limpiar cola
                            st.success("✅ Cambios móviles guardados")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab_rep:
        st.dataframe(leer_ventas(), use_container_width=True)

def panel_vendedor():
    st.title("Punto de Venta")
    q = st.text_input("🔍 Buscar...")
    
    df = leer_productos()
    res = busqueda_inteligente(df, q) if q else df
    
    st.info(f"Mostrando {len(res)} productos")
    for idx, row in res.iterrows():
        renderizar_tarjeta_venta(row, idx)

# ========== MAIN ==========
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.title(NOMBRE_LOCAL)
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                res = verificar_login(u, p)
                if res["valido"]:
                    st.session_state.logged_in = True
                    st.session_state.user_role = res["rol"]
                    st.session_state.username = res["nombre"]
                    st.rerun()
                else:
                    st.error("Error de credenciales")
    else:
        with st.sidebar:
            render_logo()
            st.write(f"👤 {st.session_state.username}")
            if st.button("Cerrar Sesión"):
                # FIX 4: Limpieza de estado al salir
                for key in ['logged_in', 'user_role', 'username', 'mobile_buffer']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        if st.session_state.user_role == "admin":
            panel_admin()
        else:
            panel_vendedor()

if __name__ == "__main__":
    main()
