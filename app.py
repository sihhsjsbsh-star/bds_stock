import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
import time
import unicodedata

# ========== CONFIGURACIÓN DEL LOCAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"
TELEFONO_LOCAL = "+595 982 627824"
DIRECCION_LOCAL = "Avenida 1ro. de Mayo &, Carlos Antonio López, Capiatá"
# =============================================

# ========== CONFIGURACIÓN DE USUARIOS ==========
USUARIOS = {
    "Rosana": {
        "password": "bdse1975",
        "rol": "admin",
        "nombre_completo": "Rosana Da Silva"
    },
    "vendedor": {
        "password": "ventas123",
        "rol": "vendedor",
        "nombre_completo": "vendedor"
    }
}
# ================================================

# Configuración de la página
st.set_page_config(
    page_title=f"{NOMBRE_LOCAL} - Gestión",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== UTILIDADES ==========
def formato_guaranies(valor):
    """Formatea números al estilo paraguayo: 1.000.000 (puntos para miles, sin decimales)"""
    try:
        valor_int = int(float(valor))
        return f"{valor_int:,}".replace(",", ".")
    except:
        return "0"

def normalizar_texto(texto):
    """Elimina tildes y convierte a minúsculas para comparaciones"""
    if not isinstance(texto, str):
        return str(texto).lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def fuzzy_match(query, text, threshold=0.6):
    """Fuzzy matching mejorado con normalización de caracteres (tildes/ñ)"""
    if not query or not text:
        return False
    
    query_norm = normalizar_texto(query)
    text_norm = normalizar_texto(text)
    
    if query_norm in text_norm:
        return True
    
    query_words = query_norm.split()
    text_words = text_norm.split()
    
    for q_word in query_words:
        for t_word in text_words:
            ratio = SequenceMatcher(None, q_word, t_word).ratio()
            if ratio >= threshold:
                return True
    
    return False

def busqueda_inteligente(df, query, categoria=None, marca=None):
    """Búsqueda inteligente con fuzzy matching y filtros combinados"""
    df_resultado = df.copy()
    
    if categoria and categoria != 'Todas las categorías':
        df_resultado = df_resultado[df_resultado['CATEGORIA'] == categoria]
    
    if marca and marca != 'Todas las marcas':
        df_resultado = df_resultado[df_resultado['MARCA'] == marca]
    
    if query:
        mascara = df_resultado.apply(
            lambda row: fuzzy_match(query, str(row['PRODUCTO'])) or 
                        fuzzy_match(query, str(row['MARCA'])),
            axis=1
        )
        df_resultado = df_resultado[mascara]
    
    return df_resultado
# ================================

# Estilos CSS
st.markdown("""
<style>
    :root {
        --primary: #FF9900;
        --secondary: #146EB4;
        --success: #067D62;
        --danger: #C7511F;
        --text-dark: #0F1111;
        --text-light: #565959;
        --bg-card: #FFFFFF;
        --border: #D5D9D9;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
    }
    .main .block-container { padding: 1rem; max-width: 100%; }
    .search-wrapper { position: relative; margin-bottom: 1.5rem; }
    .search-icon { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); font-size: 20px; color: var(--text-light); pointer-events: none; z-index: 10; }
    .stTextInput > div > div > input { padding-left: 48px !important; padding-right: 16px !important; height: 52px !important; font-size: 15px !important; border-radius: 8px !important; border: 2px solid var(--border) !important; box-shadow: var(--shadow-sm) !important; transition: all 0.2s ease !important; }
    .stTextInput > div > div > input:focus { border-color: var(--secondary) !important; box-shadow: 0 0 0 4px rgba(20, 110, 180, 0.1), var(--shadow-md) !important; outline: none !important; }
    .filtros-row { display: flex; gap: 12px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .stSelectbox { flex: 1; min-width: 140px; }
    .stSelectbox > div > div > div { border-radius: 8px !important; border: 2px solid var(--border) !important; font-size: 14px !important; }
    .producto-card { background: var(--bg-card); border: 2px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: var(--shadow-sm); transition: all 0.2s ease; }
    .producto-card:hover { box-shadow: var(--shadow-md); border-color: var(--secondary); transform: translateY(-2px); }
    .card-header { margin-bottom: 12px; }
    .producto-nombre { font-size: 16px; font-weight: 700; color: var(--text-dark); line-height: 1.4; margin-bottom: 4px; }
    .producto-marca { font-size: 12px; color: var(--secondary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .precio-principal { background: linear-gradient(135deg, #B12704 0%, #C7511F 100%); color: white; padding: 16px; border-radius: 8px; margin: 12px 0; text-align: center; }
    .precio-label { font-size: 11px; opacity: 0.9; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px; }
    .precio-valor { font-size: 32px; font-weight: 800; letter-spacing: -1px; }
    .precio-simbolo { font-size: 18px; font-weight: 600; margin-right: 4px; }
    .precios-secundarios { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; }
    .precio-cuota-box { background: #F7F8F8; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid var(--border); }
    .precio-cuota-label { font-size: 10px; color: var(--text-light); margin-bottom: 4px; text-transform: uppercase; }
    .precio-cuota-valor { font-size: 14px; font-weight: 700; color: var(--text-dark); }
    .stock-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; margin: 8px 0; }
    .stock-alto { background: #D5F4E6; color: var(--success); }
    .stock-medio { background: #FFF3CD; color: #856404; }
    .stock-bajo { background: #F8D7DA; color: var(--danger); animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .categoria-badge { display: inline-block; background: #E7F3FF; color: var(--secondary); padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .stButton > button { width: 100%; height: 56px; border-radius: 8px; font-weight: 700; font-size: 15px; border: none; transition: all 0.2s ease; text-transform: uppercase; letter-spacing: 1px; margin-top: 12px; }
    .stButton > button[kind="primary"] { background: linear-gradient(180deg, #FFD814 0%, #F7CA00 100%); color: var(--text-dark); box-shadow: 0 4px 12px rgba(255, 153, 0, 0.3); }
    .stButton > button[kind="primary"]:hover { background: linear-gradient(180deg, #F7CA00 0%, #FFD814 100%); transform: translateY(-2px); box-shadow: 0 6px 16px rgba(255, 153, 0, 0.4); }
    .resultados-info { background: var(--secondary); color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; font-weight: 700; font-size: 13px; margin-bottom: 16px; }
    .empty-state { text-align: center; padding: 80px 20px; color: var(--text-light); }
    .empty-icon { font-size: 80px; margin-bottom: 20px; opacity: 0.4; }
    .empty-state h3 { color: var(--text-dark); font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    .empty-state p { font-size: 15px; }
    .stNumberInput input, .stSelectbox select { font-size: 15px !important; padding: 12px !important; border-radius: 6px !important; border: 2px solid var(--border) !important; }
    .streamlit-expanderHeader { background: #F7F8F8 !important; border-radius: 8px !important; border: 2px solid var(--border) !important; font-weight: 700 !important; padding: 16px !important; }
    @media (max-width: 768px) { .main .block-container { padding: 0.75rem; } .producto-card { padding: 14px; } .precio-principal { padding: 14px; } .precio-valor { font-size: 28px; } .stButton > button { height: 52px; font-size: 14px; } h1 { font-size: 24px !important; } .empty-state { padding: 60px 16px; } .empty-icon { font-size: 64px; } .filtros-row { flex-direction: column; } .stSelectbox { width: 100%; } }
    @media (min-width: 769px) and (max-width: 1024px) { .producto-card { padding: 16px; } .precio-valor { font-size: 30px; } }
    html { scroll-behavior: smooth; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== CONEXIÓN Y DATOS ==========
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    df = conn.read(worksheet="PRODUCTOS")
    df = df.dropna(how='all')
    return df

@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try:
        df = conn.read(worksheet="VENTAS")
        df = df.dropna(how='all')
        return df
    except:
        return pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])

def guardar_productos(df):
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()

def registrar_venta(vendedor, producto, cantidad, tipo_pago, monto_total):
    conn = get_connection()
    df_ventas = leer_ventas()
    
    nueva_venta = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': vendedor,
        'PRODUCTO': producto,
        'CANTIDAD': cantidad,
        'TIPO_PAGO': tipo_pago,
        'MONTO_TOTAL': monto_total
    }])
    
    df_ventas = pd.concat([df_ventas, nueva_venta], ignore_index=True)
    conn.update(worksheet="VENTAS", data=df_ventas)
    st.cache_data.clear()

def actualizar_stock(df_productos, producto_nombre, cantidad_vendida):
    mask = df_productos['PRODUCTO'] == producto_nombre
    df_productos.loc[mask, 'STOCK'] = df_productos.loc[mask, 'STOCK'] - cantidad_vendida
    guardar_productos(df_productos)

# ========== TARJETA DE PRODUCTO REFACTORIZADA (VENDEDOR) ==========
def renderizar_tarjeta_producto(producto, index):
    nombre = producto['PRODUCTO']
    marca = producto['MARCA']
    categoria = producto['CATEGORIA']
    precio_contado = float(producto['CONTADO'])
    precio_6 = float(producto['6 CUOTAS'])
    precio_12 = float(producto['12 CUOTAS'])
    stock = int(producto['STOCK'])
    
    if stock >= 10:
        stock_class = "stock-alto"
        stock_icon = "✅"
        stock_text = "Disponible"
    elif stock >= 5:
        stock_class = "stock-medio"
        stock_icon = "⚠️"
        stock_text = f"Quedan {stock}"
    elif stock > 0:
        stock_class = "stock-bajo"
        stock_icon = "🔴"
        stock_text = f"¡Solo {stock}!"
    else:
        stock_class = "stock-bajo"
        stock_icon = "❌"
        stock_text = "Agotado"
    
    st.markdown(f"""
    <div class="producto-card">
        <div class="card-header">
            <div class="producto-nombre">{nombre}</div>
            <div class="producto-marca">{marca}</div>
        </div>
        <div class="precio-principal">
            <div class="precio-label">💳 Precio Contado</div>
            <div class="precio-valor"><span class="precio-simbolo">₲</span>{formato_guaranies(precio_contado)}</div>
        </div>
        <div class="precios-secundarios">
            <div class="precio-cuota-box"><div class="precio-cuota-label">6 Cuotas</div><div class="precio-cuota-valor">₲ {formato_guaranies(precio_6)}</div></div>
            <div class="precio-cuota-box"><div class="precio-cuota-label">12 Cuotas</div><div class="precio-cuota-valor">₲ {formato_guaranies(precio_12)}</div></div>
        </div>
        <div><span class="stock-badge {stock_class}">{stock_icon} {stock_text}</span> <span class="categoria-badge">📂 {categoria}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if stock > 0:
        if st.button("🛒 VENDER AHORA", key=f"vender_{index}", use_container_width=True, type="primary"):
            st.session_state[f'venta_{index}'] = True
            st.rerun()
        
        if st.session_state.get(f'venta_{index}', False):
            with st.expander("📝 Completar Venta", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    cantidad = st.number_input("Cantidad", min_value=1, max_value=stock, value=1, key=f"cant_{index}")
                with col2:
                    tipo_pago = st.selectbox("Forma de Pago", ["Contado", "6 CUOTAS", "12 CUOTAS"], key=f"pago_{index}")
                
                if tipo_pago == "Contado": precio_unit = precio_contado
                elif tipo_pago == "6 CUOTAS": precio_unit = precio_6
                else: precio_unit = precio_12
                total = precio_unit * cantidad
                
                st.markdown("---")
                st.markdown(f"**Producto:** {nombre}")
                st.markdown(f"**Precio Unitario:** ₲ {formato_guaranies(precio_unit)}")
                st.markdown(f"**Cantidad:** {cantidad}")
                st.markdown(f"### 💰 TOTAL: ₲ {formato_guaranies(total)}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Confirmar", key=f"conf_{index}", use_container_width=True):
                        try:
                            df_productos = leer_productos()
                            actualizar_stock(df_productos, nombre, cantidad)
                            registrar_venta(st.session_state.username, nombre, cantidad, tipo_pago, total)
                            st.success("🎉 ¡Venta registrada!")
                            st.session_state[f'venta_{index}'] = False
                            time.sleep(1.2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                with col_b:
                    if st.button("❌ Cancelar", key=f"canc_{index}", use_container_width=True):
                        st.session_state[f'venta_{index}'] = False
                        st.rerun()
    else:
        st.error("⛔ Sin stock disponible")

# ========== LOGIN ==========
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title(f"🏪 {NOMBRE_LOCAL}")
        st.markdown("### Sistema de Gestión")
        st.markdown("---")
        usuario = st.text_input("👤 Usuario", placeholder="Tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Tu contraseña")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔐 Ingresar", use_container_width=True, type="primary"):
            if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USUARIOS[usuario]["rol"]
                st.session_state.username = USUARIOS[usuario]["nombre_completo"]
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
        st.markdown("---")
        st.caption("🔒 Sistema conectado a Google Sheets")

# ========== PANEL VENDEDOR ==========
def panel_vendedor():
    st.title("🛒 Punto de Venta")
    st.markdown(f"**{st.session_state.username}** 👋")
    st.markdown("---")
    
    try:
        df_productos = leer_productos()
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
        return
    
    st.markdown('<div class="search-wrapper"><div class="search-icon">🔍</div></div>', unsafe_allow_html=True)
    busqueda = st.text_input("Buscar", placeholder="Busca por nombre o marca...", key="search", label_visibility="collapsed")
    
    col1, col2 = st.columns(2)
    with col1:
        categorias = ['Todas las categorías'] + sorted(df_productos['CATEGORIA'].unique().tolist())
        categoria = st.selectbox("📂 Categoría", categorias, key="cat")
    with col2:
        marcas = ['Todas las marcas'] + sorted(df_productos['MARCA'].unique().tolist())
        marca = st.selectbox("🏷️ Marca", marcas, key="marca")
    
    st.markdown("---")
    df_resultado = busqueda_inteligente(df_productos, busqueda, categoria, marca)
    
    hay_filtros = busqueda or categoria != 'Todas las categorías' or marca != 'Todas las marcas'
    if hay_filtros:
        if len(df_resultado) > 0:
            st.markdown(f'<div class="resultados-info">✅ {len(df_resultado)} productos encontrados</div>', unsafe_allow_html=True)
            for index, row in df_resultado.iterrows():
                renderizar_tarjeta_producto(row, index)
        else:
            st.markdown('<div class="empty-state"><div class="empty-icon">🔍</div><h3>Sin resultados</h3></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">🛍️</div><h3>¡Listo para vender!</h3></div>', unsafe_allow_html=True)
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("📦 Productos", len(df_productos))
        with col2: st.metric("📂 Categorías", len(df_productos['CATEGORIA'].unique()))
        with col3: st.metric("🏷️ Marcas", len(df_productos['MARCA'].unique()))
        with col4: 
            disponibles = len(df_productos[df_productos['STOCK'] > 0])
            st.metric("✅ Disponibles", disponibles)

# ========== PANEL ADMIN (CORREGIDO CON BUSCADOR Y MERGE SEGURO) ==========
def panel_administrador():
    st.title("⚙️ Administración")
    st.markdown(f"**{st.session_state.username}**")
    
    tab1, tab2 = st.tabs(["📦 Productos", "📊 Ventas"])
    
    with tab1:
        st.subheader("Gestión de Productos")
        
        try:
            # 1. Cargar Base de Datos Original
            df_full_original = leer_productos()
            
            # 2. BUSCADOR EN ADMIN (NUEVO)
            col_search_1, col_search_2 = st.columns([3, 1])
            with col_search_1:
                busqueda_admin = st.text_input("🔍 Buscar Producto para Editar", placeholder="Escribe para filtrar...")
            with col_search_2:
                vista_movil = st.toggle("📱 Vista Tarjetas", value=True)
            
            # 3. Filtrar para la VISTA
            if busqueda_admin:
                df_view = busqueda_inteligente(df_full_original, busqueda_admin)
            else:
                df_view = df_full_original.copy()
            
            if not vista_movil:
                # --- VISTA ESCRITORIO ---
                st.info("💡 Edita en la tabla y presiona 'Guardar Cambios' al final")
                columnas = ['PRODUCTO', 'MARCA', 'CONTADO', '6 CUOTAS', '12 CUOTAS', 'STOCK', 'CATEGORIA']
                
                df_editado_view = st.data_editor(
                    df_view[columnas],
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_desktop"
                )
            else:
                # --- VISTA MÓVIL ---
                st.info("💡 Toca 'Editar' para modificar")
                
                # Inicializar sesión móvil solo si cambia la búsqueda o no existe
                # (Clave compuesta para resetear si cambia la busqueda)
                key_mobile = f"df_mobile_{busqueda_admin}"
                if 'current_mobile_key' not in st.session_state or st.session_state.current_mobile_key != key_mobile:
                    st.session_state.df_editado_mobile = df_view.copy()
                    st.session_state.current_mobile_key = key_mobile
                
                df_render = st.session_state.df_editado_mobile
                
                if df_render.empty:
                    st.warning("No hay productos que coincidan con la búsqueda.")
                
                for idx, row in df_render.iterrows():
                    with st.container(border=True):
                        col_nombre, col_stock = st.columns([3, 1])
                        with col_nombre:
                            st.markdown(f"### {row['PRODUCTO']}")
                            st.caption(f"🏷️ {row['MARCA']} | 📂 {row['CATEGORIA']}")
                        with col_stock:
                            stock_val = int(row['STOCK'])
                            st.markdown(f"<div style='text-align: right; font-size: 24px; font-weight: bold;'>{'🔴' if stock_val<3 else '🟢'} {stock_val}</div>", unsafe_allow_html=True)
                        
                        st.divider()
                        col1, col2, col3 = st.columns(3)
                        with col1: st.markdown(f"**💳 Contado**\n₲ {formato_guaranies(row['CONTADO'])}")
                        with col2: st.markdown(f"**📅 6 C.**\n₲ {formato_guaranies(row['6 CUOTAS'])}")
                        with col3: st.markdown(f"**📅 12 C.**\n₲ {formato_guaranies(row['12 CUOTAS'])}")
                        
                        if st.button("✏️ Editar", key=f"edit_{idx}", use_container_width=True):
                            st.session_state[f'editing_{idx}'] = True
                            st.rerun()
                        
                        if st.session_state.get(f'editing_{idx}', False):
                            with st.expander("📝 Editar", expanded=True):
                                new_name = st.text_input("Producto", value=row['PRODUCTO'], key=f"n_{idx}")
                                new_brand = st.text_input("Marca", value=row['MARCA'], key=f"m_{idx}")
                                new_cat = st.text_input("Cat", value=row['CATEGORIA'], key=f"c_{idx}")
                                c1, c2, c3 = st.columns(3)
                                with c1: n_cont = st.number_input("Contado", value=int(row['CONTADO']), key=f"p1_{idx}")
                                with c2: n_6 = st.number_input("6 Cuotas", value=int(row['6 CUOTAS']), key=f"p2_{idx}")
                                with c3: n_12 = st.number_input("12 Cuotas", value=int(row['12 CUOTAS']), key=f"p3_{idx}")
                                n_stock = st.number_input("Stock", value=int(row['STOCK']), key=f"s_{idx}")
                                
                                cx, cy = st.columns(2)
                                with cx:
                                    if st.button("💾 Aplicar", key=f"save_btn_{idx}", use_container_width=True):
                                        st.session_state.df_editado_mobile.at[idx, 'PRODUCTO'] = new_name
                                        st.session_state.df_editado_mobile.at[idx, 'MARCA'] = new_brand
                                        st.session_state.df_editado_mobile.at[idx, 'CATEGORIA'] = new_cat
                                        st.session_state.df_editado_mobile.at[idx, 'CONTADO'] = n_cont
                                        st.session_state.df_editado_mobile.at[idx, '6 CUOTAS'] = n_6
                                        st.session_state.df_editado_mobile.at[idx, '12 CUOTAS'] = n_12
                                        st.session_state.df_editado_mobile.at[idx, 'STOCK'] = n_stock
                                        st.session_state[f'editing_{idx}'] = False
                                        st.success("✅ Cambios en memoria. GUARDA ABAJO.")
                                        time.sleep(1)
                                        st.rerun()
                                with cy:
                                    if st.button("❌", key=f"cls_{idx}", use_container_width=True):
                                        st.session_state[f'editing_{idx}'] = False
                                        st.rerun()

            # --- BOTÓN DE GUARDADO INTELIGENTE (MERGE) ---
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Guardar Cambios en BD", use_container_width=True, type="primary"):
                    try:
                        # 1. Recuperamos la BD completa fresca
                        df_db_fresh = leer_productos()
                        
                        # 2. Identificamos qué datos modificados tenemos
                        if vista_movil:
                            if 'df_editado_mobile' in st.session_state:
                                df_changes = st.session_state.df_editado_mobile
                            else:
                                df_changes = df_view # No hubo cambios
                        else:
                            df_changes = df_editado_view
                        
                        # 3. MERGE / UPDATE: Actualizamos la BD completa con los cambios
                        # Usamos el índice original para mapear los cambios
                        df_db_fresh.update(df_changes)
                        
                        # 4. Guardamos la BD completa (no solo la vista filtrada)
                        guardar_productos(df_db_fresh)
                        
                        # Limpieza
                        if 'df_editado_mobile' in st.session_state:
                            del st.session_state.df_editado_mobile
                        
                        st.success("✅ ¡Base de datos actualizada correctamente!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {str(e)}")
            
            with col2:
                if st.button("🔄 Recargar", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

            # Stats (basadas en datos completos)
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total", len(df_full_original))
            with col2: 
                val = (df_full_original['CONTADO'] * df_full_original['STOCK']).sum()
                st.metric("Valor", f"₲ {formato_guaranies(val)}")
            with col3: st.metric("Bajo Stock", len(df_full_original[df_full_original['STOCK'] < 5]))
            with col4: st.metric("Agotados", len(df_full_original[df_full_original['STOCK'] == 0]))

        except Exception as e:
            st.error(f"❌ Error en Admin: {str(e)}")
            
    with tab2:
        st.subheader("Historial")
        try:
            df_ventas = leer_ventas()
            st.dataframe(df_ventas, use_container_width=True, hide_index=True)
        except: st.error("Error cargando ventas")

# ========== MAIN ==========
def main():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.username}")
            if st.button("🚪 Salir", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
        
        if st.session_state.user_role == "admin":
            panel_administrador()
        else:
            panel_vendedor()

if __name__ == "__main__":
    main()
