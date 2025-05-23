# streamlit run licitaciones_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv('dataset_ok.csv', parse_dates=['Fecha de apertura'])
    return df


df = load_data()

st.title("📊 Análisis de Licitaciones")

# -- Instituciones que licitan --
st.markdown("### 🏢 ¿Qué instituciones licitan más?")

# Agrupar por institución y contar códigos de licitación únicos
top_inst = df.dropna(subset=['Código de licitación']).drop_duplicates(
    subset=['Institución que abrió la licitación', 'Código de licitación']
)
top_inst = top_inst['Institución que abrió la licitación'].value_counts().head(
    10).reset_index()
top_inst.columns = ['Institución', 'Cantidad']

# Gráfico
fig = px.pie(top_inst, names='Institución', values='Cantidad',
             title='Top 10 Instituciones que Abren Licitaciones', hole=0.3)
fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
st.plotly_chart(fig, use_container_width=True)

# -- Época del año --
st.markdown("### 📅 ¿En qué época del año hay más licitaciones?")
lic_unicas = df[['Código de licitación', 'Fecha de apertura']
                ].drop_duplicates().dropna()
lic_unicas['Mes'] = lic_unicas['Fecha de apertura'].dt.month_name()
orden_meses = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
conteo_meses = lic_unicas['Mes'].value_counts().reindex(
    orden_meses).reset_index()
conteo_meses.columns = ['Mes', 'Cantidad']
fig = px.bar(conteo_meses, x='Mes', y='Cantidad', title='Cantidad de Licitaciones por Mes',
             labels={'Cantidad': 'Número de Licitaciones', 'Mes': 'Mes'}, text='Cantidad')
fig.update_traces(marker_color='lightskyblue', textposition='outside')
fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
st.plotly_chart(fig, use_container_width=True)

# -- Filtro por producto --
st.markdown("### 🔍 Filtrar por producto")

producto_sel = st.selectbox(
    "Seleccioná un producto", sorted(df['Producto'].dropna().unique()))

filtrado = df[df['Producto'] == producto_sel]
total_producto = filtrado['Cantidad'].sum()

col1, col2 = st.columns([1, 3])
with col1:
    st.metric(label="Total solicitado",
              value=f"{total_producto:,.0f} unidades")

resumen = (
    filtrado.groupby(
        ['Institución que abrió la licitación', 'Institución Destino'])
    ['Cantidad']
    .sum()
    .reset_index()
    .sort_values(by='Cantidad', ascending=False)
)

resumen.columns = ['Institución que abrió la licitación',
                   'Institución Destino', 'Cantidad Total']
resumen['Cantidad Total'] = resumen['Cantidad Total'].map('{:,.0f}'.format)

# Línea clave para eliminar el índice:
resumen = resumen.reset_index(drop=True)

# Mostrar tabla sin índice
with st.expander("🔎 Ver detalle por institución", expanded=True):
    st.dataframe(resumen, use_container_width=True, hide_index=True)

# Gráfico de barras
fig = px.bar(
    resumen,
    x='Cantidad Total',
    y='Institución que abrió la licitación',
    color='Institución Destino',
    orientation='h',
    text='Cantidad Total',
    title=f"Cantidad total solicitada de '{producto_sel}' por institución"
)
fig.update_traces(textposition='outside', marker_line_width=0.5)
fig.update_layout(
    yaxis={'categoryorder': 'total ascending'},
    xaxis_title='Cantidad Total',
    yaxis_title='',
    margin=dict(l=60, r=30, t=50, b=40),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# -- Productos más pedidos por licitaciones --
st.markdown("### 📦 Top 10 Productos por Cantidad de Licitaciones")
licit_prod = df[['Código de licitación', 'Producto']].drop_duplicates()
top_prod_licit = licit_prod['Producto'].value_counts().head(10).reset_index()
top_prod_licit.columns = ['Producto', 'Cantidad']
fig = px.bar(top_prod_licit, x='Cantidad', y='Producto',
             orientation='h', color='Producto', text='Cantidad')
fig.update_traces(textposition='outside')
fig.update_layout(showlegend=False, margin=dict(l=40, r=40, t=40, b=40))
st.plotly_chart(fig, use_container_width=True)

# -- Productos más pedidos por volumen --
st.markdown("### 📦 Top 10 Productos por Volumen Total Solicitado")
cant_total = df.groupby('Producto')['Cantidad'].sum(
).sort_values(ascending=False).head(10).reset_index()
cant_total.columns = ['Producto', 'Cantidad Total']
df_top = df[df['Producto'].isin(cant_total['Producto'])]
linea_porcentaje = df_top.groupby('Línea de Producto')[
    'Cantidad'].sum().reset_index()
linea_porcentaje['Porcentaje'] = 100 * \
    linea_porcentaje['Cantidad'] / linea_porcentaje['Cantidad'].sum()
col1, col2 = st.columns([2, 1])
with col1:
    fig = px.bar(cant_total, x='Cantidad Total', y='Producto',
                 orientation='h', color='Producto', text='Cantidad Total')
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)
with col2:
    # Distribución por Línea de Producto
    pie_fig = px.pie(linea_porcentaje, values='Porcentaje',
                     names='Línea de Producto', hole=0.4)
    pie_fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(pie_fig, use_container_width=True)

