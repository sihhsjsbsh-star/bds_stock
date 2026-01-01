import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher

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

def fuzzy_match(query, text, threshold=0.6):
    """Implementa fuzzy matching usando SequenceMatcher nativo de Python"""
    if not query or not text:
        return False
    
    query = query.lower().strip()
    text = text.lower().strip()
    
    # Coincidencia exacta
    if query in text:
        return True
    
    # Fuzzy matching por palabras
    query_words = query.split()
    text_words = text.split()
    
    for q_word in query_words:
        for t_word in text_words:
            ratio = SequenceMatcher(None, q_word, t_word).ratio()
            if ratio >= threshold:
                return True
    
    return False

def busqueda_inteligente(df, query, categoria=None, marca=None):
    """Búsqueda inteligente con fuzzy matching y filtros combinados"""
    df_resultado = df.copy()
    
    # Aplicar filtro de categoría
    if categoria and categoria != 'Todas las categorías':
        df_resultado = df_resultado[df_resultado['CATEGORIA'] == categoria]
    
    # Aplicar filtro de marca
    if marca and marca != 'Todas las marcas':
        df_resultado = df_resultado[df_resultado['MARCA'] == marca]
    
    # Búsqueda fuzzy por texto
    if query:
        mascara = df_resultado.apply(
            lambda row: fuzzy_match(query, str(row['PRODUCTO'])) or 
                       fuzzy_match(query, str(row['MARCA'])),
            axis=1
        )
        df_resultado = df_resultado[mascara]
    
    return df_resultado
# ================================

