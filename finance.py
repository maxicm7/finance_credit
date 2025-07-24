import streamlit as st
import pandas as pd

# --- Funciones de Cálculo Financiero ---

def calcular_opcion_1_contado(monto_capital, descuento_pct):
    """Calcula el valor de la opción de pago al contado con descuento."""
    pago_contado = monto_capital * (1 - descuento_pct / 100)
    # El VAN es el mismo pago, ya que está en el momento cero.
    van = pago_contado
    
    df = pd.DataFrame([{
        "Mes": 0,
        "Flujo de Caja (AR$)": pago_contado,
        "Valor Actual (AR$)": van
    }])
    return van, df

def calcular_opcion_2_inflacion(monto_capital, plazo_meses, inflacion_mensual_pct, tasa_descuento_mensual):
    """Calcula el VAN de las cuotas ajustadas por inflación."""
    cuota_capital_base = monto_capital / plazo_meses
    inflacion_mensual = inflacion_mensual_pct / 100
    
    flujos = []
    van = 0
    for mes in range(1, plazo_meses + 1):
        # La cuota se ajusta por la inflación acumulada hasta ese mes
        factor_ajuste = (1 + inflacion_mensual) ** mes
        cuota_ajustada = cuota_capital_base * factor_ajuste
        
        # Traemos esa cuota futura a valor presente
        valor_actual_cuota = cuota_ajustada / ((1 + tasa_descuento_mensual) ** mes)
        
        flujos.append({
            "Mes": mes,
            "Flujo de Caja (AR$)": cuota_ajustada,
            "Valor Actual (AR$)": valor_actual_cuota
        })
        van += valor_actual_cuota
        
    df = pd.DataFrame(flujos)
    return van, df

def calcular_opcion_3_dolar(monto_capital, plazo_meses, tc_inicial, devaluacion_mensual_pct, tasa_descuento_mensual):
    """Calcula el VAN de las cuotas ajustadas por tipo de cambio."""
    capital_en_usd = monto_capital / tc_inicial
    cuota_usd = capital_en_usd / plazo_meses
    devaluacion_mensual = devaluacion_mensual_pct / 100

    flujos = []
    van = 0
    for mes in range(1, plazo_meses + 1):
        # Se proyecta el tipo de cambio para cada mes
        tc_proyectado = tc_inicial * ((1 + devaluacion_mensual) ** mes)
        cuota_en_ars = cuota_usd * tc_proyectado

        # Traemos esa cuota futura a valor presente
        valor_actual_cuota = cuota_en_ars / ((1 + tasa_descuento_mensual) ** mes)
        
        flujos.append({
            "Mes": mes,
            "TC Proyectado": tc_proyectado,
            "Flujo de Caja (AR$)": cuota_en_ars,
            "Valor Actual (AR$)": valor_actual_cuota
        })
        van += valor_actual_cuota
        
    df = pd.DataFrame(flujos)
    return van, df


# --- Interfaz de Usuario con Streamlit ---

st.set_page_config(page_title="Evaluador de Opciones de Cobro", layout="wide")

st.title("💸 Evaluador de Opciones de Cobro de Créditos")
st.markdown("""
Esta herramienta ayuda a comparar diferentes propuestas de pago para un crédito, calculando el **Valor Actual Neto (VAN)** de cada opción.
**La opción con el VAN más alto es la más conveniente para el acreedor (quien cobra).**
""")

# --- Panel de Entradas en la Barra Lateral ---
st.sidebar.header("Parámetros del Crédito y Supuestos")

st.sidebar.subheader("Datos del Crédito")
monto_capital = st.sidebar.number_input(
    "Monto del Crédito Nominal (AR$)", 
    min_value=1000, 
    value=1000000, 
    step=50000,
    format="%d"
)
plazo_meses = 12  # Fijo según el caso de uso

st.sidebar.subheader("Parámetros de las Opciones")
descuento_contado_pct = st.sidebar.slider(
    "Opción 1: Descuento por Pago Contado (%)", 0.0, 25.0, 7.0, 0.5
)
tc_inicial = st.sidebar.number_input(
    "Opción 3: Tipo de Cambio Inicial (AR$/USD)", min_value=1.0, value=950.0, step=1.0
)

