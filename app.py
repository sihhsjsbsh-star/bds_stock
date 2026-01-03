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

    div[data-testid="stMetric"] {
        background-color: white; padding: 15px; border-radius: 10px;
        border: 1px solid #E5E7EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
    }

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
        df = df.dropna(subset=['PRODUCTO'])
        df = df[df['PRODUCTO'].str.strip() != ''] 
        
        # Limpieza de categorías para el filtro
        if 'CATEGORIA' in df.columns:
            df['CATEGORIA'] = df['CATEGORIA'].astype(str).str.strip().str.upper()
        else:
            df['CATEGORIA'] = "GENERAL"

        cols_num = ['STOCK', 'CONTADO', '6 CUOTAS', '12 CUOTAS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # ID BLINDADO
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

# ========== VENTANA EMERGENTE (POP-UP) ==========

@st.dialog("🎫 PROCESAR VENTA")
def popup_venta(item, usuario):
    st.markdown(f"### {item['PRODUCTO']}")
    st.markdown(f"<small>{item['MARCA']} | {item['CATEGORIA']}</small>", unsafe_allow_html=True)
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
    
    st.markdown("<br>", unsafe_allow_html=
