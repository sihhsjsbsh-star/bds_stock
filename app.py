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
LOGO_PATH = "bds_image.jpg"
# ==========================================

# Configuración de la página
st.set_page_config(
    page_title=f"{NOMBRE_LOCAL} - Gestión",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SEGURIDAD ==========
def verificar_login(usuario, password):
    # En producción usar st.secrets.
    creds = {
        "Rosana": "bdse1975",
        "vendedor": "ventas123"
    }
    roles = {"Rosana": "admin", "vendedor": "vendedor"}
    nombres = {"Rosana": "Rosana Da Silva", "vendedor": "Vendedor Turno"}
    
    if usuario in creds and creds[usuario] == password:
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
    if not isinstance(texto, str): return str(texto).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

def fuzzy_match(query, text, threshold=0.7):
    if not query or not text: return False
    q = normalizar_texto(query)
    t = normalizar_texto(text)
    if q in t: return True
    return SequenceMatcher(None, q, t).ratio() >= threshold

def busqueda_inteligente(df, query, categoria=None, marca=None):
    df_res = df.copy()
    if categoria and categoria != 'Todas las categorías':
        df_res = df_res[df_res['CATEGORIA'] == categoria]
    if marca and marca != 'Todas las marcas':
        df_res = df_res[df_res['MARCA'] == marca]
    if query:
        mask = df_res.apply(lambda r: fuzzy_match(query, str(r['PRODUCTO'])) or fuzzy_match(query, str(r['MARCA'])), axis=1)
        df_res = df_res[mask]
    return df_res

# ========== ESTILOS CSS ==========
st.markdown("""
<style>
    :root { --primary: #D32F2F; --bg-card: #FFFFFF; --border: #E0E0E0; }
    
    /* LOGOS */
    [data-testid="stSidebar"] img { max-height: 150px; margin: 0 auto; display: block; border-radius: 10px; }
    
    /* TARJETAS */
    .producto-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .card-header { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 5px; }
    .card-sub { font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 15px; }
    
    /* PRECIOS */
    .price-tag-main {
        background: linear-gradient(135deg, #D32F2F, #B71C1C);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        margin: 10px 0;
    }
    .price-small {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #eee;
    }
    .price-label { font-size: 11px; text-transform: uppercase; color: #555; font-weight: bold; }
    .price-val { font-size: 16px; font-weight: bold; color: #333; }
    
    /* STOCK */
    .stock-ok { color: #2E7D32; font-weight: bold; background: #E8F5E9; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
    .stock-low { color: #C62828; font-weight: bold; background: #FFEBEE; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
    
    /* BOTONES */
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ========== DATA ==========
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# FIX: TTL AUMENTADO A 60 SEGUNDOS
@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    try:
        df = conn.read(worksheet="PRODUCTOS")
        return df.dropna(how='all')
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try:
        return conn.read(worksheet="VENTAS").dropna(how='all')
    except: return pd.DataFrame(columns=['FECHA','VENDEDOR','PRODUCTO','CANTIDAD','TIPO_PAGO','MONTO_TOTAL'])

def guardar_productos(df):
    # FIX: VALIDACIÓN DE NEGATIVOS
    cols_precio = ['CONTADO', '6 CUOTAS', '12 CUOTAS']
    for col in cols_precio:
        if col in df.columns and (df[col] < 0).any():
            st.error(f"⛔ Error: Se detectaron precios negativos en {col}. No se guardó nada.")
            return False
            
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()
    return True

def registrar_venta(vendedor, producto, cantidad, tipo_pago, monto_total):
    conn = get_connection()
    df_v = leer_ventas()
    nuevo = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': vendedor, 'PRODUCTO': producto,
        'CANTIDAD': cantidad, 'TIPO_PAGO': tipo_pago, 'MONTO_TOTAL': monto_total
    }])
    df_v = pd.concat([df_v, nuevo], ignore_index=True)
    conn.update(worksheet="VENTAS", data=df_v)
    st.cache_data.clear()

def actualizar_stock_venta(nombre_prod, cantidad):
    df = leer_productos()
    mask = df['PRODUCTO'] == nombre_prod
    if not mask.any(): return False
    
    idx = df[mask].index[0]
    actual = int(df.at[idx, 'STOCK'])
    if actual < cantidad: return False
    
    df.at[idx, 'STOCK'] = actual - cantidad
    guardar_productos(df)
    return True

# ========== TARJETA VISUAL (Card Renderer) ==========
def card_producto(row, idx, es_admin=False):
    # Preparar datos
    nombre = row['PRODUCTO']
    marca = row['MARCA']
    cat = row['CATEGORIA']
    stock = int(row['STOCK'])
    p_contado = float(row['CONTADO'])
    p_6 = float(row['6 CUOTAS'])
    p_12 = float(row['12 CUOTAS'])
    
    st.markdown(f"""
    <div class="producto-card">
        <div class="card-header">{nombre}</div>
        <div class="card-sub">{marca} | {cat}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="{ 'stock-ok' if stock > 2 else 'stock-low' }">STOCK: {stock}</span>
        </div>
        <div class="price-tag-main">
            <div style="font-size:12px; opacity:0.8;">CONTADO</div>
            ₲ {formato_guaranies(p_contado)}
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
            <div class="price-small">
                <div class="price-label">6 CUOTAS</div>
                <div class="price-val">₲ {formato_guaranies(p_6)}</div>
            </div>
            <div class="price-small">
                <div class="price-label">12 CUOTAS</div>
                <div class="price-val">₲ {formato_guaranies(p_12)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # LÓGICA DE BOTONES (VENTA O EDICIÓN)
    if not es_admin:
        # VISTA VENDEDOR
        if stock > 0:
            if st.button("🛒 VENDER", key=f"btn_v_{idx}"):
                st.session_state[f'v_mode_{idx}'] = True
                st.rerun()
            
            if st.session_state.get(f'v_mode_{idx}', False):
                with st.container(border=True):
                    st.info("Confirmar Venta")
                    cant = st.number_input("Cantidad", 1, stock, 1, key=f"q_{idx}")
                    pago = st.selectbox("Pago", ["Contado", "6 Cuotas", "12 Cuotas"], key=f"p_{idx}")
                    
                    p_unit = p_contado if pago == "Contado" else (p_6 if pago == "6 Cuotas" else p_12)
                    total = p_unit * cant
                    st.write(f"**Total: ₲ {formato_guaranies(total)}**")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅ CONFIRMAR", key=f"ok_{idx}"):
                        if actualizar_stock_venta(nombre, cant):
                            registrar_venta(st.session_state.username, nombre, cant, pago, total)
                            st.success("Venta Exitosa")
                            st.session_state[f'v_mode_{idx}'] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error de Stock")
                    
                    if c2.button("❌ CANCELAR", key=f"no_{idx}"):
                        st.session_state[f'v_mode_{idx}'] = False
                        st.rerun()
        else:
            st.error("AGOTADO")
    
    else:
        # VISTA ADMIN (EDICIÓN MÓVIL)
        if st.button("✏️ EDITAR", key=f"btn_e_{idx}"):
            st.session_state[f'e_mode_{idx}'] = True
            st.rerun()
            
        if st.session_state.get(f'e_mode_{idx}', False):
            with st.container(border=True):
                st.warning("Editando Producto")
                with st.form(key=f"form_{idx}"):
                    # FIX: Formulario completo para no perder datos
                    n_nom = st.text_input("Nombre", nombre)
                    n_marc = st.text_input("Marca", marca)
                    n_cat = st.text_input("Categoría", cat)
                    n_stk = st.number_input("Stock", value=stock)
                    
                    c_p1, c_p2, c_p3 = st.columns(3)
                    n_cont = c_p1.number_input("Contado", value=int(p_contado))
                    n_c6 = c_p2.number_input("6 Cuotas", value=int(p_6))
                    n_c12 = c_p3.number_input("12 Cuotas", value=int(p_12))
                    
                    if st.form_submit_button("💾 GUARDAR CAMBIO LOCAL"):
                        # FIX: Guardar fila completa para no perder columnas
                        if 'mobile_changes' not in st.session_state: st.session_state.mobile_changes = {}
                        
                        # Copiamos la fila original y actualizamos
                        nuevo_dato = row.to_dict()
                        nuevo_dato.update({
                            'PRODUCTO': n_nom, 'MARCA': n_marc, 'CATEGORIA': n_cat,
                            'STOCK': n_stk, 'CONTADO': n_cont,
                            '6 CUOTAS': n_c6, '12 CUOTAS': n_c12
                        })
                        
                        st.session_state.mobile_changes[idx] = nuevo_dato
                        st.session_state[f'e_mode_{idx}'] = False
                        st.success("Cambio en cola. Ve arriba a GUARDAR EN BD.")
                        st.rerun()

# ========== PÁGINAS ==========
def login_page():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        try: st.image(LOGO_PATH, use_container_width=True)
        except: st.header(NOMBRE_LOCAL)
        
        st.write("")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR", type="primary"):
            res = verificar_login(u, p)
            if res["valido"]:
                st.session_state.logged_in = True
                st.session_state.user_role = res["rol"]
                st.session_state.username = res["nombre"]
                st.rerun()
            else: st.error("Error de acceso")

def panel_admin():
    st.title("Panel Administrador")
    
    # GUARDADO MÓVIL MASTER
    if 'mobile_changes' in st.session_state and st.session_state.mobile_changes:
        st.warning(f"Tienes {len(st.session_state.mobile_changes)} cambios pendientes.")
        if st.button("💾 GUARDAR TODO EN BASE DE DATOS", type="primary"):
            df = leer_productos()
            for idx, cambios in st.session_state.mobile_changes.items():
                if idx in df.index:
                    for k, v in cambios.items(): df.at[idx, k] = v
            
            if guardar_productos(df):
                st.session_state.mobile_changes = {}
                st.success("Base de datos actualizada")
                time.sleep(1)
                st.rerun()

    tab1, tab2 = st.tabs(["INVENTARIO", "VENTAS"])
    
    with tab1:
        df = leer_productos()
        c1, c2 = st.columns([3,1])
        q = c1.text_input("Buscar producto...")
        modo_movil = c2.toggle("Vista Móvil", value=True)
        
        df_view = busqueda_inteligente(df, q) if q else df.copy()
        
        if not modo_movil:
            # TABLA DE ESCRITORIO
            edited = st.data_editor(df_view, num_rows="dynamic", use_container_width=True, height=500)
            if st.button("💾 GUARDAR CAMBIOS TABLA", type="primary"):
                # Update seguro
                df.loc[edited.index] = edited 
                if guardar_productos(df):
                    st.success("Guardado")
        else:
            # TARJETAS MÓVILES
            if df_view.empty:
                st.info("Sin resultados.")
            
            for idx, row in df_view.iterrows():
                card_producto(row, idx, es_admin=True)

    with tab2:
        st.dataframe(leer_ventas(), use_container_width=True)

def panel_vendedor():
    st.title(f"Hola, {st.session_state.username}")
    
    q = st.text_input("🔍 Buscar producto para vender...")
    
    df = leer_productos()
    
    # FIX: OPTIMIZACIÓN DE BÚSQUEDA
    if not q:
        st.info("Escribe algo para buscar o ver el inventario.")
        # Opcional: Mostrar top 5 más vendidos o random si quisieras
    else:
        res = busqueda_inteligente(df, q)
        st.caption(f"Mostrando {len(res)} productos")
        
        for idx, row in res.iterrows():
            card_producto(row, idx, es_admin=False)

# ========== MAIN ==========
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    with st.sidebar:
        try: st.image(LOGO_PATH, use_container_width=True)
        except: st.header("BDS")
        st.write(f"👤 {st.session_state.username}")
        if st.button("Cerrar Sesión"):
            # FIX: Limpieza segura de sesión
            keys_to_clear = ['logged_in', 'user_role', 'username', 'mobile_changes']
            for k in keys_to_clear:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
    
    if st.session_state.user_role == "admin":
        panel_admin()
    else:
        panel_vendedor()
