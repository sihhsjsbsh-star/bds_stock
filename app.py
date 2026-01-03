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

# ========== ESTILOS CSS ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    :root {
        --success: #2E7D32;
        --neutral: #1976D2;
        --danger: #D32F2F;
    }

    .stApp { background-color: #F3F4F6; }

    /* Métricas Globales (Arriba) */
    div[data-testid="stMetric"] {
        background-color: white; padding: 15px; border-radius: 10px;
        border: 1px solid #E5E7EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
    }

    /* Card de Producto */
    .product-card-mini {
        background: white; border-radius: 8px; padding: 15px;
        margin-bottom: 10px; border-left: 5px solid var(--neutral);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; justify_content: space-between; align-items: center;
    }
    .mini-title { font-weight: 700; font-size: 16px; color: #111827; }
    .mini-price { font-weight: 800; color: #4B5563; font-size: 15px; }
    .mini-stock { font-size: 11px; padding: 4px 10px; border-radius: 12px; background: #E5E7EB; color: #374151; font-weight: 700; }
    .stock-low { background: #FEE2E2; color: #991B1B; }

    .login-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
        border-top: 5px solid var(--danger);
    }
    
    /* Botones más grandes */
    div.stButton > button:first-child {
        font-weight: 700; border-radius: 8px; height: 45px; border: none; width: 100%;
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
        df = conn.read(worksheet="PRODUCTOS")
        # LIMPIEZA DE FILAS VACÍAS
        df = df.dropna(subset=['PRODUCTO'])
        df = df[df['PRODUCTO'].str.strip() != ''] 
        
        cols_num = ['STOCK', 'CONTADO', '6 CUOTAS', '12 CUOTAS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # ID ÚNICO BLINDADO (Usa hash + índice para evitar error de duplicados)
        df['ID_REF'] = [hashlib.md5(f"{r.PRODUCTO}_{i}".encode()).hexdigest()[:10] for i, r in df.iterrows()]
        return df
    except Exception as e: 
        st.error(f"Error leyendo datos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try: return conn.read(worksheet="VENTAS").dropna(how='all')
    except: return pd.DataFrame(columns=['FECHA','VENDEDOR','PRODUCTO','CANTIDAD','TIPO_PAGO','MONTO_TOTAL'])

def guardar_productos(df):
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
    mask = df['ID_REF'] == id_ref
    if not mask.any(): return False
    idx = df[mask].index[0]
    stock_actual = int(df.at[idx, 'STOCK'])
    if stock_actual < cantidad: return False
    df.at[idx, 'STOCK'] = stock_actual - cantidad
    return guardar_productos(df)

# ========== VENTANA EMERGENTE (DIALOG) ==========
# Esta es la magia que evita que tengas que subir y bajar

@st.dialog("🎫 PROCESAR VENTA")
def popup_venta(item, usuario):
    st.markdown(f"### {item['PRODUCTO']}")
    st.markdown(f"<small>{item['MARCA']}</small>", unsafe_allow_html=True)
    st.divider()
    
    stock_max = int(item['STOCK'])
    c1, c2 = st.columns(2)
    cant = c1.number_input("Cantidad", 1, stock_max, 1)
    
    pago = st.radio("Forma de Pago", ["Contado", "6 Cuotas", "12 Cuotas"], horizontal=True)
    
    precios = {
        "Contado": float(item['CONTADO']),
        "6 Cuotas": float(item['6 CUOTAS']),
        "12 Cuotas": float(item['12 CUOTAS'])
    }
    total = precios[pago] * cant
    
    st.markdown(f"""
    <div style="background:#ECFDF5; color:#065F46; padding:15px; border-radius:8px; text-align:center; border:1px solid #6EE7B7; margin-top:10px;">
        <div style="font-size:12px; font-weight:bold;">TOTAL A COBRAR</div>
        <div style="font-size:24px; font-weight:900;">₲ {formato_guaranies(total)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_ok, col_no = st.columns(2)
    if col_ok.button("✅ CONFIRMAR", type="primary", use_container_width=True):
        if actualizar_stock_pos(item['ID_REF'], cant):
            registrar_venta(usuario, item['PRODUCTO'], cant, pago, total)
            st.toast("¡Venta registrada con éxito!", icon="🎉")
            time.sleep(1)
            st.rerun()
        else:
            st.error("¡Stock insuficiente!")
            
    if col_no.button("Cerrar", use_container_width=True):
        st.rerun()

# ========== INTERFAZ POS ==========

def render_pos_interface(usuario):
    st.subheader("📦 Catálogo de Productos")
    
    # Buscador y Filtros
    df = leer_productos()
    busqueda = st.text_input("🔎 Buscar...", placeholder="Escribe el nombre o marca...", label_visibility="collapsed")
    
    if busqueda:
        mask = df.apply(lambda r: fuzzy_match(busqueda, str(r['PRODUCTO'])) or fuzzy_match(busqueda, str(r['MARCA'])), axis=1)
        df_filtro = df[mask]
    else:
        df_filtro = df

    # Renderizado de lista
    if not df_filtro.empty:
        # Usamos enumerate para generar keys 100% únicas y evitar el error "DuplicateElementKey"
        for i, row in df_filtro.iterrows():
            id_unico = f"{row['ID_REF']}_{i}" # Key compuesta
            stock = int(row['STOCK'])
            bg_stock = "stock-low" if stock <= 2 else ""
            
            # Tarjeta Visual
            st.markdown(f"""
            <div class="product-card-mini">
                <div style="flex:3;">
                    <div class="mini-title">{row['PRODUCTO']}</div>
                    <div style="font-size:12px; color:#6B7280;">{row['MARCA']}</div>
                </div>
                <div style="flex:1; text-align:right;">
                    <div class="mini-price">₲ {formato_guaranies(row['CONTADO'])}</div>
                    <span class="mini-stock {bg_stock}">Stock: {stock}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón de Acción
            if stock > 0:
                # Al hacer clic, se abre el POPUP. No hay scroll.
                if st.button("🛒 VENDER", key=f"btn_{id_unico}"):
                    popup_venta(row, usuario)
            else:
                st.button("🚫 AGOTADO", disabled=True, key=f"dis_{id_unico}")
    else:
        st.info("No se encontraron productos.")

# ========== PANEL ADMIN ==========

def panel_admin():
    st.title("⚙️ Panel de Control")
    
    # Métricas Globales (Arriba)
    df = leer_productos()
    if not df.empty:
        total_plata = (df['STOCK'] * df['CONTADO']).sum()
        items_bajos = df[df['STOCK'] <= 2].shape[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Valor Inventario", f"₲ {formato_guaranies(total_plata)}")
        m2.metric("⚠️ Stock Crítico", f"{items_bajos} productos", delta="- RIESGO" if items_bajos > 0 else "OK", delta_color="inverse")
        m3.metric("📦 Total Items", f"{len(df)}")
    
    if 'mob_q' in st.session_state and st.session_state.mob_q:
        st.warning(f"⚠️ {len(st.session_state.mob_q)} cambios sin guardar")
        if st.button("💾 GUARDAR CAMBIOS AHORA"):
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
        columnas_visibles = [c for c in df.columns if c != 'ID_REF']
        edited = st.data_editor(df[columnas_visibles], num_rows="dynamic", use_container_width=True, height=500)
        if st.button("💾 ACTUALIZAR INVENTARIO"):
            guardar_productos(edited)
            st.success("Inventario Actualizado")

    with tab3:
        df_v = leer_ventas()
        if not df_v.empty:
            st.subheader("🏆 Ranking Vendedores")
            df_v['MONTO_TOTAL'] = pd.to_numeric(df_v['MONTO_TOTAL'], errors='coerce').fillna(0)
            ranking = df_v.groupby('VENDEDOR')['MONTO_TOTAL'].sum().reset_index().sort_values(by='MONTO_TOTAL', ascending=False)
            
            c_rank1, c_rank2 = st.columns([1, 2])
            ranking_display = ranking.copy()
            ranking_display['TOTAL'] = ranking_display['MONTO_TOTAL'].apply(lambda x: f"₲ {formato_guaranies(x)}")
            c_rank1.dataframe(ranking_display[['VENDEDOR', 'TOTAL']], hide_index=True, use_container_width=True)
            c_rank2.bar_chart(ranking, x='VENDEDOR', y='MONTO_TOTAL', color="#2E7D32")
            
            st.divider()
            st.subheader("📝 Historial")
            st.dataframe(df_v, use_container_width=True)
        else: st.info("No hay ventas registradas.")

# ========== LOGIN ==========

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
            else: st.error("Acceso Denegado")
        st.markdown('</div>', unsafe_allow_html=True)

# ========== MAIN ==========

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    with st.sidebar:
        try: st.image(LOGO_PATH, use_container_width=True)
        except: pass
        st.divider()
        st.markdown(f"👤 **{st.session_state.username}**")
        st.markdown(f"🔑 Rol: **{st.session_state.user_role.upper()}**")
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.clear(); st.rerun()

    if st.session_state.user_role == "admin":
        panel_admin()
    else:
        st.title(f"Punto de Venta")
        render_pos_interface(st.session_state.username)
