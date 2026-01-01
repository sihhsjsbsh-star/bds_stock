import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

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

# Estilos CSS personalizados - PROFESIONAL MOBILE FIRST
st.markdown("""
<style>
    /* Variables de color */
    :root {
        --primary-color: #FF9900;
        --secondary-color: #146EB4;
        --success-color: #067D62;
        --danger-color: #C7511F;
        --text-dark: #0F1111;
        --text-light: #565959;
        --bg-card: #FFFFFF;
        --bg-hover: #F7F8F8;
        --border-color: #D5D9D9;
    }
    
    /* Contenedor principal */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Barra de búsqueda grande tipo Amazon */
    .search-container {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Tarjeta de producto estilo Amazon */
    .producto-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    
    .producto-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        border-color: var(--secondary-color);
    }
    
    /* Título del producto */
    .producto-titulo {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-dark);
        margin-bottom: 6px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* Marca del producto */
    .producto-marca {
        font-size: 13px;
        color: var(--secondary-color);
        font-weight: 600;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    /* Precio contado - GRANDE Y DESTACADO */
    .precio-contado {
        font-size: 28px;
        font-weight: 700;
        color: #B12704;
        margin: 12px 0 8px 0;
        display: flex;
        align-items: baseline;
    }
    
    .precio-simbolo {
        font-size: 16px;
        font-weight: 500;
        margin-right: 2px;
    }
    
    /* Precios de cuotas - más pequeños */
    .precios-cuotas {
        display: flex;
        gap: 12px;
        margin: 8px 0 12px 0;
        flex-wrap: wrap;
    }
    
    .precio-cuota {
        font-size: 12px;
        color: var(--text-light);
        background: #F0F2F2;
        padding: 4px 8px;
        border-radius: 4px;
    }
    
    .precio-cuota-valor {
        font-weight: 600;
        color: var(--text-dark);
    }
    
    /* Stock con indicador de color */
    .stock-container {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 600;
        margin: 8px 0;
    }
    
    .stock-alto {
        background: #D5F4E6;
        color: var(--success-color);
    }
    
    .stock-medio {
        background: #FFF3CD;
        color: #856404;
    }
    
    .stock-bajo {
        background: #F8D7DA;
        color: var(--danger-color);
        animation: pulse-warning 2s infinite;
    }
    
    @keyframes pulse-warning {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Categoría */
    .categoria-tag {
        display: inline-block;
        font-size: 11px;
        color: var(--text-light);
        background: #F0F2F2;
        padding: 4px 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Botón Vender - estilo Amazon */
    .stButton>button {
        width: 100%;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        border: none;
        transition: all 0.15s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(180deg, #FFD814 0%, #F7CA00 100%);
        color: var(--text-dark);
        border: 1px solid #F0C14B;
    }
    
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(180deg, #F7CA00 0%, #F0C14B 100%);
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }
    
    /* Inputs optimizados */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        font-size: 14px !important;
        padding: 12px !important;
        border-radius: 4px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: var(--secondary-color) !important;
        box-shadow: 0 0 0 3px rgba(20, 110, 180, 0.1) !important;
    }
    
    /* Expander mejorado */
    .streamlit-expanderHeader {
        font-size: 14px !important;
        font-weight: 600 !important;
        background-color: #F7F8F8;
        border-radius: 8px;
        padding: 12px !important;
        border: 1px solid var(--border-color);
    }
    
    /* Badge de resultados */
    .resultados-badge {
        background: var(--secondary-color);
        color: white;
        padding: 8px 16px;
        border-radius: 16px;
        display: inline-block;
        font-weight: 600;
        font-size: 13px;
        margin: 10px 0;
    }
    
    /* Estado vacío */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--text-light);
    }
    
    .empty-state-icon {
        font-size: 72px;
        margin-bottom: 20px;
        opacity: 0.5;
    }
    
    .empty-state h3 {
        color: var(--text-dark);
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    /* Filtros avanzados */
    .filtros-container {
        background: white;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 20px;
    }
    
    /* Optimizaciones móviles */
    @media (max-width: 768px) {
        .producto-card {
            padding: 14px;
        }
        
        .producto-titulo {
            font-size: 15px;
        }
        
        .precio-contado {
            font-size: 24px;
        }
        
        h1 {
            font-size: 22px !important;
        }
        
        h2 {
            font-size: 19px !important;
        }
        
        [data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    
    /* Scroll suave */
    html {
        scroll-behavior: smooth;
    }
</style>
""", unsafe_allow_html=True)

# Función para conectar con Google Sheets
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# Función para leer productos
@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    df = conn.read(worksheet="PRODUCTOS")
    df = df.dropna(how='all')
    return df

