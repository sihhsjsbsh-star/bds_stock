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

# Estilos CSS personalizados - MOBILE FIRST
st.markdown("""
<style>
    /* Contenedor principal */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Tarjeta de producto - DISEÑO VERTICAL PARA MÓVIL */
    .producto-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .producto-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .producto-nombre {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    
    .producto-marca {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    
    .producto-categoria {
        font-size: 12px;
        opacity: 0.8;
        background: rgba(255,255,255,0.2);
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    
    .precio-grande {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .stock-info {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    
    .stock-bajo {
        background: #ff6b6b;
        animation: pulse 2s infinite;
    }
    
    .stock-ok {
        background: rgba(76, 175, 80, 0.8);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Botones más grandes y táctiles */
    .stButton>button {
        width: 100%;
        padding: 14px 24px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 16px;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Inputs optimizados para móvil */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    
    /* Expander más visible */
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: 600 !important;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px !important;
    }
    
    /* Mensaje de búsqueda vacía */
    .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: #666;
    }
    
    .empty-state-icon {
        font-size: 64px;
        margin-bottom: 20px;
    }
    
    /* Optimizaciones para pantallas pequeñas */
    @media (max-width: 768px) {
        .producto-card {
            padding: 16px;
        }
        
        .producto-nombre {
            font-size: 16px;
        }
        
        .precio-grande {
            font-size: 24px;
        }
        
        h1 {
            font-size: 24px !important;
        }
        
        h2 {
            font-size: 20px !important;
        }
        
        h3 {
            font-size: 18px !important;
        }
        
        [data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    
    /* Badge de resultados */
    .resultados-badge {
        background: #1f77b4;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
        margin: 10px 0;
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

# FUNCIÓN PARA RENDERIZAR TARJETA DE PRODUCTO - MOBILE FIRST
def renderizar_tarjeta_producto(producto, index):
    """Renderiza una tarjeta de producto optimizada para móvil"""
    
    nombre = producto['PRODUCTO']
    marca = producto['MARCA']
    categoria = producto['CATEGORIA']
    precio_contado = float(producto['CONTADO'])
    precio_6_cuotas = float(producto['6 CUOTAS'])
    precio_12_cuotas = float(producto['12 CUOTAS'])
    stock = int(producto['STOCK'])
    
    # Determinar clase de stock
    stock_class = "stock-ok" if stock >= 5 else "stock-bajo"
    stock_emoji = "✅" if stock >= 5 else "⚠️"
    
    # HTML de la tarjeta
    st.markdown(f"""
    <div class="producto-card">
        <div class="producto-categoria">📂 {categoria}</div>
        <div class="producto-nombre">{nombre}</div>
        <div class="producto-marca">🏷️ {marca}</div>
        <div class="precio-grande">₲ {precio_contado:,.0f}</div>
        <div style="font-size: 12px; opacity: 0.9;">💳 Contado</div>
        <div class="stock-info {stock_class}">{stock_emoji} Stock: {stock}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de vender
    if stock > 0:
        if st.button(f"🛒 Vender", key=f"vender_{index}", use_container_width=True, type="primary"):
            st.session_state[f'venta_activa_{index}'] = True
            st.rerun()
        
        # Formulario de venta dentro de expander
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
                st.markdown(f"**Precio Unit.:** ₲ {precio_unitario:,.0f}")
                st.markdown(f"**Cantidad:** {cantidad}")
                st.markdown(f"### 💰 Total: ₲ {monto_total:,.0f}")
                
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
                                monto_total
                            )
                            st.success("🎉 ¡Venta exitosa!")
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
        st.error("⛔ Sin stock")
    
    st.markdown("---")

# Sistema de autenticación
def login_page():
    st.title(f"🏪 {NOMBRE_LOCAL}")
    st.markdown("### Sistema de Gestión con Google Sheets")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Iniciar Sesión")
        usuario = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        
        if st.button("Ingresar", use_container_width=True):
            if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USUARIOS[usuario]["rol"]
                st.session_state.username = USUARIOS[usuario]["nombre_completo"]
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        
        st.markdown("---")
        st.info("""
        **Credenciales de prueba:**
        
        👤 **Administrador:**
        - Usuario: `Rosana`
        - Contraseña: `bdse1975`
        
        👤 **Vendedor:**
        - Usuario: `vendedor`
        - Contraseña: `ventas123`
        """)