# Estilos CSS - REFACTORIZADOS MOBILE FIRST
st.markdown("""
<style>
    /* ========== VARIABLES DE COLOR ========== */
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
    
    /* ========== LAYOUT BASE ========== */
    .main .block-container {
        padding: 1rem;
        max-width: 100%;
    }
    
    /* ========== BÚSQUEDA PREMIUM ========== */
    .search-wrapper {
        position: relative;
        margin-bottom: 1.5rem;
    }
    
    .search-icon {
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 20px;
        color: var(--text-light);
        pointer-events: none;
        z-index: 10;
    }
    
    .stTextInput > div > div > input {
        padding-left: 48px !important;
        padding-right: 16px !important;
        height: 52px !important;
        font-size: 15px !important;
        border-radius: 8px !important;
        border: 2px solid var(--border) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--secondary) !important;
        box-shadow: 0 0 0 4px rgba(20, 110, 180, 0.1), var(--shadow-md) !important;
        outline: none !important;
    }
    
    /* ========== FILTROS COMPACTOS ========== */
    .filtros-row {
        display: flex;
        gap: 12px;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    
    .stSelectbox {
        flex: 1;
        min-width: 140px;
    }
    
    .stSelectbox > div > div > div {
        border-radius: 8px !important;
        border: 2px solid var(--border) !important;
        font-size: 14px !important;
    }
    
    /* ========== TARJETAS MOBILE FIRST ========== */
    .producto-card {
        background: var(--bg-card);
        border: 2px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .producto-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--secondary);
        transform: translateY(-2px);
    }
    
    /* Mobile First: Información clave primero */
    .card-header {
        margin-bottom: 12px;
    }
    
    .producto-nombre {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-dark);
        line-height: 1.4;
        margin-bottom: 4px;
    }
    
    .producto-marca {
        font-size: 12px;
        color: var(--secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Precio PRIMERO en móvil - MÁS GRANDE */
    .precio-principal {
        background: linear-gradient(135deg, #B12704 0%, #C7511F 100%);
        color: white;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
        text-align: center;
    }
    
    .precio-label {
        font-size: 11px;
        opacity: 0.9;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .precio-valor {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    .precio-simbolo {
        font-size: 18px;
        font-weight: 600;
        margin-right: 4px;
    }
    
    /* Precios secundarios compactos */
    .precios-secundarios {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin: 12px 0;
    }
    
    .precio-cuota-box {
        background: #F7F8F8;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        border: 1px solid var(--border);
    }
    
    .precio-cuota-label {
        font-size: 10px;
        color: var(--text-light);
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    
    .precio-cuota-valor {
        font-size: 14px;
        font-weight: 700;
        color: var(--text-dark);
    }
    
    /* Stock con colores */
    .stock-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin: 8px 0;
    }
    
    .stock-alto { background: #D5F4E6; color: var(--success); }
    .stock-medio { background: #FFF3CD; color: #856404; }
    .stock-bajo { 
        background: #F8D7DA; 
        color: var(--danger);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .categoria-badge {
        display: inline-block;
        background: #E7F3FF;
        color: var(--secondary);
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    /* Botón vender prominente */
    .stButton > button {
        width: 100%;
        height: 56px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 15px;
        border: none;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 12px;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #FFD814 0%, #F7CA00 100%);
        color: var(--text-dark);
        box-shadow: 0 4px 12px rgba(255, 153, 0, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #F7CA00 0%, #FFD814 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(255, 153, 0, 0.4);
    }
    
    /* Badge de resultados */
    .resultados-info {
        background: var(--secondary);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        display: inline-block;
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 16px;
    }
    
    /* Estado vacío elegante */
    .empty-state {
        text-align: center;
        padding: 80px 20px;
        color: var(--text-light);
    }
    
    .empty-icon {
        font-size: 80px;
        margin-bottom: 20px;
        opacity: 0.4;
    }
    
    .empty-state h3 {
        color: var(--text-dark);
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .empty-state p {
        font-size: 15px;
    }
    
    /* Inputs mejorados */
    .stNumberInput input, .stSelectbox select {
        font-size: 15px !important;
        padding: 12px !important;
        border-radius: 6px !important;
        border: 2px solid var(--border) !important;
    }
    
    /* Expander mejorado */
    .streamlit-expanderHeader {
        background: #F7F8F8 !important;
        border-radius: 8px !important;
        border: 2px solid var(--border) !important;
        font-weight: 700 !important;
        padding: 16px !important;
    }
    
    /* ========== RESPONSIVE MOBILE ========== */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.75rem;
        }
        
        .producto-card {
            padding: 14px;
        }
        
        .precio-principal {
            padding: 14px;
        }
        
        .precio-valor {
            font-size: 28px;
        }
        
        .stButton > button {
            height: 52px;
            font-size: 14px;
        }
        
        h1 {
            font-size: 24px !important;
        }
        
        .empty-state {
            padding: 60px 16px;
        }
        
        .empty-icon {
            font-size: 64px;
        }
        
        /* Filtros en columna en móvil */
        .filtros-row {
            flex-direction: column;
        }
        
        .stSelectbox {
            width: 100%;
        }
    }
    
    /* Tablets */
    @media (min-width: 769px) and (max-width: 1024px) {
        .producto-card {
            padding: 16px;
        }
        
        .precio-valor {
            font-size: 30px;
        }
    }
    
    /* Scroll suave */
    html {
        scroll-behavior: smooth;
    }
    
    /* Ocultar elementos innecesarios */
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

# ========== TARJETA DE PRODUCTO REFACTORIZADA ==========
def renderizar_tarjeta_producto(producto, index):
    """Tarjeta optimizada mobile-first con formato paraguayo"""
    
    nombre = producto['PRODUCTO']
    marca = producto['MARCA']
    categoria = producto['CATEGORIA']
    precio_contado = float(producto['CONTADO'])
    precio_6 = float(producto['6 CUOTAS'])
    precio_12 = float(producto['12 CUOTAS'])
    stock = int(producto['STOCK'])
    
    # Stock styling
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
    
    # HTML con FORMATO PARAGUAYO (puntos en miles)
    st.markdown(f"""
    <div class="producto-card">
        <div class="card-header">
            <div class="producto-nombre">{nombre}</div>
            <div class="producto-marca">{marca}</div>
        </div>
        
        <!-- PRECIO PRINCIPAL - PRIMERO Y MÁS GRANDE -->
        <div class="precio-principal">
            <div class="precio-label">💳 Precio Contado</div>
            <div class="precio-valor">
                <span class="precio-simbolo">₲</span>{formato_guaranies(precio_contado)}
            </div>
        </div>
        
        <!-- Precios secundarios -->
        <div class="precios-secundarios">
            <div class="precio-cuota-box">
                <div class="precio-cuota-label">6 Cuotas</div>
                <div class="precio-cuota-valor">₲ {formato_guaranies(precio_6)}</div>
            </div>
            <div class="precio-cuota-box">
                <div class="precio-cuota-label">12 Cuotas</div>
                <div class="precio-cuota-valor">₲ {formato_guaranies(precio_12)}</div>
            </div>
        </div>
        
        <!-- Stock y categoría -->
        <div>
            <span class="stock-badge {stock_class}">{stock_icon} {stock_text}</span>
            <span class="categoria-badge">📂 {categoria}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón vender
    if stock > 0:
        if st.button("🛒 VENDER AHORA", key=f"vender_{index}", use_container_width=True, type="primary"):
            st.session_state[f'venta_{index}'] = True
            st.rerun()
        
        # Formulario de venta
        if st.session_state.get(f'venta_{index}', False):
            with st.expander("📝 Completar Venta", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    cantidad = st.number_input(
                        "Cantidad",
                        min_value=1,
                        max_value=stock,
                        value=1,
                        key=f"cant_{index}"
                    )
                
                with col2:
                    tipo_pago = st.selectbox(
                        "Forma de Pago",
                        ["Contado", "6 CUOTAS", "12 CUOTAS"],
                        key=f"pago_{index}"
                    )
                
                # Calcular según tipo de pago
                if tipo_pago == "Contado":
                    precio_unit = precio_contado
                elif tipo_pago == "6 CUOTAS":
                    precio_unit = precio_6
                else:
                    precio_unit = precio_12
                
                total = precio_unit * cantidad
                
                # Resumen
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
                            registrar_venta(
                                st.session_state.username,
                                nombre,
                                cantidad,
                                tipo_pago,
                                total
                            )
                            st.success("🎉 ¡Venta registrada!")
                            st.session_state[f'venta_{index}'] = False
                            import time
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
    
    # BÚSQUEDA PREMIUM CON ICONO
    st.markdown('<div class="search-wrapper"><div class="search-icon">🔍</div></div>', unsafe_allow_html=True)
    busqueda = st.text_input(
        "Buscar",
        placeholder="Busca por nombre o marca (ej: 'Samung' encuentra 'Samsung')...",
        key="search",
        label_visibility="collapsed"
    )
    
    # FILTROS COMPACTOS
    col1, col2 = st.columns(2)
    with col1:
        categorias = ['Todas las categorías'] + sorted(df_productos['CATEGORIA'].unique().tolist())
        categoria = st.selectbox("📂 Categoría", categorias, key="cat")
    
    with col2:
        marcas = ['Todas las marcas'] + sorted(df_productos['MARCA'].unique().tolist())
        marca = st.selectbox("🏷️ Marca", marcas, key="marca")
    
    st.markdown("---")
    
    # BÚSQUEDA INTELIGENTE
    df_resultado = busqueda_inteligente(df_productos, busqueda, categoria, marca)
    
    # Verificar si hay filtros activos
    hay_filtros = busqueda or categoria != 'Todas las categorías' or marca != 'Todas las marcas'
    
    if hay_filtros:
        if len(df_resultado) > 0:
            st.markdown(
                f'<div class="resultados-info">✅ {len(df_resultado)} productos encontrados</div>',
                unsafe_allow_html=True
            )
            
            for index, row in df_resultado.iterrows():
                renderizar_tarjeta_producto(row, index)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>Sin resultados</h3>
                <p>Intenta con otros términos o ajusta los filtros</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🛍️</div>
            <h3>¡Listo para vender!</h3>
            <p>Usa el buscador inteligente o los filtros para encontrar productos</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Estadísticas
        st.markdown("---")
        st.markdown("### 📊 Resumen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Productos", len(df_productos))
        with col2:
            st.metric("📂 Categorías", len(df_productos['CATEGORIA'].unique()))
        with col3:
            st.metric("🏷️ Marcas", len(df_productos['MARCA'].unique()))
        with col4:
            disponibles = len(df_productos[df_productos['STOCK'] > 0])
            st.metric("✅ Disponibles", disponibles)

# ========== PANEL ADMIN ==========
def panel_administrador():
    st.title("⚙️ Administración")
    st.markdown(f"**{st.session_state.username}**")
    
    tab1, tab2 = st.tabs(["📦 Productos", "📊 Ventas"])
    
    with tab1:
        st.subheader("Gestión de Productos")
        
        try:
            df_productos = leer_productos()
            
            st.info("💡 Edita y presiona 'Guardar Cambios'")
            
            columnas = ['PRODUCTO', 'MARCA', 'CONTADO', '6 CUOTAS', '12 CUOTAS', 'STOCK', 'CATEGORIA']
            df_edit = df_productos[columnas]
            
            df_editado = st.data_editor(
                df_edit,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "PRODUCTO": st.column_config.TextColumn("Producto", width="large", required=True),
                    "MARCA": st.column_config.TextColumn("Marca", width="medium", required=True),
                    "CONTADO": st.column_config.NumberColumn("Contado", format="₲ %d", required=True),
                    "6 CUOTAS": st.column_config.NumberColumn("6 Cuotas", format="₲ %d", required=True),
                    "12 CUOTAS": st.column_config.NumberColumn("12 Cuotas", format="₲ %d", required=True),
                    "STOCK": st.column_config.NumberColumn("Stock", format="%d", required=True),
                    "CATEGORIA": st.column_config.TextColumn("Categoría", width="medium", required=True)
                },
                hide_index=True,
                key="editor"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    try:
                        cols_orig = ['CATEGORIA', 'MARCA', 'PRODUCTO', 'CONTADO', '12 CUOTAS', '6 CUOTAS', 'STOCK']
                        df_reord = df_editado[['CATEGORIA', 'MARCA', 'PRODUCTO', 'CONTADO', '12 CUOTAS', '6 CUOTAS', 'STOCK']]
                        guardar_productos(df_reord)
                        st.success("✅ Guardado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            with col2:
                if st.button("🔄 Recargar", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 📊 Estadísticas")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(df_productos))
            with col2:
                valor_total = (df_productos['CONTADO'] * df_productos['STOCK']).sum()
                st.metric("Valor Inventario", f"₲ {formato_guaranies(valor_total)}")
            with col3:
                bajo = len(df_productos[df_productos['STOCK'] < 5])
                st.metric("Stock Bajo", bajo)
            with col4:
                sin = len(df_productos[df_productos['STOCK'] == 0])
                st.metric("Sin Stock", sin)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.subheader("Historial de Ventas")
        
        try:
            df_ventas = leer_ventas()
            
            if df_ventas.empty:
                st.info("📭 Sin ventas registradas")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    vendedores = ['Todos'] + df_ventas['VENDEDOR'].unique().tolist()
                    filtro_vendedor = st.selectbox("👤 Vendedor", vendedores)
                
                with col2:
                    tipos = ['Todos'] + df_ventas['TIPO_PAGO'].unique().tolist()
                    filtro_pago = st.selectbox("💳 Tipo Pago", tipos)
                
                df_filt = df_ventas.copy()
                if filtro_vendedor != 'Todos':
                    df_filt = df_filt[df_filt['VENDEDOR'] == filtro_vendedor]
                if filtro_pago != 'Todos':
                    df_filt = df_filt[df_filt['TIPO_PAGO'] == filtro_pago]
                
                st.dataframe(
                    df_filt,
                    use_container_width=True,
                    column_config={
                        "FECHA": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY HH:mm"),
                        "MONTO_TOTAL": st.column_config.NumberColumn("Total", format="₲ %d")
                    }
                )
                
                st.markdown("---")
                st.markdown("### 📊 Resumen")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total = df_filt['MONTO_TOTAL'].sum()
                    st.metric("Total Vendido", f"₲ {formato_guaranies(total)}")
                with col2:
                    st.metric("Cantidad Ventas", len(df_filt))
                with col3:
                    if len(df_filt) > 0:
                        promedio = df_filt['MONTO_TOTAL'].mean()
                        st.metric("Promedio", f"₲ {formato_guaranies(promedio)}")
                    else:
                        st.metric("Promedio", "₲ 0")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ========== MAIN ==========
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.username}")
            st.markdown(f"**Rol:** {st.session_state.user_role}")
            st.markdown("---")
            
            st.markdown(f"### 🏪 {NOMBRE_LOCAL}")
            st.markdown(f"📞 {TELEFONO_LOCAL}")
            st.markdown(f"📍 {DIRECCION_LOCAL}")
            st.markdown("---")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.username = None
                st.rerun()
        
        if st.session_state.user_role == "admin":
            panel_administrador()
        else:
            panel_vendedor()

if __name__ == "__main__":
    main()
