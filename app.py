import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
import time
import unicodedata

# ========== CONFIGURACIÓN GLOBAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"
LOGO_PATH = "bds_image.jpg" # Tu archivo exacto
# ==========================================

# Configuración de página (Debe ser lo primero)
st.set_page_config(
    page_title=NOMBRE_LOCAL,
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed" if 'logged_in' not in st.session_state or not st.session_state.logged_in else "expanded"
)

# ========== ESTILOS CSS "PREMIUM" ==========
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* COLORES PRINCIPALES */
    :root {
        --primary: #D32F2F; /* Rojo BDS */
        --primary-dark: #B71C1C;
        --bg-gray: #F8F9FA;
        --card-bg: #FFFFFF;
        --text-main: #1F2937;
    }

    /* FONDO GENERAL */
    .stApp {
        background-color: var(--bg-gray);
    }

    /* TARJETA DE LOGIN */
    .login-card {
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 5px solid var(--primary);
    }

    /* BOTONES ROJOS */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none;
        border-radius: 10px;
        height: 50px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: var(--primary-dark) !important;
        box-shadow: 0 5px 15px rgba(211, 47, 47, 0.4);
        transform: translateY(-2px);
    }

    /* TARJETAS DE PRODUCTOS (VENDEDOR/MOVIL) */
    .product-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .product-card:hover {
        border-color: var(--primary);
        transform: translateY(-3px);
    }
    
    .card-title {
        font-size: 18px;
        font-weight: 800;
        color: var(--text-main);
        margin-bottom: 4px;
        line-height: 1.3;
    }
    
    .card-meta {
        font-size: 12px;
        color: #6B7280;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 12px;
    }

    /* PRECIOS */
    .price-main {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
    }
    .price-main .label { font-size: 10px; opacity: 0.8; text-transform: uppercase; }
    .price-main .value { font-size: 24px; font-weight: 900; }

    .price-sec {
        background: #F3F4F6;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
    }
    .price-sec .label { font-size: 9px; color: #666; font-weight: 700; }
    .price-sec .value { font-size: 14px; color: #333; font-weight: 700; }

    /* STOCK BADGES */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
    }
    .badge-ok { background: #DCFCE7; color: #166534; }
    .badge-low { background: #FEE2E2; color: #991B1B; }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #E5E7EB;
    }
    [data-testid="stSidebar"] img {
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ========== LÓGICA DE NEGOCIO (SIN CAMBIOS, SOLO ROBUSTEZ) ==========
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def formato_guaranies(valor):
    try: return f"{int(float(valor)):,}".replace(",", ".")
    except: return "0"

@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    try: return conn.read(worksheet="PRODUCTOS").dropna(how='all')
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try: return conn.read(worksheet="VENTAS").dropna(how='all')
    except: return pd.DataFrame(columns=['FECHA','VENDEDOR','PRODUCTO','CANTIDAD','TIPO_PAGO','MONTO_TOTAL'])

def guardar_productos(df):
    cols_check = ['CONTADO', 'STOCK']
    for c in cols_check:
        if c in df.columns and (df[c] < 0).any():
            st.error(f"❌ Error: Valores negativos en {c}"); return False
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
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

def actualizar_stock_venta(nombre, cantidad):
    df = leer_productos()
    mask = df['PRODUCTO'] == nombre
    if not mask.any(): return False
    idx = df[mask].index[0]
    stock = int(df.at[idx, 'STOCK'])
    if stock < cantidad: return False
    df.at[idx, 'STOCK'] = stock - cantidad
    return guardar_productos(df)

# ========== COMPONENTES VISUALES ==========

def card_visual(row, idx, es_admin=False):
    # Datos
    nom = row['PRODUCTO']
    marca = row['MARCA']
    cat = row['CATEGORIA']
    stk = int(row['STOCK'])
    p1 = float(row['CONTADO'])
    p6 = float(row['6 CUOTAS'])
    p12 = float(row['12 CUOTAS'])
    
    st.markdown(f"""
    <div class="product-card">
        <div class="card-title">{nom}</div>
        <div class="card-meta">{marca} | {cat}</div>
        <div style="margin-bottom:10px;">
            <span class="badge {'badge-ok' if stk > 2 else 'badge-low'}">STOCK: {stk}</span>
        </div>
        <div class="price-main">
            <div class="label">PRECIO CONTADO</div>
            <div class="value">₲ {formato_guaranies(p1)}</div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="price-sec">
                <div class="label">6 CUOTAS</div>
                <div class="value">₲ {formato_guaranies(p6)}</div>
            </div>
            <div class="price-sec">
                <div class="label">12 CUOTAS</div>
                <div class="value">₲ {formato_guaranies(p12)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botonera
    if not es_admin:
        if stk > 0:
            if st.button("🛒 VENDER", key=f"v_{idx}"):
                st.session_state[f'mod_v_{idx}'] = True
                st.rerun()
            
            if st.session_state.get(f'mod_v_{idx}'):
                with st.container(border=True):
                    st.info("Confirmar Venta")
                    cant = st.number_input("Cant.", 1, stk, 1, key=f"qn_{idx}")
                    pago = st.selectbox("Pago", ["Contado", "6 Cuotas", "12 Cuotas"], key=f"pg_{idx}")
                    total = (p1 if pago=="Contado" else (p6 if pago=="6 Cuotas" else p12)) * cant
                    st.write(f"**Total: ₲ {formato_guaranies(total)}**")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ OK", key=f"ok_{idx}"):
                        if actualizar_stock_venta(nom, cant):
                            registrar_venta(st.session_state.username, nom, cant, pago, total)
                            st.success("Listo!")
                            st.session_state[f'mod_v_{idx}'] = False
                            time.sleep(1); st.rerun()
                    if c2.button("❌", key=f"no_{idx}"):
                        st.session_state[f'mod_v_{idx}'] = False; st.rerun()
        else:
            st.error("AGOTADO")
    else:
        # Admin Edit
        if st.button("✏️ EDITAR", key=f"e_{idx}"):
            st.session_state[f'mod_e_{idx}'] = True; st.rerun()
            
        if st.session_state.get(f'mod_e_{idx}'):
            with st.container(border=True):
                st.warning("Editar Producto")
                with st.form(key=f"fe_{idx}"):
                    # Campos completos para no perder datos
                    nn = st.text_input("Nombre", nom)
                    ns = st.number_input("Stock", value=stk)
                    np1 = st.number_input("Contado", value=int(p1))
                    if st.form_submit_button("💾 GUARDAR"):
                        if 'mob_q' not in st.session_state: st.session_state.mob_q = {}
                        # Guardar fila completa actualizada
                        new_row = row.to_dict()
                        new_row.update({'PRODUCTO':nn, 'STOCK':ns, 'CONTADO':np1})
                        st.session_state.mob_q[idx] = new_row
                        st.session_state[f'mod_e_{idx}'] = False
                        st.success("Guardado en cola. Dale a 'GUARDAR CAMBIOS' arriba.")
                        st.rerun()

# ========== PÁGINAS ==========

def login_page():
    # Diseño centrado y elegante
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # INICIO TARJETA
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        try: st.image(LOGO_PATH, width=150) 
        except: st.title("🔴 BDS")
        
        st.markdown("### Bienvenido al Sistema")
        st.markdown("<div style='color:#666; margin-bottom:20px;'>Ingresa tus credenciales para continuar</div>", unsafe_allow_html=True)
        
        u = st.text_input("Usuario", placeholder="Ej: Rosana")
        p = st.text_input("Contraseña", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
            creds = {"Rosana":"bdse1975", "vendedor":"ventas123"}
            if u in creds and creds[u] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = "admin" if u == "Rosana" else "vendedor"
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        
        st.markdown('</div>', unsafe_allow_html=True) # FIN TARJETA

def panel_vendedor():
    st.title(f"👋 Hola, {st.session_state.username}")
    q = st.text_input("🔍 ¿Qué desea buscar el cliente?", placeholder="Escribe 'Split', 'Tokyo', etc.")
    
    df = leer_productos()
    
    # Búsqueda simple
    if q:
        q = q.lower()
        # Filtramos por texto
        df = df[df.apply(lambda r: q in str(r['PRODUCTO']).lower() or q in str(r['MARCA']).lower(), axis=1)]
    
    st.write(f"Encontramos {len(df)} productos")
    
    for idx, row in df.iterrows():
        card_visual(row, idx, es_admin=False)

def panel_admin():
    st.title("⚙️ Panel de Control")
    
    # Botonera móvil
    if 'mob_q' in st.session_state and st.session_state.mob_q:
        st.info(f"Tienes {len(st.session_state.mob_q)} cambios pendientes de guardar.")
        if st.button("💾 GUARDAR TODO EN BD", type="primary"):
            df = leer_productos()
            for i, data in st.session_state.mob_q.items():
                if i in df.index:
                    for k,v in data.items(): df.at[i,k]=v
            guardar_productos(df)
            st.session_state.mob_q = {}
            st.success("¡Base de datos actualizada!"); time.sleep(1); st.rerun()

    tab1, tab2 = st.tabs(["INVENTARIO", "VENTAS"])
    
    with tab1:
        c1, c2 = st.columns([3,1])
        q = c1.text_input("Buscar en inventario...")
        vista_movil = c2.toggle("Vista Móvil", value=True)
        
        df = leer_productos()
        if q:
            q = q.lower()
            df = df[df.apply(lambda r: q in str(r['PRODUCTO']).lower(), axis=1)]
            
        if not vista_movil:
            # TABLA PC
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500)
            if st.button("💾 GUARDAR TABLA"):
                # Truco para guardar respetando indices
                df_master = leer_productos()
                df_master.loc[edited.index] = edited
                guardar_productos(df_master)
                st.success("Guardado")
        else:
            # VISTA MOVIL
            for idx, row in df.iterrows():
                card_visual(row, idx, es_admin=True)
                
    with tab2:
        st.dataframe(leer_ventas(), use_container_width=True)

# ========== MAIN ==========
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    with st.sidebar:
        try: st.image(LOGO_PATH, use_container_width=True)
        except: st.title("BDS")
        
        st.write(f"👤 **{st.session_state.username}**")
        st.write(f"🔑 {st.session_state.user_role.upper()}")
        st.divider()
        if st.button("CERRAR SESIÓN"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state.user_role == "admin":
        panel_admin()
    else:
        panel_vendedor()
