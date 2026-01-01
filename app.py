# -*- coding: utf-8 -*-
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
    stock_actual = int(df_productos.loc[mask, 'STOCK'].iloc[0])
    nuevo_stock = stock_actual - cantidad_vendida
    df_productos.loc[mask, 'STOCK'] = nuevo_stock
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
    
    # Determinar clase y emoji de stock (USANDO CÓDIGOS SEGUROS)
    if stock >= 10:
        stock_class = "stock-alto"
        stock_emoji = ":white_check_mark:"
        stock_texto = "Disponible"
    elif stock >= 5:
        stock_class = "stock-medio"
        stock_emoji = ":warning:"
        stock_texto = f"Quedan {stock}"
    elif stock > 0:
        stock_class = "stock-bajo"
        stock_emoji = ":red_circle:"
        stock_texto = f"¡Solo {stock}!"
    else:
        stock_class