st.sidebar.subheader("Supuestos Macroeconómicos (Proyecciones)")
tasa_descuento_anual_pct = st.sidebar.slider(
    "Tasa de Descuento Anual (Costo de Oportunidad %)", 0.0, 300.0, 120.0, 0.01,
    help="Es la tasa de rendimiento que su empresa podría obtener con el dinero (ej. tasa de plazo fijo, caución, etc.). Se usa para traer los flujos futuros a valor de hoy."
)
inflacion_mensual_pct = st.sidebar.slider(
    "Opción 2: Inflación Mensual Promedio Proyectada (%)", 0.0, 30.0, 9.0, 0.01
)
devaluacion_mensual_pct = st.sidebar.slider(
    "Opción 3: Devaluación Mensual Promedio Proyectada (%)", 0.0, 30.0, 5.0, 0.01
)

# --- Lógica Principal y Visualización ---

# Convertir tasas a formato decimal para cálculos
tasa_descuento_mensual = (1 + tasa_descuento_anual_pct / 100)**(1/12) - 1

# Calcular VAN y flujos de cada opción
van1, df1 = calcular_opcion_1_contado(monto_capital, descuento_contado_pct)
van2, df2 = calcular_opcion_2_inflacion(monto_capital, plazo_meses, inflacion_mensual_pct, tasa_descuento_mensual)
van3, df3 = calcular_opcion_3_dolar(monto_capital, plazo_meses, tc_inicial, devaluacion_mensual_pct, tasa_descuento_mensual)

resultados = {
    "Opción 1: Pago Contado": van1,
    "Opción 2: Cuotas + Inflación": van2,
    "Opción 3: Cuotas 'Dólar'": van3,
}

# Encontrar la mejor opción
mejor_opcion = max(resultados, key=resultados.get)

st.header("🏆 Resumen y Recomendación")
st.info(f"**La opción recomendada es: {mejor_opcion}**\n\nPorque genera el mayor Valor Actual Neto (VAN) con los supuestos ingresados.")

# Mostrar los resultados en columnas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Opción 1: Contado", f"AR$ {van1:,.2f}")
with col2:
    st.metric("Opción 2: Inflación", f"AR$ {van2:,.2f}")
with col3:
    st.metric("Opción 3: Dólar", f"AR$ {van3:,.2f}")

st.markdown("---")

# Mostrar el detalle de cada opción en expanders
st.header("🔍 Detalle de Cada Opción")

with st.expander("Opción 1: Pago Contado con Descuento"):
    st.write(f"Se recibe un único pago de **AR$ {van1:,.2f}** en el momento inicial.")
    st.dataframe(df1.style.format({"Flujo de Caja (AR$)": "AR$ {:,.2f}", "Valor Actual (AR$)": "AR$ {:,.2f}"}))

with st.expander("Opción 2: 12 Cuotas ajustadas por Inflación"):
    st.write(f"Total nominal a cobrar: **AR$ {df2['Flujo de Caja (AR$)'].sum():,.2f}**. Valor actual total: **AR$ {van2:,.2f}**.")
    st.dataframe(df2.style.format({
        "Flujo de Caja (AR$)": "AR$ {:,.2f}", 
        "Valor Actual (AR$)": "AR$ {:,.2f}"
    }))

with st.expander("Opción 3: 12 Cuotas ajustadas por Tipo de Cambio (Base Dólar)"):
    st.write(f"Total nominal a cobrar: **AR$ {df3['Flujo de Caja (AR$)'].sum():,.2f}**. Valor actual total: **AR$ {van3:,.2f}**.")
    st.dataframe(df3.style.format({
        "TC Proyectado": "{:,.2f}",
        "Flujo de Caja (AR$)": "AR$ {:,.2f}", 
        "Valor Actual (AR$)": "AR$ {:,.2f}"
    }))
