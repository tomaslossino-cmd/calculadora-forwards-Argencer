"""
Calculadora de Contratos Forward Agrícolas e Inversiones
========================================================
App Streamlit unificada con cuatro módulos:
  1. Estrategia: Spot vs Forward vs Venta Futura/Pago ahora
  2. Tasas disponibles en el mercado
  3. Tasa implícita entre precio spot y forward
  4. Descuento de contratos (Nera / factoring)
"""

import streamlit as st
import pandas as pd
import datetime

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
    page_title="Suite Financiera Agro",
    page_icon="🌾",
    layout="wide",
)

st.title("🌾 Argencer- Herramientas Financieras Interactivas")
st.caption("Herramienta interna — Corredora de granos Argencer")

# Nuevo orden de las pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "⚖️ Estrategia: Spot vs Fwd vs Venta Futura/Pago ahora",
    "📋 Tasas de mercado",
    "📊 Tasa implícita spot / fwd",
    "💵 Descuento de contrato"
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Estrategia: Spot vs Forward vs Venta Futura/Pago ahora
# ════════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("Análisis de Estrategia (En Dólares)")
    st.markdown("Completa los precios y evalua que condicion es la mas favorable")

    st.subheader("1. Datos a completar")
    c1, c2 = st.columns(2)

    with c1:
        p_spot_est = st.number_input("Precio Spot (U$S)", value=318.0, step=1.0)
        p_forward_est = st.number_input("Precio Forward (U$S)", value=338.0, step=1.0)
        p_desc_est = st.number_input("Precio Venta Futura/Pago ahora (U$S)", value=328.0, step=1.0)

    with c2:
        # Lógica para generar los meses futuros y su 1er día hábil automáticamente
        hoy_dt = datetime.date.today()
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        opciones_meses = []
        dicc_fechas = {}

        for i in range(1, 15): # Mostramos 14 meses hacia adelante
            mes_num = hoy_dt.month + i - 1
            year_calc = hoy_dt.year + (mes_num // 12)
            mes_index = mes_num % 12
            nombre_mes = f"{meses_nombres[mes_index]} {year_calc}"
            opciones_meses.append(nombre_mes)

            # Buscamos el primer día del mes
            primer_dia = datetime.date(year_calc, mes_index + 1, 1)
            
            # Ajuste a primer día hábil (salta sábado y domingo)
            if primer_dia.weekday() == 5: # 5 es Sábado
                primer_habil = primer_dia + datetime.timedelta(days=2)
            elif primer_dia.weekday() == 6: # 6 es Domingo
                primer_habil = primer_dia + datetime.timedelta(days=1)
            else:
                primer_habil = primer_dia

            dicc_fechas[nombre_mes] = primer_habil

        # Input de selección de mes
        mes_futuro = st.selectbox("Mes futuro (Entrega)", opciones_meses)
        
        # Cálculos de fechas
        fecha_objetivo = dicc_fechas[mes_futuro]
        dias_plazo_est = (fecha_objetivo - hoy_dt).days

        # Muestra el plazo automático
        st.info(f"📅 **Plazo aproximado:** {dias_plazo_est} días (Calculado automáticamente hasta el 1° día hábil: {fecha_objetivo.strftime('%d/%m/%Y')})")

    st.markdown("---")
    st.subheader("2. Análisis de Tasas Implícitas")
    
    # Cálculos matemáticos (Pase)
    if dias_plazo_est > 0:
        tna_spot_fwd = ((p_forward_est / p_spot_est) - 1) * (365 / dias_plazo_est) * 100
        tna_desc_fwd = ((p_forward_est / p_desc_est) - 1) * (365 / dias_plazo_est) * 100
    else:
        tna_spot_fwd = 0.0
        tna_desc_fwd = 0.0

    p1, p2 = st.columns(2)
    p1.metric("Precio Spot (U$S)", f"U$S {p_spot_est:.2f}")
    p2.metric("Precio Venta Futura/Pago ahora (U$S)", f"U$S {p_desc_est:.2f}")

    st.markdown("<br>", unsafe_allow_html=True) # Espacio sutil

    t1, t2, t3 = st.columns(3)
    
    # Cálculos de diferencias en USD
    pase_fwd_spot = p_forward_est - p_spot_est
    pase_fwd_desc = p_forward_est - p_desc_est
    dif_desc_spot = p_desc_est - p_spot_est
    
    # Se usa delta_color="off" para que el texto salga en un gris profesional
    t1.metric("TNA Implícita Spot vs. Forward", f"{tna_spot_fwd:.2f}%", f"Pase Fwd-Spot: U$S {pase_fwd_spot:.2f}", delta_color="off")
    t2.metric("TNA Implícita Venta Futura/Pago ahora vs. Forward", f"{tna_desc_fwd:.2f}%", f"Pase Fwd-Venta Futura: U$S {pase_fwd_desc:.2f}", delta_color="off")
    t3.metric("Diferencia Venta Futura/Pago ahora vs. Spot", f"U$S {dif_desc_spot:.2f}", "Brecha en dólares", delta_color="off")

    # CONCLUSIÓN INICIAL (Necesidad de Liquidez)
    st.markdown("#### 💡 Conclusión inicial (Si necesitás la plata ahora):")
    if tna_spot_fwd > tna_desc_fwd:
        st.success("✅ **Conviene elegir VENTA FUTURA/PAGO AHORA**. La tasa implícita que pagás por adelantar el forward es menor que el altísimo costo de oportunidad de vender al precio Spot.")
    else:
        st.warning("✅ **Conviene vender SPOT directamente**. El castigo en precio que te hacen por la Venta Futura/Pago ahora es demasiado alto; te rinde más ir directo al mercado Spot físico.")

    st.markdown("---")
    st.subheader("3. Si podés Esperar e Invertir")

    tea_usd_est = st.number_input("TEA/TIR en USD del instrumento disponible (%)", value=6.0, step=0.1)

    # Cálculos de Inversión (Aplicando fórmula de capitalización exponencial a los días exactos)
    estrategia_fwd = p_forward_est
    factor_inv = (1 + (tea_usd_est / 100)) ** (dias_plazo_est / 365)
    
    estrategia_spot = p_spot_est * factor_inv
    estrategia_desc = p_desc_est * factor_inv

    # Títulos dinámicos basados en el mes elegido
    label_fwd = f"Estrategia Forward {mes_futuro}"
    label_spot = f"Venta Spot + Inversión a {mes_futuro}"
    label_desc = f"Venta Futura/Pago ahora + Inversión a {mes_futuro}"

    e1, e2, e3 = st.columns(3)
    e1.metric(label_fwd, f"U$S {estrategia_fwd:.2f}")
    e2.metric(label_spot, f"U$S {estrategia_spot:.2f}")
    e3.metric(label_desc, f"U$S {estrategia_desc:.2f}")

    # CONCLUSIÓN FINAL (Maximizar Capital)
    st.markdown("#### 🏆 Conclusión Final (Si podés esperar e Invertir):")
    
    resultados_est = {
        label_fwd: estrategia_fwd,
        label_spot: estrategia_spot,
        label_desc: estrategia_desc
    }
    
    mejor_estrategia = max(resultados_est, key=resultados_est.get)

    st.success(f"📈 La mejor alternativa comercial y financiera es ir por la **{mejor_estrategia}**, alcanzando un capital proyectado de **U$S {resultados_est[mejor_estrategia]:.2f}**.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Tasas disponibles en el mercado por instrumento (Argencer)
# ════════════════════════════════════════════════════════════════════════════

with tab2:
    from datetime import date

    st.markdown(
        """
        <style>
        .argencer-header {
            background: #1a2e4a;
            border-radius: 10px;
            padding: 18px 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0;
        }
        .argencer-logo-text { color: white; font-size: 26px; font-weight: 700; letter-spacing: 2px; }
        .argencer-sub { color: #a0b4c8; font-size: 11px; letter-spacing: 3px; margin-top: 2px; }
        .argencer-date { background: #2c4260; color: #d0dcea; border-radius: 8px; padding: 8px 18px; font-size: 14px; }
        .seccion-header {
            background: #1a2e4a;
            color: white;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 0;
        }
        .seccion-badge {
            background: #2c4260;
            color: #d0dcea;
            border-radius: 6px;
            padding: 3px 14px;
            font-size: 12px;
            letter-spacing: 1px;
        }
        .col-header {
            background: #e8ede6;
            color: #4a6741;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 8px 20px;
            display: flex;
            justify-content: space-between;
        }
        .instrumento-row {
            background: #f5f3ec;
            border-bottom: 1px solid #e0ddd4;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 16px;
        }
        .instrumento-row:nth-child(even) { background: #eeebe0; }
        .dot-green { color: #4a7a3a; font-size: 12px; margin-right: 10px; }
        .dot-blue  { color: #1a2e4a; font-size: 12px; margin-right: 10px; }
        .dot-gold  { color: #b8860b; font-size: 12px; margin-right: 10px; }
        .tasa-val  { color: #2c3e2d; font-size: 17px; font-weight: 500; }
        .tasa-gold { color: #b8860b; font-size: 17px; font-weight: 500; }
        .footer-bar {
            background: #1a2e4a;
            color: #a0b4c8;
            font-size: 11px;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            border-radius: 0 0 10px 10px;
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    hoy = date.today()
    dias_es = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    meses_es = ["enero","febrero","marzo","abril","mayo","junio",
                "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    fecha_str = f"{dias_es[hoy.weekday()]}, {hoy.day} de {meses_es[hoy.month-1]} de {hoy.year}"

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="argencer-header">
        <div>
            <div class="argencer-logo-text">⊙ &nbsp; ARGENCER</div>
            <div class="argencer-sub">CORREDORES DE CEREALES Y OLEAGINOSAS</div>
        </div>
        <div class="argencer-date">{fecha_str}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── TASAS — editá estos valores cuando cambien las tasas de mercado ─────────
    ars_pf   = "17%"
    ars_cau  = "20% – 22%"
    ars_fmm  = "16,0%"
    ars_frec = "32%"

    usd_pf   = "2%"
    usd_cau  = "2%"
    usd_fmm  = "1,9%"
    usd_fon  = "6,5%"
    usd_lat  = "5% – 6%"
    # ─────────────────────────────────────────────────────────────────────────

    # ── Cuadro estético ───────────────────────────────────────────────────────
    def fila(instrumento, tasa, dot="green", gold=False):
        dot_class = f"dot-{dot}"
        tasa_class = "tasa-gold" if gold else "tasa-val"
        return f"""
        <div class="instrumento-row">
            <span><span class="{dot_class}">●</span>{instrumento}</span>
            <span class="{tasa_class}">{tasa}</span>
        </div>"""

    html_cuadro = (
        '<div style="border-radius:10px; overflow:hidden; border: 1px solid #c8c4b4;">'

        # SECCIÓN ARS
        '<div class="seccion-header">TASAS EN ARS &nbsp; <span class="seccion-badge">PESOS</span></div>'
        '<div class="col-header"><span>INSTRUMENTO</span><span>TNA — RENDIMIENTO ACTUALIZADO</span></div>'
        + fila("Plazo fijo", ars_pf, dot="green")
        + fila("Caución 1/3 días", ars_cau, dot="green")
        + fila("Fondo MM", ars_fmm, dot="green")
        + fila("Fondos recomendados por Argencer", ars_frec, dot="gold", gold=True)

        # SECCIÓN USD
        + '<div class="seccion-header">TASAS EN USD &nbsp; <span class="seccion-badge">DÓLARES</span></div>'
        + '<div class="col-header"><span>INSTRUMENTO</span><span>TNA — RENDIMIENTO ACTUALIZADO</span></div>'
        + fila("Plazo fijo", usd_pf, dot="blue")
        + fila("Caución 1/3 días", usd_cau, dot="blue")
        + fila("Fondo MM", usd_fmm, dot="blue")
        + fila("Fondo de ON", usd_fon, dot="blue")
        + fila("Fondo LATAM", usd_lat, dot="blue")

        # FOOTER
        + '<div class="footer-bar">'
        + '<span>Los rendimientos son orientativos y pueden variar.</span>'
        + '<span>Argencer · Corredores de Cereales y Oleaginosas</span>'
        + '</div>'
        + '</div>'
    )
    st.markdown(html_cuadro, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Tasa implícita spot / forward
# ════════════════════════════════════════════════════════════════════════════

with tab3:
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
    situacion = "🟢 forward > spot" if contango else "🔴 forward < spot"

    with col_b:
        st.markdown(f"**Situación de mercado:** {situacion}")
        st.metric("Tasa directa del período", f"{ri['tasa_directa'] * 100:+.4f}%")
        st.metric("TNA implícita", f"{ri['tna'] * 100:+.4f}%")
        st.metric("TEA implícita", f"{ri['tea'] * 100:+.4f}%")
        st.metric("Pase absoluto", f"{moneda.split('/')[0]} {ri['premio_absoluto']:+,.2f}")

    st.divider()

    # Comparación con tasa de referencia
    st.markdown("#### Comparación con tasa de referencia")
    st.caption(
        "Compará la tasa implícita del forward contra una inversión alternativa (plazo fijo, caución, fondo MM). "
        "La comparación en TNA es válida solo si ambas operaciones tienen el mismo plazo. "
        "La TEA es siempre la métrica correcta para comparar inversiones con distintos plazos o que capitalizan."
    )
    col_ref1, col_ref2 = st.columns([1, 2], gap="large")

    with col_ref1:
        usar_ref = st.toggle("Activar comparación", value=False)
        tasa_ref_pct = st.number_input(
            "Tasa de referencia — TIR / TEA (%)",
            min_value=0.1,
            max_value=500.0,
            value=17.0,
            step=0.5,
            format="%.2f",
            disabled=not usar_ref,
        )

    if usar_ref:
        tasa_ref = tasa_ref_pct / 100
        tna_ref = tasa_ref  # alias para forward justo
        tea_ref = tasa_ref  # la referencia ya es TEA/TIR, no se recapitaliza
        fwd_justo = calcular_forward_justo(spot, tna_ref, int(dias_t))
        diferencia = fwd - fwd_justo

        # Spread en TNA y TEA
        spread_tna = (ri["tna"] - tna_ref) * 100
        spread_tea = (ri["tea"] - tea_ref) * 100

        # Veredicto basado en TEA (métrica correcta)
        if abs(spread_tea) < 0.05:
            veredicto = "Equivalentes en términos efectivos ✅"
            v_color = "normal"
        elif ri["tea"] > tea_ref:
            veredicto = "Forward MEJOR que inversión alternativa 📈"
            v_color = "normal"
        else:
            veredicto = "Inversión alternativa MEJOR que forward 📉"
            v_color = "inverse"

        with col_ref2:
            # Precios
            col_r1, col_r2, col_r3 = st.columns(3)
            mon = moneda.split('/')[0]
            col_r1.metric("Precio spot", f"{mon} {spot:,.2f}")
            col_r2.metric("Forward de mercado", f"{mon} {fwd:,.2f}")
            col_r3.metric("Spot + Inversión (ref TNA)", f"{mon} {fwd_justo:,.2f}",
                         delta=f"{mon} {diferencia:+,.2f}",
                         delta_color="inverse" if diferencia < 0 else "normal")

            st.markdown("---")

            # Tabla comparativa TNA y TEA
            st.markdown("**Comparación de tasas**")
            df_comp = pd.DataFrame([
                {
                    "Métrica":               "TNA implícita forward",
                    "Forward impl.":         f"{ri['tna'] * 100:.4f}%",
                    "Referencia (TIR/TEA)":  "—",
                    "Spread":                "—",
                    "Nota":                  "No comparable directamente con TIR/TEA",
                },
                {
                    "Métrica":               "TEA implícita forward ✅",
                    "Forward impl.":         f"{ri['tea'] * 100:.4f}%",
                    "Referencia (TIR/TEA)":  f"{tasa_ref * 100:.4f}%",
                    "Spread":                f"{spread_tea:+.4f}%",
                    "Nota":                  "Comparación correcta",
                },
            ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            st.info(f"**Conclusión:** {veredicto}")

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


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Descuento de contrato (Nera / factoring)
# ════════════════════════════════════════════════════════════════════════════

with tab4:
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
        tna_pct_val = st.number_input(
            "Tasa de descuento (TNA %)",
            min_value=0.1,
            max_value=500.0,
            value=60.0,
            step=0.5,
            format="%.2f",
        )
        tna_pct = st.slider("", min_value=0.1, max_value=300.0, value=tna_pct_val, step=0.5, label_visibility="collapsed")
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