# Función para leer ventas
@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try:
        df = conn.read(worksheet="VENTAS")
        df = df.dropna(how='all')
        return df
    except:
        return pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])

# Función para guardar productos
def guardar_productos(df):
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()

# Función para registrar venta
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

# Función para actualizar stock
def actualizar_stock(df_productos, producto_nombre, cantidad_vendida):
    mask = df_productos['PRODUCTO'] == producto_nombre
    df_productos.loc[mask, 'STOCK'] = df_productos.loc[mask, 'STOCK'] - cantidad_vendida
    guardar_productos(df_productos)

# FUNCIÓN PARA RENDERIZAR TARJETA DE PRODUCTO - ESTILO AMAZON
def renderizar_tarjeta_producto(producto, index):
    """Renderiza una tarjeta de producto profesional estilo Amazon"""
    
    nombre = producto['PRODUCTO']
    marca = producto['MARCA']
    categoria = producto['CATEGORIA']
    precio_contado = float(producto['CONTADO'])
    precio_6_cuotas = float(producto['6 CUOTAS'])
    precio_12_cuotas = float(producto['12 CUOTAS'])
    stock = int(producto['STOCK'])
    
    # Determinar clase y emoji de stock
    if stock >= 10:
        stock_class = "stock-alto"
        stock_emoji = "✅"
        stock_texto = "Disponible"
    elif stock >= 5:
        stock_class = "stock-medio"
        stock_emoji = ⚠️"
        stock_texto = f"Quedan {stock}"
    elif stock > 0:
        stock_class = "stock-bajo"
        stock_emoji = "🔴"
        stock_texto = f"¡Solo {stock}!"
    else:
        stock_class = "stock-bajo"
        stock_emoji = "❌"
        stock_texto = "Sin stock"
    
    # HTML de la tarjeta con el ORDEN REQUERIDO
    st.markdown(f"""
    <div class="producto-card">
        <!-- 1. PRODUCTO (Título en negrita) -->
        <div class="producto-titulo">{nombre}</div>
        
        <!-- 2. MARCA -->
        <div class="producto-marca">{marca}</div>
        
        <!-- 3. PRECIO CONTADO (En grande y color llamativo) -->
        <div class="precio-contado">
            <span class="precio-simbolo">₲</span>
            <span>{precio_contado:,.0f}</span>
        </div>
        <div style="font-size: 11px; color: #565959; margin-bottom: 8px;">💳 Precio Contado</div>
        
        <!-- 4. CUOTA 6 | CUOTA 12 (Más pequeños) -->
        <div class="precios-cuotas">
            <div class="precio-cuota">
                6 Cuotas: <span class="precio-cuota-valor">₲ {precio_6_cuotas:,.0f}</span>
            </div>
            <div class="precio-cuota">
                12 Cuotas: <span class="precio-cuota-valor">₲ {precio_12_cuotas:,.0f}</span>
            </div>
        </div>
        
        <!-- 5. STOCK (Con indicador de color) -->
        <div class="stock-container {stock_class}">
            <span>{stock_emoji}</span>
            <span>{stock_texto}</span>
        </div>
        
        <!-- 6. CATEGORÍA -->
        <div class="categoria-tag">📂 {categoria}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de vender
    if stock > 0:
        if st.button(f"🛒 VENDER", key=f"vender_{index}", use_container_width=True, type="primary"):
            st.session_state[f'venta_activa_{index}'] = True
            st.rerun()
        
        # Formulario de venta
        if st.session_state.get(f'venta_activa_{index}', False):
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
                        "Tipo de Pago",
                        ["Contado", "6 CUOTAS", "12 CUOTAS"],
                        key=f"pago_{index}"
                    )
                
                # Calcular precio según tipo de pago
                if tipo_pago == "Contado":
                    precio_unitario = precio_contado
                elif tipo_pago == "6 CUOTAS":
                    precio_unitario = precio_6_cuotas
                else:
                    precio_unitario = precio_12_cuotas
                
                monto_total = precio_unitario * cantidad
                
                # Resumen
                st.markdown("---")
                st.markdown(f"**Producto:** {nombre}")
                st.markdown(f"**Precio Unit.:** ₲ {precio_unitario:,.0f}")
                st.markdown(f"**Cantidad:** {cantidad}")
                st.markdown(f"### 💰 Total: ₲ {monto_total:,.0f}")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("✅ Confirmar Venta", key=f"conf_{index}", use_container_width=True):
                        try:
                            df_productos = leer_productos()
                            actualizar_stock(df_productos, nombre, cantidad)
                            registrar_venta(
                                st.session_state.username,
                                nombre,
                                cantidad,
                                tipo_pago,
                                monto_total
                            )
                            st.success("🎉 ¡Venta registrada exitosamente!")
                            st.session_state[f'venta_activa_{index}'] = False
                            import time
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with col_b:
                    if st.button("❌ Cancelar", key=f"canc_{index}", use_container_width=True):
                        st.session_state[f'venta_activa_{index}'] = False
                        st.rerun()
    else:
        st.error("⛔ Producto sin stock")
    
    st.markdown("")

# Sistema de autenticación - SIN CREDENCIALES VISIBLES
def login_page():
    # Centrar el formulario
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title(f"🏪 {NOMBRE_LOCAL}")
        st.markdown("### Sistema de Gestión")
        st.markdown("---")
        
        # Formulario limpio sin credenciales de prueba
        usuario = st.text_input("👤 Usuario", key="login_user", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", key="login_pass", placeholder="Ingresa tu contraseña")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔐 Ingresar al Sistema", use_container_width=True, type="primary"):
            if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USUARIOS[usuario]["rol"]
                st.session_state.username = USUARIOS[usuario]["nombre_completo"]
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        
        st.markdown("---")
        st.caption("🔒 Sistema seguro conectado a Google Sheets")

# Panel del vendedor - DISEÑO TIPO AMAZON
def panel_vendedor():
    st.title("🛒 Punto de Venta")
    st.markdown(f"Hola, **{st.session_state.username}** 👋")
    st.markdown("---")
    
    # Cargar productos
    try:
        df_productos = leer_productos()
    except Exception as e:
        st.error(f"❌ Error al cargar productos: {str(e)}")
        st.info("Verifica la conexión con Google Sheets.")
        return
    
    # BUSCADOR GRANDE TIPO AMAZON (Lo primero que aparece)
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    busqueda = st.text_input(
        "🔍 Buscar productos",
        placeholder="Busca por nombre o marca del producto...",
        key="search_vendedor",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FILTROS AVANZADOS
    st.markdown('<div class="filtros-container">', unsafe_allow_html=True)
    st.markdown("**🎯 Filtros Avanzados**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # A) Filtro por Categoría
        categorias = ['Todas las categorías'] + sorted(df_productos['CATEGORIA'].unique().tolist())
        categoria_seleccionada = st.selectbox(
            "📂 Categoría",
            categorias,
            key="filtro_categoria"
        )
    
    with col2:
        # B) Filtro por Marca
        marcas = ['Todas las marcas'] + sorted(df_productos['MARCA'].unique().tolist())
        marca_seleccionada = st.selectbox(
            "🏷️ Marca",
            marcas,
            key="filtro_marca"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # APLICAR FILTROS
    df_filtrado = df_productos.copy()
    
    # Filtrar por categoría
    if categoria_seleccionada != 'Todas las categorías':
        df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == categoria_seleccionada]
    
    # Filtrar por marca
    if marca_seleccionada != 'Todas las marcas':
        df_filtrado = df_filtrado[df_filtrado['MARCA'] == marca_seleccionada]
    
    # Filtrar por búsqueda de texto (Nombre o Marca)
    if busqueda:
        mascara = (
            df_filtrado['PRODUCTO'].str.contains(busqueda, case=False, na=False) |
            df_filtrado['MARCA'].str.contains(busqueda, case=False, na=False)
        )
        df_filtrado = df_filtrado[mascara]
    
    # MOSTRAR RESULTADOS
    # Verificar si hay algún filtro activo
    hay_filtros = (
        busqueda or 
        categoria_seleccionada != 'Todas las categorías' or 
        marca_seleccionada != 'Todas las marcas'
    )
    
    if hay_filtros:
        # Hay filtros aplicados - mostrar resultados
        if len(df_filtrado) > 0:
            st.markdown(
                f'<div class="resultados-badge">✅ {len(df_filtrado)} productos encontrados</div>', 
                unsafe_allow_html=True
            )
            st.markdown("")
            
            # Renderizar tarjetas de productos con el ORDEN especificado
            for index, row in df_filtrado.iterrows():
                renderizar_tarjeta_producto(row, index)
        else:
            # No hay resultados
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>No encontramos productos</h3>
                <p>Intenta ajustar los filtros o buscar con otros términos</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # No hay filtros - mostrar mensaje inicial
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🛍️</div>
            <h3>¡Bienvenido al sistema de ventas!</h3>
            <p>Usa el buscador o los filtros para encontrar productos rápidamente</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar estadísticas generales
        st.markdown("---")
        st.markdown("### 📊 Resumen del Inventario")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Total Productos", len(df_productos))
        with col2:
            st.metric("📂 Categorías", len(df_productos['CATEGORIA'].unique()))
        with col3:
            st.metric("🏷️ Marcas", len(df_productos['MARCA'].unique()))
        with col4:
            productos_disponibles = len(df_productos[df_productos['STOCK'] > 0])
            st.metric("✅ Con Stock", productos_disponibles)

# Panel del administrador
def panel_administrador():
    st.title("⚙️ Panel de Administración")
    st.markdown(f"Bienvenido, **{st.session_state.username}**")
    
    tab1, tab2 = st.tabs(["📦 Gestión de Productos", "📊 Historial de Ventas"])
    
    # TAB 1: Gestión de Productos
    with tab1:
        st.subheader("Gestión de Productos")
        
        try:
            df_productos = leer_productos()
            
            st.info("💡 Edita directamente en la tabla. Presiona 'Guardar Cambios' cuando termines.")
            
            # ORDEN DE COLUMNAS ESPECIFICADO: PRODUCTO, MARCA, CONTADO, 6 CUOTAS, 12 CUOTAS, STOCK, CATEGORIA
            columnas_ordenadas = ['PRODUCTO', 'MARCA', 'CONTADO', '6 CUOTAS', '12 CUOTAS', 'STOCK', 'CATEGORIA']
            df_productos_ordenado = df_productos[columnas_ordenadas]
            
            # Editor de datos
            df_editado = st.data_editor(
                df_productos_ordenado,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "PRODUCTO": st.column_config.TextColumn("Producto", width="large", required=True),
                    "MARCA": st.column_config.TextColumn("Marca", width="medium", required=True),
                    "CONTADO": st.column_config.NumberColumn("Contado", format="₲ %.0f", width="small", required=True),
                    "6 CUOTAS": st.column_config.NumberColumn("6 Cuotas", format="₲ %.0f", width="small", required=True),
                    "12 CUOTAS": st.column_config.NumberColumn("12 Cuotas", format="₲ %.0f", width="small", required=True),
                    "STOCK": st.column_config.NumberColumn("Stock", format="%d", width="small", required=True),
                    "CATEGORIA": st.column_config.TextColumn("Categoría", width="medium", required=True)
                },
                hide_index=True,
                key="editor_productos"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    try:
                        # Reordenar al formato original de Google Sheets
                        columnas_originales = ['CATEGORIA', 'MARCA', 'PRODUCTO', 'CONTADO', '12 CUOTAS', '6 CUOTAS', 'STOCK']
                        df_editado = df_editado[columnas_originales]
                        guardar_productos(df_editado)
                        st.success("✅ Productos actualizados correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {str(e)}")
            
            with col2:
                if st.button("🔄 Recargar Datos", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            
            # Métricas
            st.markdown("---")
            st.markdown("### 📊 Estadísticas del Inventario")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Productos", len(df_productos))
            with col2:
                valor_total = (df_productos['CONTADO'] * df_productos['STOCK']).sum()
                st.metric("Valor Inventario", f"₲ {valor_total:,.0f}")
            with col3:
                bajo_stock = len(df_productos[df_productos['STOCK'] < 5])
                st.metric("Stock Bajo", bajo_stock)
            with col4:
                sin_stock = len(df_productos[df_productos['STOCK'] == 0])
                st.metric("Sin Stock", sin_stock)
            
        except Exception as e:
            st.error(f"❌ Error al cargar productos: {str(e)}")
    
    # TAB 2: Historial de Ventas
    with tab2:
        st.subheader("Historial de Ventas")
        
        try:
            df_ventas = leer_ventas()
            
            if df_ventas.empty:
                st.info("📭 No hay ventas registradas aún.")
            else:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    vendedores = ['Todos'] + df_ventas['VENDEDOR'].unique().tolist()
                    filtro_vendedor = st.selectbox("👤 Filtrar por vendedor", vendedores)
                
                with col2:
                    tipos_pago = ['Todos'] + df_ventas['TIPO_PAGO'].unique().tolist()
                    filtro_pago = st.selectbox("💳 Filtrar por tipo de pago", tipos_pago)
                
                # Aplicar filtros
                df_filtrado = df_ventas.copy()
                if filtro_vendedor != 'Todos':
                    if filtro_vendedor != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['VENDEDOR'] == filtro_vendedor]
                
                if filtro_pago != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['TIPO_PAGO'] == filtro_pago]
                
                # Mostrar tabla de ventas
                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "MONTO_TOTAL": st.column_config.NumberColumn("Total", format="₲ %.0f"),
                        "FECHA": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY HH:mm")
                    }
                )
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

# --- FUNCIÓN PRINCIPAL (MAIN) ---
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar simple para salir
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.username}")
            st.markdown(f"Rol: **{st.session_state.user_role}**")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.rerun()
            
            st.markdown("---")
            st.info("📞 Soporte: " + TELEFONO_LOCAL)

        # Router de páginas
        if st.session_state.user_role == "admin":
            panel_administrador()
        else:
            panel_vendedor()

if __name__ == "__main__":
    main()
