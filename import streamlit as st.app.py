"""
Calculadora de Contratos Forward Agrícolas
==========================================
App Streamlit unificada con dos módulos:
  1. Descuento de contratos (Nera / factoring)
  2. Tasa implícita entre precio spot y forward
"""

import streamlit as st
import pandas as pd


# ── Lógica de cálculo ────────────────────────────────────────────────────────

def calcular_descuento(valor_futuro: float, tna: float, dias: int) -> dict:
    factor = 1 + tna * (dias / 365)
    valor_presente = valor_futuro / factor
    interes = valor_futuro - valor_presente
    tea = (factor ** (365 / dias)) - 1
    return {
        "valor_futuro": valor_futuro,
        "valor_presente": valor_presente,
        "interes_descontado": interes,
        "porcentaje_descontado": (interes / valor_futuro) * 100,
        "tna": tna,
        "tea": tea,
        "dias": dias,
        "factor_descuento": factor,
    }


def calcular_tasa_implicita(precio_spot: float, precio_forward: float, dias: int) -> dict:
    ratio = precio_forward / precio_spot
    tasa_directa = ratio - 1
    tna = tasa_directa * (365 / dias)
    tea = ratio ** (365 / dias) - 1
    return {
        "precio_spot": precio_spot,
        "precio_forward": precio_forward,
        "dias": dias,
        "ratio": ratio,
        "premio_absoluto": precio_forward - precio_spot,
        "tasa_directa": tasa_directa,
        "tna": tna,
        "tea": tea,
    }


def calcular_forward_justo(precio_spot: float, tna: float, dias: int) -> float:
    return precio_spot * (1 + tna * dias / 365)


# ── Configuración de la app ──────────────────────────────────────────────────

st.set_page_config(
    page_title="Forward Agrícola",
    page_icon="🌾",
    layout="wide",
)

st.title("🌾 Calculadora de Contratos Forward Agrícolas")
st.caption("Herramienta interna — Corredora de granos")

