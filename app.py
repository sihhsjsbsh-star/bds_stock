import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ========== CONFIGURACIÓN DEL LOCAL ==========
NOMBRE_LOCAL = "Electrodomésticos del Sur"
TELEFONO_LOCAL = "+595 21 123-4567"
DIRECCION_LOCAL = "Av. Mariscal López 1234, Asunción"
# =============================================

# Configuración de la página
st.set_page_config(
    page_title=f"{NOMBRE_LOCAL} - Gestión",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .producto-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .precio-tag {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .stock-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 5px;
        background-color: #4caf50;
        color: white;
        font-weight: bold;
    }
    .stock-bajo {
        background-color: #f44336;
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
    # Limpiar filas vacías
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
        # Si la hoja VENTAS no existe o está vacía, crear DataFrame vacío
        return pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])

# Función para guardar productos
def guardar_productos(df):
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()

# Función para registrar venta
def registrar_venta(vendedor, producto, cantidad, tipo_pago, monto_total):
    conn = get_connection()
    
    # Leer ventas actuales
    df_ventas = leer_ventas()
    
    # Crear nueva fila
    nueva_venta = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': vendedor,
        'PRODUCTO': producto,
        'CANTIDAD': cantidad,
        'TIPO_PAGO': tipo_pago,
        'MONTO_TOTAL': monto_total
    }])
    
    # Agregar nueva venta
    df_ventas = pd.concat([df_ventas, nueva_venta], ignore_index=True)
    
    # Guardar en Google Sheets
    conn.update(worksheet="VENTAS", data=df_ventas)
    
    st.cache_data.clear()

# Función para actualizar stock
def actualizar_stock(df_productos, producto_nombre, cantidad_vendida):
    # Buscar el producto y reducir stock
    mask = df_productos['PRODUCTO'] == producto_nombre
    df_productos.loc[mask, 'STOCK'] = df_productos.loc[mask, 'STOCK'] - cantidad_vendida
    
    # Guardar cambios
    guardar_productos(df_productos)

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
            if usuario == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "Administrador"
                st.rerun()
            elif usuario == "vendedor" and password == "ventas123":
                st.session_state.logged_in = True
                st.session_state.user_role = "vendedor"
                st.session_state.username = usuario
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        
        st.markdown("---")
        st.info("""
        **Credenciales de prueba:**
        
        👤 **Administrador:**
        - Usuario: `admin`
        - Contraseña: `admin123`
        
        👤 **Vendedor:**
        - Usuario: `vendedor`
        - Contraseña: `ventas123`
        """)

# Panel del vendedor
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
    
    # Buscador de productos
    st.markdown("### 🔍 Buscar Producto")
    busqueda = st.text_input(
        "Buscar por nombre, marca o categoría",
        placeholder="Ej: heladera, samsung, refrigeración...",
        key="search_vendedor"
    )
    
    # Filtrar productos
    if busqueda:
        mascara = (
            df_productos['PRODUCTO'].str.contains(busqueda, case=False, na=False) |
            df_productos['MARCA'].str.contains(busqueda, case=False, na=False) |
            df_productos['CATEGORIA'].str.contains(busqueda, case=False, na=False)
        )
        df_filtrado = df_productos[mascara]
    else:
        df_filtrado = df_productos
    
    st.markdown("---")
    
    if df_filtrado.empty:
        st.warning("No se encontraron productos.")
    else:
        st.success(f"**{len(df_filtrado)} productos encontrados**")
        
        # Selector de producto
        productos_lista = df_filtrado['PRODUCTO'].tolist()
        producto_seleccionado = st.selectbox(
            "Selecciona el producto a vender",
            productos_lista,
            key="producto_select"
        )
        
        if producto_seleccionado:
            # Obtener información del producto
            producto_info = df_filtrado[df_filtrado['PRODUCTO'] == producto_seleccionado].iloc[0]
            
            # Mostrar información del producto
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="producto-card">
                    <h3>{producto_info['PRODUCTO']}</h3>
                    <p><strong>Marca:</strong> {producto_info['MARCA']}</p>
                    <p><strong>Categoría:</strong> {producto_info['CATEGORIA']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                stock_actual = int(producto_info['STOCK'])
                stock_class = "stock-badge" if stock_actual >= 5 else "stock-badge stock-bajo"
                st.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <p style="margin: 0;">Stock Disponible</p>
                    <div class="{stock_class}" style="font-size: 32px; margin-top: 10px;">
                        {stock_actual}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Formulario de venta
            if stock_actual > 0:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    cantidad = st.number_input(
                        "Cantidad a vender",
                        min_value=1,
                        max_value=stock_actual,
                        value=1,
                        step=1,
                        key="cantidad_venta"
                    )
                
                with col_b:
                    tipo_pago = st.selectbox(
                        "Tipo de Pago",
                        ["Contado", "6 CUOTAS", "12 CUOTAS"],
                        key="tipo_pago_select"
                    )
                
                # Calcular precio según tipo de pago
                if tipo_pago == "Contado":
                    precio_unitario = float(producto_info['CONTADO'])
                elif tipo_pago == "6 CUOTAS":
                    precio_unitario = float(producto_info['6 CUOTAS'])
                else:  # 12 CUOTAS
                    precio_unitario = float(producto_info['12 CUOTAS'])
                
                monto_total = precio_unitario * cantidad
                
                # Mostrar resumen
                st.markdown("### 💰 Resumen de la Venta")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Precio Unitario", f"₲ {precio_unitario:,.0f}")
                with col2:
                    st.metric("Cantidad", cantidad)
                with col3:
                    st.metric("Total", f"₲ {monto_total:,.0f}")
                
                st.markdown("---")
                
                # Botón confirmar venta
                if st.button("✅ Confirmar Venta", use_container_width=True, type="primary"):
                    try:
                        # Actualizar stock
                        actualizar_stock(df_productos, producto_seleccionado, cantidad)
                        
                        # Registrar venta
                        registrar_venta(
                            st.session_state.username,
                            producto_seleccionado,
                            cantidad,
                            tipo_pago,
                            monto_total
                        )
                        
                        st.success("🎉 ¡Venta registrada exitosamente!")
                        st.balloons()
                        
                        # Esperar un momento y recargar
                        import time
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al registrar la venta: {str(e)}")
            else:
                st.error("⚠️ Este producto no tiene stock disponible.")

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
            
            # Editor de datos
            df_editado = st.data_editor(
                df_productos,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "CATEGORIA": st.column_config.TextColumn("Categoría", required=True),
                    "MARCA": st.column_config.TextColumn("Marca", required=True),
                    "PRODUCTO": st.column_config.TextColumn("Producto", required=True),
                    "CONTADO": st.column_config.NumberColumn("Precio Contado", format="₲ %.0f", required=True),
                    "12 CUOTAS": st.column_config.NumberColumn("Precio 12 Cuotas", format="₲ %.0f", required=True),
                    "6 CUOTAS": st.column_config.NumberColumn("Precio 6 Cuotas", format="₲ %.0f", required=True),
                    "STOCK": st.column_config.NumberColumn("Stock", format="%d unidades", required=True)
                },
                hide_index=True,
                key="editor_productos"
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    try:
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
