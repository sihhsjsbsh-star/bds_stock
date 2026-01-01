import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(
    page_title="Sistema de Stock",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes
NOMBRE_LOCAL = "BDS Electrodomésticos"
TELEFONO_LOCAL = "+595 982 627824"

# Usuarios
USUARIOS = {
    "Rosana": {"pass": "bdse1975", "rol": "admin", "nombre": "Rosana Da Silva"},
    "vendedor": {"pass": "ventas123", "rol": "vendedor", "nombre": "Vendedor Caja"}
}

# ==========================================
# ESTILOS CSS (DISEÑO TIPO APP MÓVIL)
# ==========================================
st.markdown("""
<style>
    /* Estilo General */
    .stApp { background-color: #f8f9fa; }
    
    /* Barra de Búsqueda Flotante */
    .search-box {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* Tarjetas de Producto */
    .product-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border-left: 5px solid #1f77b4;
        transition: transform 0.2s;
    }
    
    .product-title {
        font-size: 16px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    
    .product-brand {
        font-size: 12px;
        color: #7f8c8d;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .price-tag {
        font-size: 22px;
        font-weight: 800;
        color: #e67e22; /* Naranja tipo Amazon */
        margin: 8px 0;
    }
    
    .stock-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    
    .stock-low {
        background-color: #ffebee;
        color: #c62828;
    }

    /* Botones grandes para celular */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXIÓN CON GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def leer_datos(hoja):
    conn = get_connection()
    try:
        df = conn.read(worksheet=hoja)
        return df.dropna(how='all')
    except:
        return pd.DataFrame() # Retorna vacío si falla

def guardar_datos(hoja, df):
    conn = get_connection()
    conn.update(worksheet=hoja, data=df)
    st.cache_data.clear()

# ==========================================
# LÓGICA DE NEGOCIO
# ==========================================
def registrar_venta(usuario, producto, cantidad, pago, total):
    df_ventas = leer_datos("VENTAS")
    if df_ventas.empty:
        df_ventas = pd.DataFrame(columns=['FECHA', 'VENDEDOR', 'PRODUCTO', 'CANTIDAD', 'TIPO_PAGO', 'MONTO_TOTAL'])
    
    nueva_linea = pd.DataFrame([{
        'FECHA': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'VENDEDOR': usuario,
        'PRODUCTO': producto,
        'CANTIDAD': cantidad,
        'TIPO_PAGO': pago,
        'MONTO_TOTAL': total
    }])
    
    df_final = pd.concat([df_ventas, nueva_linea], ignore_index=True)
    guardar_datos("VENTAS", df_final)

def descontar_stock(producto_nombre, cantidad):
    df = leer_datos("PRODUCTOS")
    # Limpiamos espacios por si acaso
    df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip()
    
    mask = df['PRODUCTO'] == producto_nombre
    if mask.any():
        idx = df.index[mask][0]
        stock_actual = int(df.at[idx, 'STOCK'])
        df.at[idx, 'STOCK'] = max(0, stock_actual - cantidad)
        guardar_datos("PRODUCTOS", df)
        return True
    return False

# ==========================================
# INTERFAZ: TARJETA DE PRODUCTO
# ==========================================
def mostrar_tarjeta(row):
    # Cálculos visuales
    stock = int(row.get('STOCK', 0))
    stock_style = "stock-low" if stock < 5 else "stock-badge"
    stock_icon = "🔴" if stock < 5 else "✅"
    
    # Contenedor visual (HTML puro para velocidad)
    st.markdown(f"""
    <div class="product-card">
        <div class="product-brand">{row['MARCA']}</div>
        <div class="product-title">{row['PRODUCTO']}</div>
        <div class="price-tag">₲ {float(row['CONTADO']):,.0f}</div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#666;">
            <span>6x ₲ {float(row['6 CUOTAS']):,.0f}</span>
            <span>12x ₲ {float(row['12 CUOTAS']):,.0f}</span>
        </div>
        <div style="margin-top:10px;">
            <span class="{stock_style}">{stock_icon} Stock: {stock}</span>
            <span style="float:right; color:#888; font-size:12px;">{row['CATEGORIA']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Botón de acción (Streamlit nativo para funcionalidad)
    if stock > 0:
        if st.button(f"🛒 VENDER", key=f"btn_{row['PRODUCTO']}"):
            st.session_state.producto_seleccionado = row.to_dict()
            st.rerun()
    else:
        st.button("🚫 AGOTADO", disabled=True, key=f"btn_{row['PRODUCTO']}")

# ==========================================
# PANTALLAS
# ==========================================
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,8,1])
    with col2:
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("INGRESAR", type="primary"):
            if user in USUARIOS and USUARIOS[user]['pass'] == password:
                st.session_state.logged_in = True
                st.session_state.user_info = USUARIOS[user]
                st.rerun()
            else:
                st.error("Datos incorrectos")

def pantalla_vendedor():
    # Header
    st.markdown(f"**👤 {st.session_state.user_info['nombre']}** | 📞 {TELEFONO_LOCAL}")
    if st.button("Salir", key="logout_top"):
        st.session_state.logged_in = False
        st.rerun()
    
    # MODAL DE VENTA (Si se seleccionó un producto)
    if 'producto_seleccionado' in st.session_state and st.session_state.producto_seleccionado:
        prod = st.session_state.producto_seleccionado
        with st.container(border=True):
            st.markdown(f"### 📝 Finalizar Venta: {prod['PRODUCTO']}")
            
            c1, c2 = st.columns(2)
            cantidad = c1.number_input("Cantidad", min_value=1, max_value=int(prod['STOCK']), value=1)
            pago = c2.selectbox("Pago", ["CONTADO", "6 CUOTAS", "12 CUOTAS"])
            
            # Calcular total
            precio = float(prod['CONTADO']) if pago == 'CONTADO' else float(prod[pago])
            total = precio * cantidad
            st.markdown(f"<h2 style='color:#2e7d32'>Total: ₲ {total:,.0f}</h2>", unsafe_allow_html=True)
            
            if st.button("✅ CONFIRMAR VENTA", type="primary", use_container_width=True):
                if descontar_stock(prod['PRODUCTO'], cantidad):
                    registrar_venta(st.session_state.user_info['rol'], prod['PRODUCTO'], cantidad, pago, total)
                    st.success("¡Venta Exitosa!")
                    del st.session_state.producto_seleccionado
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error de stock")
            
            if st.button("❌ CANCELAR", use_container_width=True):
                del st.session_state.producto_seleccionado
                st.rerun()
        st.markdown("---")

    # BUSCADOR PRINCIPAL
    df = leer_datos("PRODUCTOS")
    
    st.markdown("### 🔎 Buscar Producto")
    busqueda = st.text_input("Escribe nombre o marca...", placeholder="Ej: Licuadora Tokyo", label_visibility="collapsed")
    
    # Filtros
    c_cat, c_marca = st.columns(2)
    filtro_cat = c_cat.selectbox("Categoría", ["Todas"] + sorted(df['CATEGORIA'].unique().tolist()))
    filtro_marca = c_marca.selectbox("Marca", ["Todas"] + sorted(df['MARCA'].unique().tolist()))

    # Lógica de filtrado
    df_filtrado = df.copy()
    
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['PRODUCTO'].str.contains(busqueda, case=False, na=False) | 
            df_filtrado['MARCA'].str.contains(busqueda, case=False, na=False)
        ]
    
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == filtro_cat]
        
    if filtro_marca != "Todas":
        df_filtrado = df_filtrado[df_filtrado['MARCA'] == filtro_marca]

    # MOSTRAR TARJETAS
    if not df_filtrado.empty:
        st.markdown(f"<small>Encontrados: {len(df_filtrado)}</small>", unsafe_allow_html=True)
        # Mostramos solo los primeros 50 para que no sea lento en el cel
        for idx, row in df_filtrado.head(50).iterrows():
            mostrar_tarjeta(row)
    else:
        st.info("No se encontraron productos.")

def pantalla_admin():
    st.title("Panel Administrador")
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()
        
    tab1, tab2 = st.tabs(["Productos", "Ventas"])
    
    with tab1:
        df = leer_datos("PRODUCTOS")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Guardar Cambios Inventario", type="primary"):
            guardar_datos("PRODUCTOS", edited_df)
            st.success("Guardado")
            
    with tab2:
        st.write("Historial de Ventas")
        df_v = leer_datos("VENTAS")
        st.dataframe(df_v, use_container_width=True)

# ==========================================
# MAIN APP
# ==========================================
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
    else:
        if st.session_state.user_info['rol'] == 'admin':
            pantalla_admin()
        else:
            pantalla_vendedor()

if __name__ == "__main__":
    main()
