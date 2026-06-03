import streamlit as st
import pandas as pd

# 1. Configuración de página
st.set_page_config(page_title="Calculadora Forward", page_icon="🌾", layout="centered")

# --- LÓGICA MATEMÁTICA UNIFICADA ---
def calcular_ambos_metodos(valor_futuro, tna_porcentaje, dias):
    """Calcula y compara el descuento lineal (TNA) y exponencial (TEA)."""
    tna = tna_porcentaje / 100.0
    
    # Método 1: Exponencial (TEA) - Tu primer script (El correcto/recomendado)
    tea = (1 + tna / 365) ** 365 - 1
    factor_exp = (1 + tea) ** (dias / 365)
    vp_tea = valor_futuro / factor_exp
    costo_tea = valor_futuro - vp_tea
    
    # Método 2: Lineal (TNA) - Tu segundo script (El comercial tradicional)
    factor_lin = 1 + tna * (dias / 365)
    vp_tna = valor_futuro / factor_lin
    costo_tna = valor_futuro - vp_tna
    
    return {
        "TEA": {"vp": vp_tea, "costo": costo_tea, "tea_real": tea * 100},
        "TNA": {"vp": vp_tna, "costo": costo_tna}
    }

def simular_tasas(valor_futuro, tna_base, dias):
    """Genera la tabla de simulación de escenarios basada en el segundo script."""
    tasas = [tna_base * m for m in (0.50, 0.75, 1.00, 1.25, 1.50)]
    resultados = []
    
    for t in tasas:
        res = calcular_ambos_metodos(valor_futuro, t, dias)
        resultados.append({
            "TNA Base (%)": t,
            "Monto a Cobrar ($)": res["TEA"]["vp"],
            "Costo Financiero ($)": res["TEA"]["costo"],
            "TEA Equivalente (%)": res["TEA"]["tea_real"]
        })
    return pd.DataFrame(resultados)

# --- INTERFAZ WEB STREAMLIT ---
st.title("🌾 Descuento de Contratos Forward")
st.markdown("Herramienta de liquidación y simulación de escenarios financieros.")

# Cajas de Inputs
st.subheader("1. Datos del Contrato")
col1, col2, col3 = st.columns(3)
with col1:
    monto_contrato = st.number_input("Valor Futuro ($)", min_value=0.0, value=10000000.0, step=100000.0)
with col2:
    tna_descuento = st.number_input("TNA de descuento (%)", min_value=0.0, value=60.0, step=1.0)
with col3:
    dias_plazo = st.number_input("Días al vencimiento", min_value=1, value=90, step=1)

st.markdown("---")

# Botón de acción
if st.button("Calcular Liquidación", type="primary", use_container_width=True):
    
    # Ejecutamos el motor de cálculo
    resultados = calcular_ambos_metodos(monto_contrato, tna_descuento, dias_plazo)
    
    st.subheader("2. Resultados en $t_0$ (Cálculo Racional - TEA)")
    
    # Tarjetas visuales
    res1, res2, res3 = st.columns(3)
    res1.metric(label="💰 Monto a Cobrar Hoy", value=f"${resultados['TEA']['vp']:,.2f}")
    res2.metric(label="📉 Interés Descontado", value=f"${resultados['TEA']['costo']:,.2f}")
    res3.metric(label="📊 TEA Real Aplicada", value=f"{resultados['TEA']['tea_real']:.2f}%")
    
    # El "As bajo la manga": Comparamos contra el descuento común
    diferencia_a_favor = resultados['TEA']['vp'] - resultados['TNA']['vp']
    st.info(f"💡 **Dato clave para negociación:** Al valuar el contrato usando la capitalización correcta (TEA) en lugar del descuento lineal comercial, el cliente recibe **${diferencia_a_favor:,.2f} extra** de liquidez hoy.")

    st.markdown("---")
    
    # Mostramos la tabla de simulación
    st.subheader("3. Simulación de Escenarios")
    st.markdown("Impacto en la liquidación si la TNA de mercado se mueve:")
    
    df_simulacion = simular_tasas(monto_contrato, tna_descuento, dias_plazo)
    
    # Le damos un formato elegante a los números de la tabla
    st.dataframe(
        df_simulacion.style.format({
            "TNA Base (%)": "{:.2f}%",
            "Monto a Cobrar ($)": "${:,.2f}",
            "Costo Financiero ($)": "${:,.2f}",
            "TEA Equivalente (%)": "{:.2f}%"
        }),
        use_container_width=True,
        hide_index=True
    )