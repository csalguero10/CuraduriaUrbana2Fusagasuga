"""Consolidado de trámites de la Curaduría — app Streamlit."""

from __future__ import annotations

import hmac
import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import ORDEN_TIPOS, cargar_excel

st.set_page_config(
    page_title="Consolidado Curaduría",
    page_icon="🏗️",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
COLORES = px.colors.qualitative.Safe + px.colors.qualitative.Pastel


# ---------------------------------------------------------------------------
# 1. Contraseña
# ---------------------------------------------------------------------------
def verificar_contrasena() -> bool:
    """Devuelve True si el usuario ingresó la contraseña definida en secrets."""
    if st.session_state.get("autenticado", False):
        return True

    if "password" not in st.secrets:
        st.error(
            "No hay contraseña configurada. Agrega `password = \"...\"` en "
            "`.streamlit/secrets.toml` (local) o en *Settings → Secrets* (Streamlit Cloud)."
        )
        st.stop()

    def _validar():
        ingresada = st.session_state.get("pwd", "")
        if hmac.compare_digest(
            ingresada.encode("utf-8"), str(st.secrets["password"]).encode("utf-8")
        ):
            st.session_state["autenticado"] = True
            del st.session_state["pwd"]  # no guardar la contraseña
        else:
            st.session_state["autenticado"] = False
            st.session_state["intento_fallido"] = True

    st.title("🔒 Consolidado Curaduría")
    st.text_input("Contraseña", type="password", key="pwd", on_change=_validar)
    if st.session_state.get("intento_fallido"):
        st.error("Contraseña incorrecta.")
    return False


if not verificar_contrasena():
    st.stop()


# ---------------------------------------------------------------------------
# 2. Datos
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando Excel…")
def datos_desde_archivo(ruta: str, modificado: float) -> pd.DataFrame:
    return cargar_excel(ruta)


@st.cache_data(show_spinner="Cargando Excel…")
def datos_desde_bytes(contenido: bytes) -> pd.DataFrame:
    return cargar_excel(contenido)


def obtener_datos() -> pd.DataFrame | None:
    excels = sorted(DATA_DIR.glob("*.xlsx"))
    subido = st.sidebar.file_uploader(
        "Reemplazar con otro Excel (opcional)",
        type=["xlsx"],
        help="Debe tener una hoja por año (2021, 2022…) con las mismas columnas.",
    )
    if subido is not None:
        return datos_desde_bytes(subido.getvalue())
    if excels:
        ruta = excels[0]
        return datos_desde_archivo(str(ruta), ruta.stat().st_mtime)
    return None


df = obtener_datos()

st.title("🏗️ Consolidado de trámites — Curaduría")

if df is None:
    st.info("Sube el Excel consolidado desde la barra lateral para comenzar.")
    st.stop()


# ---------------------------------------------------------------------------
# 3. Filtros
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

anios_disponibles = sorted(df["Año"].unique().tolist())
anios = st.sidebar.multiselect(
    "Año(s)", anios_disponibles, default=anios_disponibles, placeholder="Elige uno o más años"
)

tipos_presentes = [t for t in ORDEN_TIPOS if t in set(df["Tipo de Proyecto"].dropna())]
tipos = st.sidebar.multiselect(
    "Tipo de proyecto", tipos_presentes, default=tipos_presentes,
    placeholder="Elige uno o más tipos",
)

with st.sidebar.expander("Más filtros"):
    estados_presentes = sorted(df["Estado Actual"].dropna().unique().tolist())
    estados = st.multiselect("Estado actual", estados_presentes, placeholder="Todos")
    busqueda = st.text_input(
        "Buscar texto", placeholder="Solicitante, dirección, radicado…",
        help="Busca en radicado, solicitante, dirección, proyecto, matrícula y descripción.",
    )

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

filtro = df["Año"].isin(anios) & df["Tipo de Proyecto"].isin(tipos)
if estados:
    filtro &= df["Estado Actual"].isin(estados)
if busqueda:
    campos = ["Nro Radicado", "Solicitante", "Dirección", "Proyecto", "Matrícula",
              "Descripción del Proyecto"]
    texto = df[campos].fillna("").astype(str).agg(" ".join, axis=1)
    filtro &= texto.str.contains(busqueda, case=False, regex=False)

filtrado = df[filtro].copy()

if filtrado.empty:
    st.warning("No hay registros con esos filtros.")
    st.stop()


# ---------------------------------------------------------------------------
# 4. Indicadores
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros", f"{len(filtrado):,}".replace(",", "."))
c2.metric("Años seleccionados", len(anios))
c3.metric("Tipos de proyecto", filtrado["Tipo de Proyecto"].nunique())
area = filtrado["Área Total"].sum()
c4.metric("Área total (m²)", f"{area:,.0f}".replace(",", "."))


# ---------------------------------------------------------------------------
# 5. Pestañas: tabla, comparativo y gráficos por año
# ---------------------------------------------------------------------------
tab_tabla, tab_comp, tab_anios = st.tabs(["📋 Registros", "📊 Comparativo", "📅 Gráficos por año"])

with tab_tabla:
    columnas_vista = [c for c in filtrado.columns if c != "Trámite"]
    if filtrado["Curso del Proyecto"].isna().all():
        columnas_vista.remove("Curso del Proyecto")

    st.dataframe(
        filtrado[columnas_vista],
        width="stretch",
        hide_index=True,
        height=520,
        column_config={
            "Año": st.column_config.NumberColumn(format="%d"),
            "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Fecha Estado Actual": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Área Total": st.column_config.NumberColumn(format="%.2f m²"),
        },
    )

    d1, d2 = st.columns(2)
    d1.download_button(
        "⬇️ Descargar CSV",
        filtrado[columnas_vista].to_csv(index=False).encode("utf-8-sig"),
        file_name="consolidado_filtrado.csv",
        mime="text/csv",
        width="stretch",
    )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        filtrado[columnas_vista].to_excel(writer, index=False, sheet_name="Filtrado")
    d2.download_button(
        "⬇️ Descargar Excel",
        buffer.getvalue(),
        file_name="consolidado_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

    st.caption("Resumen: número de registros por año y tipo de proyecto")
    resumen = pd.crosstab(
        filtrado["Tipo de Proyecto"].astype(str), filtrado["Año"], margins=True, margins_name="Total"
    )
    resumen.columns = resumen.columns.astype(str)
    resumen.index.name = "Tipo de Proyecto"
    st.dataframe(resumen, width="stretch")

color_map = {t: COLORES[i % len(COLORES)] for i, t in enumerate(ORDEN_TIPOS)}

with tab_comp:
    conteo = (
        filtrado.groupby(["Año", "Tipo de Proyecto"], observed=True)
        .size().reset_index(name="Registros")
    )
    conteo["Año"] = conteo["Año"].astype(str)
    fig = px.bar(
        conteo, x="Año", y="Registros", color="Tipo de Proyecto",
        color_discrete_map=color_map, barmode="stack",
        category_orders={"Tipo de Proyecto": ORDEN_TIPOS},
        title="Registros por año y tipo de proyecto",
    )
    fig.update_layout(legend_title_text="", height=480)
    st.plotly_chart(fig, width="stretch")

    fig2 = px.line(
        conteo, x="Año", y="Registros", color="Tipo de Proyecto", markers=True,
        color_discrete_map=color_map, category_orders={"Tipo de Proyecto": ORDEN_TIPOS},
        title="Evolución por tipo de proyecto",
    )
    fig2.update_layout(legend_title_text="", height=420)
    st.plotly_chart(fig2, width="stretch")

    if len(anios) > 0 and str(max(anios)) == str(max(anios_disponibles)):
        st.caption(
            f"Nota: {max(anios_disponibles)} puede estar incompleto si el año aún no termina."
        )

with tab_anios:
    for anio in sorted(filtrado["Año"].unique()):
        sub = filtrado[filtrado["Año"] == anio]
        st.subheader(f"{anio} — {len(sub):,} registros".replace(",", "."))
        g1, g2 = st.columns(2)

        por_tipo = (
            sub.groupby("Tipo de Proyecto", observed=True).size()
            .reset_index(name="Registros").sort_values("Registros")
        )
        f_tipo = px.bar(
            por_tipo, x="Registros", y="Tipo de Proyecto", orientation="h",
            color="Tipo de Proyecto", color_discrete_map=color_map, text="Registros",
            title="Por tipo de proyecto",
        )
        f_tipo.update_traces(textposition="outside", cliponaxis=False)
        f_tipo.update_layout(showlegend=False, height=360, yaxis_title="")
        g1.plotly_chart(f_tipo, width="stretch", key=f"tipo_{anio}")

        en_anio = sub[sub["Fecha"].dt.year == anio]
        fuera = len(sub) - len(en_anio)
        por_mes = (
            en_anio.assign(Mes=lambda d: d["Fecha"].dt.month.map(dict(enumerate(MESES, 1))))
            .groupby(["Mes", "Tipo de Proyecto"], observed=True).size()
            .reset_index(name="Registros")
        )
        f_mes = px.bar(
            por_mes, x="Mes", y="Registros", color="Tipo de Proyecto",
            color_discrete_map=color_map,
            category_orders={"Tipo de Proyecto": ORDEN_TIPOS, "Mes": MESES},
            title="Radicaciones por mes",
        )
        f_mes.update_layout(showlegend=False, height=360, xaxis_title="")
        g2.plotly_chart(f_mes, width="stretch", key=f"mes_{anio}")
        if fuera:
            g2.caption(f"{fuera} registro(s) de esta hoja tienen fecha de otro año y no aparecen aquí.")

        por_estado = (
            sub["Estado Actual"].fillna("Sin estado").value_counts().reset_index()
        )
        por_estado.columns = ["Estado Actual", "Registros"]
        f_est = px.bar(
            por_estado.sort_values("Registros"), x="Registros", y="Estado Actual",
            orientation="h", text="Registros", title="Por estado actual",
            color_discrete_sequence=["#5B8DB8"],
        )
        f_est.update_traces(textposition="outside", cliponaxis=False)
        f_est.update_layout(height=120 + 30 * len(por_estado), yaxis_title="")
        st.plotly_chart(f_est, width="stretch", key=f"estado_{anio}")
        st.divider()
