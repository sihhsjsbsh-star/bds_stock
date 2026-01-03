import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
import time
import unicodedata
import hashlib

# ========== CONFIGURACIÓN GLOBAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"
LOGO_PATH = "bds_image.jpg"
# ==========================================

st.set_page_config(
    page_title=NOMBRE_LOCAL,
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed" if 'logged_in' not in st.session_state or not st.session_state.logged_in else "expanded"
)

# ========== ESTILOS CSS "POS PROFESIONAL" ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Variables Semánticas */
    :root {
        --success: #2E7D32; /* Verde Dólar */
        --neutral: #1976D2; /* Azul Acción */
        --danger: #D32F2F;  /* Rojo Alerta */
        --bg-ticket: #FFFFFF;
    }

    .stApp { background-color: #F3F4F6; }

    /* TICKET DE VENTA (Columna Derecha) */
    .ticket-container {
        background-color: var(--bg-ticket);
        border: 2px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .ticket-header {
        text-align: center;
        border-bottom: 2px dashed #E5E7EB;
        padding-bottom: 10px;
        margin-bottom: 15px;
        font-weight: 800;
        color: #374151;
        letter-spacing: 1px;
    }
    .ticket-total {
        background-color: #ECFDF5;
        color: var(--success);
        font-size: 28px;
        font-weight: 900;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #6EE7B7;
        margin: 15px 0;
    }

    /* CARDS COMPACTAS (Columna Izquierda) */
    .product-card-mini {
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 5px solid var(--neutral);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        justify_content: space-between;
        align-items: center;
        transition: transform 0.1s;
    }
    .product-card-mini:hover { transform: scale(1.01); border-left-color: var(--success); }
    
    .mini-title { font-weight: 700; font-size: 15px; color: #111827; }
    .mini-price { font-weight: 800; color: #4B5563; font-size: 14px; }
    .mini-stock { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: #E5E7EB; color: #374151; font-weight: 700; }
    .stock-low { background: #FEE2E2; color: #991B1B; }

    /* LOGIN */
    .login-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
        border-top: 5px solid var(--danger);
    }
    
    /* BOTONES */
    div.stButton > button:first-child {
        font-weight: 700;
        border-radius: 8px;
        height: 45px;
        border: none;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ========== LÓGICA & DATOS ==========

def normalizar_texto(texto):
    if not isinstance(texto, str): return str(texto).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

def fuzzy_match(query, text, threshold=0.7):
    if not query or not text: return False
    q, t = normalizar_texto(query), normalizar_texto(text)
    return q in t or SequenceMatcher(None, q, t).ratio() >= threshold

def generar_id_unico(row):
    # Genera un hash único basado en nombre y marca para identificar productos sin usar el índice
    raw = f"{row['PRODUCTO']}_{row['MARCA']}".encode('utf-8')
    return hashlib.md5(raw).hexdigest()[:8]

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def formato_guaranies(valor):
    try: return f"{int(float(valor)):,}".replace(",", ".")
    except: return "0"

@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    try: 
        df = conn.read(worksheet="PRODUCTOS").dropna(how='all')
        cols_num = ['STOCK', 'CONTADO', '6 CUOTAS', '12 CUOTAS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # GENERAR ID ÚNICO (CRÍTICO PARA POS)
        df['ID_REF'] = df.apply(generar_id_unico, axis=1)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try: return conn.read(worksheet="VENTAS").dropna(how='all')
    except: return pd.DataFrame(columns=['FECHA','VENDEDOR','PRODUCTO','CANTIDAD','TIPO_PAGO','MONTO_TOTAL'])

def guardar_productos(df):
    # Antes de guardar, removemos la columna temporal ID_REF si existe
    df_save = df.drop(columns=['ID_REF'], errors='ignore')
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df_save)
    st.cache_data.clear()
    return True

def registrar_venta(vendedor, producto, cantidad, tipo_pago, monto_total):
    conn = get_connection()
    df = leer_ventas()
    nuevo = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': vendedor, 'PRODUCTO': producto,
        'CANTIDAD': cantidad, 'TIPO_PAGO': tipo_pago, 'MONTO_TOTAL': monto_total
    }])
    df = pd.concat([df, nuevo], ignore_index=True)
    conn.update(worksheet="VENTAS", data=df)
    st.cache_data.clear()

def actualizar_stock_pos(id_ref, cantidad):
    df = leer_productos()
    # Buscamos por ID ÚNICO, no por índice (mucho más seguro)
    mask = df['ID_REF'] == id_ref
    
    if not mask.any(): return False
    
    idx = df[mask].index[0]
    stock_actual = int(df.at[idx, 'STOCK'])
    
    if stock_actual < cantidad: return False
    
    df.at[idx, 'STOCK'] = stock_actual - cantidad
    return guardar_productos(df)

# ========== INTERFAZ POS (CAJA REGISTRADORA) ==========

def render_pos_interface(usuario):
    # Estado de la Caja
    if 'pos_cart' not in st.session_state: st.session_state.pos_cart = None
    
    col_catalogo, col_ticket = st.columns([0.65, 0.35], gap="large")
    
    df = leer_productos()

    # --- COLUMNA IZQUIERDA: CATÁLOGO ---
    with col_catalogo:
        st.subheader("📦 Catálogo")
        busqueda = st.text_input("🔎 Buscar producto...", placeholder="Ej: Split, Licuadora...", label_visibility="collapsed")
        
        if busqueda:
            mask = df.apply(lambda r: fuzzy_match(busqueda, str(r['PRODUCTO'])) or fuzzy_match(busqueda, str(r['MARCA'])), axis=1)
            df_filtro = df[mask]
        else:
            df_filtro = df

        # Lista Compacta
        if not df_filtro.empty:
            for _, row in df_filtro.iterrows():
                id_prod = row['ID_REF']
                stock = int(row['STOCK'])
                
                # Diseño Card Mini
                bg_stock = "stock-low" if stock <= 2 else ""
                html_card = f"""
                <div class="product-card-mini">
                    <div>
                        <div class="mini-title">{row['PRODUCTO']}</div>
                        <div style="font-size:12px; color:#6B7280;">{row['MARCA']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="mini-price">₲ {formato_guaranies(row['CONTADO'])}</div>
                        <span class="mini-stock {bg_stock}">STOCK: {stock}</span>
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
                # Botón de Acción (Azul Neutro)
                if stock > 0:
                    if st.button("➕ AGREGAR", key=f"add_{id_prod}"):
                        st.session_state.pos_cart = row.to_dict()
                else:
                    st.button("🚫 AGOTADO", disabled=True, key=f"dis_{id_prod}")
        else:
            st.info("No se encontraron productos.")

    # --- COLUMNA DERECHA: EL TICKET (CAJA) ---
    with col_ticket:
        st.markdown('<div class="ticket-container">', unsafe_allow_html=True)
        st.markdown('<div class="ticket-header">🎫 TICKET DE VENTA</div>', unsafe_allow_html=True)
        
        item = st.session_state.pos_cart
        
        if item:
            st.markdown(f"**PRODUCTO:**<br>{item['PRODUCTO']}", unsafe_allow_html=True)
            st.divider()
            
            # Controles de Venta
            stock_max = int(item['STOCK'])
            cant = st.number_input("Cantidad", min_value=1, max_value=stock_max, value=1)
            
            opciones_pago = {
                "Contado": float(item['CONTADO']),
                "6 Cuotas": float(item['6 CUOTAS']),
                "12 Cuotas": float(item['12 CUOTAS'])
            }
            pago = st.radio("Forma de Pago", list(opciones_pago.keys()))
            
            precio_unit = opciones_pago[pago]
            total = precio_unit * cant
            
            st.markdown(f"""
            <div class="ticket-total">
                <div style="font-size:12px; color:#059669; font-weight:600;">TOTAL A PAGAR</div>
                ₲ {formato_guaranies(total)}
            </div>
            """, unsafe_allow_html=True)
            
            # Botones de Acción (Semánticos)
            col_conf, col_cancel = st.columns(2)
            
            with col_conf:
                # BOTÓN VERDE (Éxito)
                if st.button("✅ COBRAR", type="primary", use_container_width=True):
                    if actualizar_stock_pos(item['ID_REF'], cant):
                        registrar_venta(usuario, item['PRODUCTO'], cant, pago, total)
                        st.balloons()
                        st.success("¡Venta Exitosa!")
                        st.session_state.pos_cart = None
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Error de Stock")
            
            with col_cancel:
                # BOTÓN ROJO (Cancelar)
                if st.button("❌ CANCELAR", use_container_width=True):
                    st.session_state.pos_cart = None
                    st.rerun()
            
        else:
            st.markdown("""
            <div style="text-align:center; padding:40px 0; color:#9CA3AF;">
                🛒<br>Selecciona un producto<br>para comenzar
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ========== VISTA ADMIN (Gestión + POS) ==========

def panel_admin():
    st.title("⚙️ Panel de Control")
    
    # Cola de guardado (se mantiene igual por seguridad)
    if 'mob_q' in st.session_state and st.session_state.mob_q:
        st.warning(f"⚠️ {len(st.session_state.mob_q)} cambios sin guardar")
        if st.button("💾 GUARDAR CAMBIOS AHORA"):
            df = leer_productos()
            for i, data in st.session_state.mob_q.items():
                if i in df.index:
                    for k,v in data.items(): df.at[i,k]=v
            guardar_productos(df)
            st.session_state.mob_q = {}
            st.success("Guardado"); st.rerun()

    tab1, tab2, tab3 = st.tabs(["🛒 CAJA (POS)", "📦 GESTIÓN INVENTARIO", "📊 REPORTES"])
    
    with tab1:
        render_pos_interface(st.session_state.username)
        
    with tab2:
        df = leer_productos()
        edited = st.data_editor(df.drop(columns=['ID_REF'], errors='ignore'), num_rows="dynamic", use_container_width=True, height=500)
        if st.button("💾 ACTUALIZAR INVENTARIO"):
            df_master = leer_productos()
            # Mapeo simple por índice (Admin debe tener cuidado al ordenar)
            # Idealmente aquí también usaríamos IDs, pero Streamlit data_editor es complejo.
            # Por ahora mantenemos lógica simple de reemplazo.
            guardar_productos(edited)
            st.success("Inventario Actualizado")

    with tab3:
        df_v = leer_ventas()
        if not df_v.empty:
            df_v['MONTO_TOTAL'] = pd.to_numeric(df_v['MONTO_TOTAL'], errors='coerce').fillna(0)
            st.metric("Total Vendido Histórico", f"₲ {formato_guaranies(df_v['MONTO_TOTAL'].sum())}")
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("Sin datos.")

# ========== MAIN ==========

def login_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        try: st.image(LOGO_PATH, width=120) 
        except: st.title("🔴 BDS")
        st.markdown("### Acceso al Sistema")
        
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        
        if st.button("INGRESAR", use_container_width=True):
            creds = {"Rosana":"bdse1975", "vendedor":"ventas123", "Yuliany":"yuli2026", "Externo":"ext123"}
            users = {
                "Rosana": {"role":"admin", "name":"Rosana Da Silva"},
                "vendedor": {"role":"vendedor", "name":"Walter"},
                "Yuliany": {"role":"vendedor", "name":"Yuliany"},
                "Externo": {"role":"vendedor", "name":"Externo"}
            }
            if u in creds and creds[u] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = users[u]["role"]
                st.session_state.username = users[u]["name"]
                st.rerun()
            else:
                st.error("Acceso Denegado")
        st.markdown('</div>', unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    with st.sidebar:
        try: st.image(LOGO_PATH, use_container_width=True)
        except: pass
        st.markdown(f"### Hola, {st.session_state.username}")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    if st.session_state.user_role == "admin":
        panel_admin()
    else:
        # Vendedores van directo al POS
        st.title(f"Punto de Venta")
        render_pos_interface(st.session_state.username)
