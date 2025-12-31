import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ========== CONFIGURACIÓN DEL LOCAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"  # 👈 CAMBIA AQUÍ EL NOMBRE DE TU LOCAL
TELEFONO_LOCAL = "+595 982 627824"  # 👈 OPCIONAL: Agrega tu teléfono
DIRECCION_LOCAL = "Avenida 1ro. de Mayo &, Carlos Antonio López, Capiatá"  # 👈 OPCIONAL: Agrega tu dirección
# =============================================

# Configuración de la página
st.set_page_config(
    page_title=f"{NOMBRE_LOCAL} - Gestión",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .low-stock {
        background-color: #ffebee;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }
    .product-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f5f5f5;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de la base de datos
def init_db():
    conn = sqlite3.connect('electrodomesticos.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            fecha_actualizacion TEXT
        )
    ''')
    
    # Insertar datos de ejemplo si la tabla está vacía
    c.execute('SELECT COUNT(*) FROM productos')
    if c.fetchone()[0] == 0:
        productos_ejemplo = [
            ('Heladera No Frost 350L', 'Samsung', 'Refrigeración', 899999.99, 8),
            ('Lavarropas Automático 8kg', 'LG', 'Lavado', 599999.99, 3),
            ('Microondas Digital 28L', 'Philco', 'Cocina', 89999.99, 12),
            ('Aire Acondicionado 3500W', 'BGH', 'Climatización', 649999.99, 2),
            ('Cocina a Gas 4 Hornallas', 'Longvie', 'Cocina', 299999.99, 6),
            ('Freezer Vertical 250L', 'Patrick', 'Refrigeración', 459999.99, 4),
            ('Lavavajillas 12 Cubiertos', 'Drean', 'Lavado', 749999.99, 1),
            ('Horno Eléctrico 60L', 'Atma', 'Cocina', 129999.99, 15),
            ('Ventilador de Pie', 'Liliana', 'Climatización', 45999.99, 20),
            ('Aspiradora Robot', 'Xiaomi', 'Limpieza', 299999.99, 7)
        ]
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for producto in productos_ejemplo:
            c.execute('''
                INSERT INTO productos (nombre, marca, categoria, precio, stock, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (*producto, fecha_actual))
    
    conn.commit()
    return conn

# Funciones de gestión de productos
def obtener_productos(conn, filtro=''):
    query = '''
        SELECT id, nombre, marca, categoria, precio, stock, fecha_actualizacion 
        FROM productos
    '''
    if filtro:
        query += f" WHERE LOWER(nombre) LIKE '%{filtro.lower()}%' OR LOWER(categoria) LIKE '%{filtro.lower()}%'"
    query += ' ORDER BY nombre'
    
    df = pd.read_sql_query(query, conn)
    return df

def agregar_producto(conn, nombre, marca, categoria, precio, stock):
    c = conn.cursor()
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO productos (nombre, marca, categoria, precio, stock, fecha_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, marca, categoria, precio, stock, fecha_actual))
    conn.commit()

def editar_producto(conn, id_producto, nombre, marca, categoria, precio, stock):
    c = conn.cursor()
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        UPDATE productos 
        SET nombre=?, marca=?, categoria=?, precio=?, stock=?, fecha_actualizacion=?
        WHERE id=?
    ''', (nombre, marca, categoria, precio, stock, fecha_actual, id_producto))
    conn.commit()

def eliminar_producto(conn, id_producto):
    c = conn.cursor()
    c.execute('DELETE FROM productos WHERE id=?', (id_producto,))
    conn.commit()

# Sistema de autenticación
def login_page():
    st.title(f"🏪 {NOMBRE_LOCAL}")
    st.markdown(f"### Sistema de Gestión de Inventario")
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
                st.session_state.username = "Vendedor"
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
def panel_vendedor(conn):
    st.title("📋 Consulta de Productos")
    st.markdown(f"Bienvenido, **{st.session_state.username}**")
    
    # Barra de búsqueda prominente
    st.markdown("### 🔍 Búsqueda de Productos")
    filtro = st.text_input(
        "Buscar por nombre o categoría",
        placeholder="Ej: heladera, cocina, samsung...",
        key="search_vendedor"
    )
    
    st.markdown("---")
    
    # Obtener y mostrar productos
    df = obtener_productos(conn, filtro)
    
    if df.empty:
        st.warning("No se encontraron productos con ese criterio de búsqueda.")
    else:
        st.success(f"**{len(df)} productos encontrados**")
        
        # Formatear precio para visualización
        df['Precio'] = df['precio'].apply(lambda x: f"${x:,.2f}")
        df['Stock'] = df['stock']
        
        # Mostrar tabla
        st.dataframe(
            df[['nombre', 'marca', 'categoria', 'Precio', 'Stock']],
            column_config={
                'nombre': 'Producto',
                'marca': 'Marca',
                'categoria': 'Categoría',
                'Precio': 'Precio',
                'Stock': st.column_config.NumberColumn(
                    'Stock',
                    help='Unidades disponibles',
                    format='%d unidades'
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Alerta de stock bajo
        productos_bajo_stock = df[df['stock'] < 5]
        if not productos_bajo_stock.empty:
            st.markdown("### ⚠️ Productos con Stock Bajo")
            for _, producto in productos_bajo_stock.iterrows():
                st.markdown(f"""
                <div class="low-stock">
                    <strong>{producto['nombre']}</strong> - {producto['marca']}<br>
                    Stock actual: <strong>{producto['stock']} unidades</strong>
                </div>
                """, unsafe_allow_html=True)

# Panel del administrador
def panel_administrador(conn):
    st.title("⚙️ Panel de Administración")
    st.markdown(f"Bienvenido, **{st.session_state.username}**")
    
    # Menú de opciones
    tab1, tab2, tab3 = st.tabs(["📦 Ver Productos", "➕ Agregar Producto", "✏️ Editar/Eliminar"])
    
    # TAB 1: Ver productos
    with tab1:
        st.subheader("Inventario de Productos")
        filtro = st.text_input(
            "🔍 Buscar por nombre o categoría",
            placeholder="Filtrar productos...",
            key="search_admin"
        )
        
        df = obtener_productos(conn, filtro)
        
        if df.empty:
            st.warning("No hay productos registrados.")
        else:
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Productos", len(df))
            with col2:
                valor_total = (df['precio'] * df['stock']).sum()
                st.metric("Valor Inventario", f"${valor_total:,.0f}")
            with col3:
                bajo_stock = len(df[df['stock'] < 5])
                st.metric("Stock Bajo", bajo_stock, delta=f"-{bajo_stock}" if bajo_stock > 0 else "OK")
            
            st.markdown("---")
            
            # Tabla de productos
            df['Precio'] = df['precio'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(
                df[['id', 'nombre', 'marca', 'categoria', 'Precio', 'stock']],
                column_config={
                    'id': 'ID',
                    'nombre': 'Producto',
                    'marca': 'Marca',
                    'categoria': 'Categoría',
                    'Precio': 'Precio',
                    'stock': 'Stock'
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Alerta de stock bajo
            productos_bajo_stock = df[df['stock'] < 5]
            if not productos_bajo_stock.empty:
                st.markdown("### ⚠️ Alertas de Stock Bajo")
                for _, producto in productos_bajo_stock.iterrows():
                    st.markdown(f"""
                    <div class="low-stock">
                        <strong>ID {producto['id']}</strong>: {producto['nombre']} - {producto['marca']}<br>
                        Stock actual: <strong>{producto['stock']} unidades</strong> ⚠️
                    </div>
                    """, unsafe_allow_html=True)
    
    # TAB 2: Agregar producto
    with tab2:
        st.subheader("Agregar Nuevo Producto")
        
        with st.form("form_agregar"):
            nombre = st.text_input("Nombre del Producto*")
            marca = st.text_input("Marca*")
            
            categorias = ['Refrigeración', 'Lavado', 'Cocina', 'Climatización', 'Limpieza', 'Otro']
            categoria = st.selectbox("Categoría*", categorias)
            
            col1, col2 = st.columns(2)
            with col1:
                precio = st.number_input("Precio ($)*", min_value=0.0, step=1000.0, format="%.2f")
            with col2:
                stock = st.number_input("Stock (unidades)*", min_value=0, step=1)
            
            submitted = st.form_submit_button("Agregar Producto", use_container_width=True)
            
            if submitted:
                if nombre and marca and precio > 0:
                    agregar_producto(conn, nombre, marca, categoria, precio, stock)
                    st.success(f"✅ Producto '{nombre}' agregado exitosamente!")
                    st.rerun()
                else:
                    st.error("❌ Por favor completa todos los campos obligatorios.")
    
    # TAB 3: Editar/Eliminar
    with tab3:
        st.subheader("Editar o Eliminar Producto")
        
        df = obtener_productos(conn)
        
        if df.empty:
            st.warning("No hay productos para editar.")
        else:
            # Selector de producto
            productos_dict = {f"{row['id']} - {row['nombre']}": row['id'] for _, row in df.iterrows()}
            producto_seleccionado = st.selectbox(
                "Selecciona un producto",
                options=list(productos_dict.keys())
            )
            
            if producto_seleccionado:
                id_seleccionado = productos_dict[producto_seleccionado]
                producto_actual = df[df['id'] == id_seleccionado].iloc[0]
                
                st.markdown("---")
                
                # Formulario de edición
                with st.form("form_editar"):
                    st.markdown("**Editar Información del Producto**")
                    
                    nombre_edit = st.text_input("Nombre", value=producto_actual['nombre'])
                    marca_edit = st.text_input("Marca", value=producto_actual['marca'])
                    
                    categorias = ['Refrigeración', 'Lavado', 'Cocina', 'Climatización', 'Limpieza', 'Otro']
                    categoria_edit = st.selectbox(
                        "Categoría",
                        categorias,
                        index=categorias.index(producto_actual['categoria']) if producto_actual['categoria'] in categorias else 0
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        precio_edit = st.number_input(
                            "Precio ($)",
                            min_value=0.0,
                            value=float(producto_actual['precio']),
                            step=1000.0,
                            format="%.2f"
                        )
                    with col2:
                        stock_edit = st.number_input(
                            "Stock",
                            min_value=0,
                            value=int(producto_actual['stock']),
                            step=1
                        )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    with col_b:
                        eliminar = st.form_submit_button("🗑️ Eliminar Producto", use_container_width=True, type="secondary")
                    
                    if guardar:
                        if nombre_edit and marca_edit and precio_edit > 0:
                            editar_producto(conn, id_seleccionado, nombre_edit, marca_edit, categoria_edit, precio_edit, stock_edit)
                            st.success("✅ Producto actualizado exitosamente!")
                            st.rerun()
                        else:
                            st.error("❌ Por favor completa todos los campos correctamente.")
                    
                    if eliminar:
                        eliminar_producto(conn, id_seleccionado)
                        st.success("✅ Producto eliminado exitosamente!")
                        st.rerun()

# Función principal
def main():
    # Inicializar session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Inicializar base de datos
    conn = init_db()
    
    # Mostrar página según estado de sesión
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar con información del usuario
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
            st.markdown("### 📊 Sistema de Gestión")
            st.info("Gestiona tu inventario de electrodomésticos de manera eficiente.")
            
            # Información de contacto del local
            if TELEFONO_LOCAL or DIRECCION_LOCAL:
                st.markdown("---")
                st.markdown("### 📞 Contacto")
                if TELEFONO_LOCAL:
                    st.markdown(f"**Tel:** {TELEFONO_LOCAL}")
                if DIRECCION_LOCAL:
                    st.markdown(f"**Dir:** {DIRECCION_LOCAL}")
        
        # Mostrar panel según rol
        if st.session_state.user_role == "vendedor":
            panel_vendedor(conn)
        elif st.session_state.user_role == "admin":
            panel_administrador(conn)
    
    conn.close()

if __name__ == "__main__":
    main()