# Panel del vendedor - REDISEÑADO MOBILE FIRST
def panel_vendedor():
    st.title("🛒 Registro de Ventas")
    st.markdown(f"Bienvenido, **{st.session_state.username}**")
    st.markdown("---")
    
    # Cargar productos
    try:
        df_productos = leer_productos()
    except Exception as e:
        st.error(f"❌ Error al cargar productos: {str(e)}")
        st.info("Verifica que tu Google Sheet tenga una hoja llamada 'PRODUCTOS' con las columnas correctas.")
        return
    
    # FILTROS EN DOS COLUMNAS
    col1, col2 = st.columns(2)
    
    with col1:
        # Selector de categoría
        categorias = ['Todas'] + sorted(df_productos['CATEGORIA'].unique().tolist())
        categoria_seleccionada = st.selectbox(
            "📂 Categoría",
            categorias,
            key="filtro_categoria"
        )
    
    with col2:
        # Buscador de texto
        busqueda = st.text_input(
            "🔍 Buscar",
            placeholder="Nombre o marca...",
            key="search_vendedor"
        )
    
    st.markdown("---")
    
    # APLICAR FILTROS
    df_filtrado = df_productos.copy()
    
    # Filtrar por categoría
    if categoria_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == categoria_seleccionada]
    
    # Filtrar por búsqueda
    if busqueda:
        mascara = (
            df_filtrado['PRODUCTO'].str.contains(busqueda, case=False, na=False) |
            df_filtrado['MARCA'].str.contains(busqueda, case=False, na=False)
        )
        df_filtrado = df_filtrado[mascara]
    
    # MOSTRAR RESULTADOS
    if busqueda or categoria_seleccionada != 'Todas':
        # Hay filtros aplicados
        if len(df_filtrado) > 0:
            st.markdown(f'<div class="resultados-badge">📦 {len(df_filtrado)} productos encontrados</div>', unsafe_allow_html=True)
            st.markdown("")
            
            # Renderizar tarjetas de productos
            for index, row in df_filtrado.iterrows():
                renderizar_tarjeta_producto(row, index)
        else:
            # No hay resultados
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>No se encontraron productos</h3>
                <p>Intenta con otro término de búsqueda o categoría diferente</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # No hay filtros - mostrar mensaje inicial
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">👆</div>
            <h3>Usa el buscador o selecciona una categoría para empezar</h3>
            <p>Evitamos mostrar todos los productos para una mejor experiencia en móvil</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar estadísticas generales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Total Productos", len(df_productos))
        with col2:
            st.metric("📂 Categorías", len(df_productos['CATEGORIA'].unique()))
        with col3:
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
            
            st.info("💡 Puedes editar, agregar o eliminar productos directamente en la tabla. Presiona 'Guardar Cambios' cuando termines.")
            
            # Reordenar columnas para mejor visualización
            columnas_ordenadas = ['PRODUCTO', 'MARCA', 'CATEGORIA', 'CONTADO', '6 CUOTAS', '12 CUOTAS', 'STOCK']
            df_productos = df_productos[columnas_ordenadas]
            
            # Editor de datos
            df_editado = st.data_editor(
                df_productos,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "PRODUCTO": st.column_config.TextColumn("Producto", width="large", required=True),
                    "MARCA": st.column_config.TextColumn("Marca", width="medium", required=True),
                    "CATEGORIA": st.column_config.TextColumn("Categoría", width="medium", required=True),
                    "CONTADO": st.column_config.NumberColumn("Contado", format="₲ %.0f", width="small", required=True),
                    "6 CUOTAS": st.column_config.NumberColumn("6 Cuotas", format="₲ %.0f", width="small", required=True),
                    "12 CUOTAS": st.column_config.NumberColumn("12 Cuotas", format="₲ %.0f", width="small", required=True),
                    "STOCK": st.column_config.NumberColumn("Stock", format="%d", width="small", required=True)
                },
                hide_index=True,
                key="editor_productos"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    try:
                        # Reordenar al formato original
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
            st.markdown("### 📊 Estadísticas")
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
                st.info("No hay ventas registradas aún.")
            else:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    vendedores = ['Todos'] + df_ventas['VENDEDOR'].unique().tolist()
                    filtro_vendedor = st.selectbox("Filtrar por vendedor", vendedores)
                
                with col2:
                    tipos_pago = ['Todos'] + df_ventas['TIPO_PAGO'].unique().tolist()
                    filtro_pago = st.selectbox("Filtrar por tipo de pago", tipos_pago)
                
                # Aplicar filtros
                df_filtrado = df_ventas.copy()
                if filtro_vendedor != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['VENDEDOR'] == filtro_vendedor]
                if filtro_pago != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['TIPO_PAGO'] == filtro_pago]
                
                # Métricas de ventas
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Ventas", len(df_filtrado))
                with col2:
                    total_facturado = df_filtrado['MONTO_TOTAL'].sum()
                    st.metric("Total Facturado", f"₲ {total_facturado:,.0f}")
                with col3:
                    total_unidades = df_filtrado['CANTIDAD'].sum()
                    st.metric("Unidades Vendidas", int(total_unidades))
                with col4:
                    if len(df_filtrado) > 0:
                        ticket_promedio = df_filtrado['MONTO_TOTAL'].mean()
                        st.metric("Ticket Promedio", f"₲ {ticket_promedio:,.0f}")
                
                st.markdown("---")
                
                # Tabla de ventas
                st.dataframe(
                    df_filtrado,
                    column_config={
                        "FECHA": "Fecha",
                        "VENDEDOR": "Vendedor",
                        "PRODUCTO": "Producto",
                        "CANTIDAD": st.column_config.NumberColumn("Cantidad", format="%d"),
                        "TIPO_PAGO": "Tipo de Pago",
                        "MONTO_TOTAL": st.column_config.NumberColumn("Monto Total", format="₲ %.0f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Botón para refrescar
                if st.button("🔄 Actualizar Ventas", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error al cargar ventas: {str(e)}")

# Función principal
def main():
    # Inicializar session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Mostrar página según estado de sesión
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar
        with st.sidebar:
            st.markdown(f"## 🏪 {NOMBRE_LOCAL}")
            st.markdown("---")
            st.markdown(f"### 👤 {st.session_state.username}")
            st.markdown(f"**Rol:** {st.session_state.user_role.upper()}")
            st.markdown("---")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.username = None
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 📊 Google Sheets")
            st.success("✅ Conectado")
            
            if TELEFONO_LOCAL or DIRECCION_LOCAL:
                st.markdown("---")
                st.markdown("### 📞 Contacto")
                if TELEFONO_LOCAL:
                    st.markdown(f"**Tel:** {TELEFONO_LOCAL}")
                if DIRECCION_LOCAL:
                    st.markdown(f"**Dir:** {DIRECCION_LOCAL}")
        
        # Mostrar panel según rol
        if st.session_state.user_role == "vendedor":
            panel_vendedor()
        elif st.session_state.user_role == "admin":
            panel_administrador()

if __name__ == "__main__":
    main()
