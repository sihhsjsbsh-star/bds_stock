import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ========== CONFIGURACIÓN DEL LOCAL ==========
NOMBRE_LOCAL = "BDS Electrodomésticos"
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
    .stButton>button { width: 100%; }
    .producto-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .stock-badge {
        padding: 5px 10px;
        border-radius: 5px;
        background-color: #4caf50;
        color: white;
        font-weight: bold;
    }
    .stock-bajo { background-color: #f44336; }
</style>
""", unsafe_allow_html=True)

# Conexión con Google Sheets
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# Leer productos
@st.cache_data(ttl=60)
def leer_productos():
    conn = get_connection()
    # Leemos la hoja PRODUCTOS
    df = conn.read(worksheet="PRODUCTOS")
    df = df.dropna(how='all')
    return df

# Leer ventas
@st.cache_data(ttl=60)
def leer_ventas():
    conn = get_connection()
    try:
        df = conn.read(worksheet="VENTAS")
        df = df.dropna(how='all')
        return df
    except:
        return pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])

# Guardar productos
def guardar_productos(df):
    conn = get_connection()
    conn.update(worksheet="PRODUCTOS", data=df)
    st.cache_data.clear()

# Registrar venta
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

# Actualizar stock
def actualizar_stock(df_productos, producto_nombre, cantidad_vendida):
    mask = df_productos['PRODUCTO'] == producto_nombre
    # Restamos al stock actual
    stock_actual = int(df_productos.loc[mask, 'STOCK'].iloc[0])
    nuevo_stock = stock_actual - cantidad_vendida
    df_productos.loc[mask, 'STOCK'] = nuevo_stock
    guardar_productos(df_productos)

# --- PÁGINAS ---

def login_page():
    st.title(f"🏪 {NOMBRE_LOCAL}")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Iniciar Sesión")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            if usuario == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.rerun()
            elif usuario == "vendedor" and password == "ventas123":
                st.session_state.logged_in = True
                st.session_state.user_role = "vendedor"
                st.rerun()
            else:
                st.error("Datos incorrectos")

def panel_vendedor():
    st.title("🛒 Realizar Venta")
    try:
        df = leer_productos()
    except Exception as e:
        st.error(f"Error leyendo la hoja: {e}")
        return

    busqueda = st.text_input("🔍 Buscar Producto (Escribe marca o modelo)")
    
    if busqueda:
        # Filtramos por lo que escriba el usuario
        df_filtrado = df[
            df['PRODUCTO'].str.contains(busqueda, case=False, na=False) | 
            df['MARCA'].str.contains(busqueda, case=False, na=False)
        ]
    else:
        df_filtrado = df

    if not df_filtrado.empty:
        producto_elegido = st.selectbox("Selecciona el producto:", df_filtrado['PRODUCTO'].unique())
        
        # Datos del producto elegido
        info = df[df['PRODUCTO'] == producto_elegido].iloc[0]
        stock = int(info['STOCK'])
        
        st.info(f"📦 Stock Disponible: **{stock}** unidades")
        
        if stock > 0:
            colA, colB = st.columns(2)
            with colA:
                cantidad = st.number_input("Cantidad", min_value=1, max_value=stock, value=1)
            with colB:
                tipo_pago = st.selectbox("Forma de Pago", ["CONTADO", "12 CUOTAS", "6 CUOTAS"])
            
            # Calcular precio
            precio = float(info[tipo_pago])
            total = precio * cantidad
            
            st.metric("Total a Cobrar", f"₲ {total:,.0f}")
            
            if st.button("✅ CONFIRMAR VENTA", type="primary"):
                actualizar_stock(df, producto_elegido, cantidad)
                registrar_venta(st.session_state.user_role, producto_elegido, cantidad, tipo_pago, total)
                st.success("¡Venta registrada y Stock descontado!")
                import time
                time.sleep(2)
                st.rerun()
        else:
            st.error("⚠️ PRODUCTO AGOTADO")

def panel_admin():
    st.title("⚙️ Panel Administrador")
    tab1, tab2 = st.tabs(["📦 Inventario", "💰 Historial Ventas"])
    
    with tab1:
        df = leer_productos()
        st.write("Edita el stock o precios aquí y dale a Guardar:")
        df_editado = st.data_editor(df, num_rows="dynamic")
        
        if st.button("💾 Guardar Cambios en Google Sheets"):
            guardar_productos(df_editado)
            st.success("¡Guardado!")
            
    with tab2:
        st.write("Historial de movimientos:")
        df_ventas = leer_ventas()
        st.dataframe(df_ventas)

# --- MAIN ---
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.write(f"Usuario: **{st.session_state.user_role}**")
            if st.button("Cerrar Sesión"):
                st.session_state.logged_in = False
                st.rerun()
        
        if st.session_state.user_role == "admin":
            panel_admin()
        else:
            panel_vendedor()

if __name__ == "__main__":
    main()