# -- Mapa --
st.markdown("### 🗺️ Mapa de Instituciones que Licitan")
df_geo = pd.read_csv('dataset_ok.csv')
instituciones_geo = df_geo.dropna(subset=['Latitud', 'Longitud']).groupby(
    ['Institución que abrió la licitación', 'Latitud', 'Longitud']).size().reset_index(name='Cantidad_licitaciones')
m = folium.Map(location=[-38.4161, -63.6167], zoom_start=5)
for _, row in instituciones_geo.iterrows():
    folium.CircleMarker(location=[row['Latitud'], row['Longitud']], radius=5 + row['Cantidad_licitaciones'] ** 0.5,
                        popup=f"{row['Institución que abrió la licitación']}<br>Cant: {row['Cantidad_licitaciones']}", color='blue', fill=True, fill_color='blue', fill_opacity=0.6).add_to(m)
col = st.columns([0.1, 0.8, 0.1])[1]
with col:
    st_folium(m, width=700, height=450)


# -- Observaciones del análisis exploratorio --
st.markdown("### 📌 Observaciones del análisis exploratorio")

st.markdown("""
A partir del análisis de las licitaciones, se destacan los siguientes hallazgos clave:

- **📅 Estacionalidad en la demanda**  
  Se identifica un patrón estacional marcado: aproximadamente el **60% de las licitaciones** se concentran en los primeros cuatro meses del año, con picos en **febrero (9 licitaciones)**, **abril (8)** y **enero (4)**. Esto sugiere que la mayoría de las instituciones realizan sus compras durante el primer cuatrimestre, posiblemente en relación con la apertura de presupuestos o planes anuales de adquisición.  
  👉 *Recomendación:* los proveedores pueden enfocar sus esfuerzos comerciales en esta etapa del año para maximizar oportunidades.

- **📦 Productos con mayor frecuencia de licitación**  
  El producto más frecuentemente solicitado es **Fortisip Vainilla botella x 200 ml** con **14 licitaciones**, seguido de **Nutrison Advanced Diason Pack x 1 (10)** y **KAS 1000 lata x 400g (9)**. Estos productos representan en conjunto cerca del **30% del total de licitaciones**, lo que revela una demanda recurrente por parte de distintas instituciones.  
  👉 *Insight:* puede ser conveniente para los fabricantes asegurar disponibilidad continua de estos productos en stock.

- **📊 Volumen total solicitado**  
  Al analizar la cantidad total de unidades licitadas, **KAS 1000 lata x 400g** lidera con **32.694 unidades**, seguido muy de cerca por **Fortisip Vainilla (32.259)** y **Vital AR lata x 400g (30.809)**. Este dato complementa la frecuencia y permite detectar productos que no solo son populares, sino también requeridos en grandes cantidades.  
  👉 *Conclusión:* estos artículos tienen un uso intensivo, probablemente para atención prolongada de pacientes o instituciones de alta rotación.

- **🗺️ Distribución geográfica de las licitaciones**  
  El análisis espacial muestra una fuerte concentración en la **zona central del país**, especialmente en la **Ciudad Autónoma de Buenos Aires** y el **norte del Gran Buenos Aires**. Se registra escasa actividad en el **norte argentino** y prácticamente nula en el **sur**.  
  👉 *Hipótesis:* esto podría estar relacionado con la concentración de infraestructura sanitaria, mayores presupuestos regionales o centralización de procesos de compra.

Este tablero permite a responsables de **compras**, **logística** y **planificación** identificar patrones clave y tomar decisiones basadas en datos concretos, como la optimización de stock, la planificación comercial por estacionalidad y la focalización regional.
""")