tab1, tab2 = st.tabs(["💵 Descuento de contrato", "📊 Tasa implícita spot / forward"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Descuento de contrato (Nera / factoring)
# ════════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Descuento de contrato forward")
    st.markdown(
        "Dado un contrato a cobrar en el futuro, calculá el monto que percibís hoy "
        "descontando a una TNA dada. **VP = VF / (1 + TNA × días/365)**"
    )
    st.divider()

    col_inp, col_res = st.columns([1, 1], gap="large")

    with col_inp:
        vf = st.number_input(
            "Monto del contrato — valor futuro ($)",
            min_value=1.0,
            value=10_000_000.0,
            step=100_000.0,
            format="%.2f",
        )
        tna_pct = st.number_input(
            "Tasa de descuento (TNA %)",
            min_value=0.1,
            max_value=500.0,
            value=60.0,
            step=0.5,
            format="%.2f",
        )
        tna_pct = st.slider("", min_value=0.1, max_value=300.0, value=tna_pct, step=0.5, label_visibility="collapsed")
        dias_d = st.number_input(
            "Días al vencimiento",
            min_value=1,
            max_value=730,
            value=90,
            step=1,
        )

    tna = tna_pct / 100
    res = calcular_descuento(vf, tna, int(dias_d))

    with col_res:
        st.metric("Monto a percibir hoy (t₀)", f"$ {res['valor_presente']:,.2f}")
        st.metric("Interés descontado", f"$ {res['interes_descontado']:,.2f}", delta=f"-{res['porcentaje_descontado']:.2f}%", delta_color="inverse")
        st.metric("TEA equivalente", f"{res['tea'] * 100:.2f}%")

        st.markdown("---")
        st.markdown(f"""
**Detalle del cálculo**
| Concepto | Valor |
|---|---|
| Valor futuro | $ {res['valor_futuro']:,.2f} |
| Días | {res['dias']} |
| TNA | {res['tna'] * 100:.2f}% |
| Factor de descuento | {res['factor_descuento']:.6f} |
| Monto presente | $ {res['valor_presente']:,.2f} |
| Interés (costo Nera) | $ {res['interes_descontado']:,.2f} |
| % descontado | {res['porcentaje_descontado']:.2f}% |
| TEA | {res['tea'] * 100:.2f}% |
""")

    st.divider()
    st.markdown("#### Simulación de escenarios — distintas TNA")

    multiplicadores = [0.50, 0.75, 1.00, 1.25, 1.50]
    filas = []
    for m in multiplicadores:
        t = tna * m
        r = calcular_descuento(vf, t, int(dias_d))
        filas.append({
            "TNA": f"{t * 100:.2f}%",
            "Monto presente ($)": f"{r['valor_presente']:,.2f}",
            "Descuento ($)": f"{r['interes_descontado']:,.2f}",
            "% descontado": f"{r['porcentaje_descontado']:.2f}%",
            "TEA": f"{r['tea'] * 100:.2f}%",
        })

    df_sim = pd.DataFrame(filas)
    st.dataframe(df_sim, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Tasa implícita spot / forward
# ════════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Tasa implícita entre precio spot y forward")
    st.markdown(
        "Dado el precio spot y el precio forward, calculá qué tasa de interés "
        "está implícita en el spread. "
        "**TNA = (PF/PS − 1) × 365/días**"
    )
    st.divider()

    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        moneda = st.selectbox("Moneda / unidad", ["USD/ton", "ARS/ton", "USD", "ARS"])
        spot = st.number_input(
            f"Precio spot ({moneda})",
            min_value=0.01,
            value=280.00,
            step=1.0,
            format="%.2f",
        )
        fwd = st.number_input(
            f"Precio forward ({moneda})",
            min_value=0.01,
            value=295.00,
            step=1.0,
            format="%.2f",
        )
        dias_t = st.number_input(
            "Días al vencimiento",
            min_value=1,
            max_value=730,
            value=90,
            step=1,
            key="dias_tab2",
        )

    ri = calcular_tasa_implicita(spot, fwd, int(dias_t))
    contango = ri["tasa_directa"] >= 0
    situacion = "🟢 CONTANGO (forward > spot)" if contango else "🔴 BACKWARDATION (forward < spot)"

    with col_b:
        st.markdown(f"**Situación de mercado:** {situacion}")
        st.metric("Tasa directa del período", f"{ri['tasa_directa'] * 100:+.4f}%")
        st.metric("TNA implícita", f"{ri['tna'] * 100:+.4f}%")
        st.metric("TEA implícita", f"{ri['tea'] * 100:+.4f}%")
        st.metric("Premio / descuento absoluto", f"{moneda.split('/')[0]} {ri['premio_absoluto']:+,.2f}")

    st.divider()

    # Comparación con tasa de referencia
    st.markdown("#### Comparación con tasa de referencia")
    col_ref1, col_ref2 = st.columns([1, 2], gap="large")

    with col_ref1:
        usar_ref = st.toggle("Activar comparación", value=False)
        tna_ref_pct = st.number_input(
            "TNA de referencia (%)",
            min_value=0.1,
            max_value=500.0,
            value=60.0,
            step=0.5,
            format="%.2f",
            disabled=not usar_ref,
        )

    if usar_ref:
        tna_ref = tna_ref_pct / 100
        fwd_justo = calcular_forward_justo(spot, tna_ref, int(dias_t))
        diferencia = fwd - fwd_justo
        spread_tasas = (ri["tna"] - tna_ref) * 100

        with col_ref2:
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Forward justo (ref)", f"{moneda.split('/')[0]} {fwd_justo:,.2f}")
            col_r2.metric("Forward de mercado", f"{moneda.split('/')[0]} {fwd:,.2f}")

            if abs(diferencia) < 0.01:
                label = "Precio justo ✅"
            elif diferencia > 0:
                label = "Forward CARO vs. ref ⚠️"
            else:
                label = "Forward BARATO vs. ref 📉"

            col_r3.metric(
                label,
                f"{moneda.split('/')[0]} {diferencia:+,.2f}",
                delta=f"Spread tasas: {spread_tasas:+.2f}%",
                delta_color="inverse" if diferencia > 0 else "normal",
            )

    st.divider()

    # Sensibilidad por plazo
    st.markdown("#### Sensibilidad por plazo — mismo spread")
    plazos = [30, 60, 90, 120, 150, 180, 270, 360]
    filas_plazos = []
    for d in plazos:
        r = calcular_tasa_implicita(spot, fwd, d)
        filas_plazos.append({
            "Días": d,
            "Tasa directa": f"{r['tasa_directa'] * 100:.4f}%",
            "TNA implícita": f"{r['tna'] * 100:.4f}%",
            "TEA implícita": f"{r['tea'] * 100:.4f}%",
        })

    df_plazos = pd.DataFrame(filas_plazos)
    st.dataframe(df_plazos, use_container_width=True, hide_index=True)
