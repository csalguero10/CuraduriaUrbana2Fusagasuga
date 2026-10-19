"""Carga y consolida las hojas anuales del Excel en una sola tabla."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Tipos de proyecto: se derivan de la columna "Tramites" (código interno).
# ---------------------------------------------------------------------------
TIPOS_PROYECTO = {
    "licenciaurbanizacion": "Licencias de urbanización",
    "licenciaparcelacion": "Licencias de parcelación",
    "licenciaconstruccion": "Licencias de construcción",
    "reconocimientos": "Reconocimiento de edificaciones existentes",
    "propiedadhorizontal": "Autorización Propiedad Horizontal",
    "conceptosuelo": "Conceptos de uso del suelo",
    "conceptonorma": "Conceptos Norma Urbanística",
    "movimientotierra": "Movimiento de Tierras y aprobación de Piscinas",
    "piscinas": "Movimiento de Tierras y aprobación de Piscinas",
    # Trámites que aparecen en el Excel pero no están en el listado principal
    "subdivisionpredios": "Otros: Subdivisión de predios",
    "ajustedecotas": "Otros: Ajuste de cotas",
    "copiaplanos": "Otros: Copia de planos",
}

# Orden en que se muestran en filtros y gráficos
ORDEN_TIPOS = [
    "Licencias de urbanización",
    "Licencias de parcelación",
    "Licencias de construcción",
    "Reconocimiento de edificaciones existentes",
    "Autorización Propiedad Horizontal",
    "Conceptos de uso del suelo",
    "Conceptos Norma Urbanística",
    "Movimiento de Tierras y aprobación de Piscinas",
    "Otros: Subdivisión de predios",
    "Otros: Ajuste de cotas",
    "Otros: Copia de planos",
    "Sin clasificar",
]

# Las hojas 2021-2024 y 2025-2026 usan nombres de columna distintos.
RENOMBRAR = {
    # Formato 2021-2024
    "Nro Radicado": "Nro Radicado",
    "Tramites": "Trámite",
    "Fecha": "Fecha",
    "Solicitante": "Solicitante",
    "Dirección": "Dirección",
    "Proyecto": "Proyecto",
    "Solicitud": "Solicitud",
    "Modalidad": "Modalidad",
    "Tipo Vivienda": "Tipo Vivienda",
    "Usos": "Usos",
    "Estrato": "Estrato",
    "Matricula": "Matrícula",
    "Ficha": "Ficha",
    "Estado Actual": "Estado Actual",
    "Fecha Estado Actual": "Fecha Estado Actual",
    "Descripción del Proyecto": "Descripción del Proyecto",
    "Area Total": "Área Total",
    # Formato 2025-2026
    "numeroradicado": "Nro Radicado",
    "tramites": "Trámite",
    "fecha": "Fecha",
    "nombresolicitante": "Solicitante",
    "direccionpredio": "Dirección",
    "proyecto_nombre": "Proyecto",
    "solicitud": "Solicitud",
    "modalidad": "Modalidad",
    "tipovivienda": "Tipo Vivienda",
    "usos": "Usos",
    "estrato": "Estrato",
    "matriculas": "Matrícula",
    "fichas": "Ficha",
    "Curso del Proyecto": "Curso del Proyecto",
    "estado_actual": "Estado Actual",
    "estado_actual_fecha": "Fecha Estado Actual",
    "descripcion_proyecto": "Descripción del Proyecto",
    "areatotal": "Área Total",
}

COLUMNAS = [
    "Año",
    "Nro Radicado",
    "Tipo de Proyecto",
    "Trámite",
    "Fecha",
    "Solicitante",
    "Dirección",
    "Proyecto",
    "Solicitud",
    "Modalidad",
    "Tipo Vivienda",
    "Usos",
    "Estrato",
    "Matrícula",
    "Ficha",
    "Curso del Proyecto",
    "Estado Actual",
    "Fecha Estado Actual",
    "Descripción del Proyecto",
    "Área Total",
]


def _limpiar_hoja(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    df = df.rename(columns={c: RENOMBRAR.get(str(c).strip(), str(c).strip()) for c in df.columns})
    df = df.dropna(how="all")

    for col in COLUMNAS:
        if col not in df.columns:
            df[col] = pd.NA

    df["Año"] = anio
    df["Trámite"] = df["Trámite"].astype("string").str.strip().str.lower()
    df["Tipo de Proyecto"] = df["Trámite"].map(TIPOS_PROYECTO).fillna("Sin clasificar")

    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d-%m-%Y", errors="coerce").fillna(
        pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
    )
    df["Fecha Estado Actual"] = pd.to_datetime(df["Fecha Estado Actual"], errors="coerce")
    df["Área Total"] = pd.to_numeric(df["Área Total"], errors="coerce")

    texto = [
        "Nro Radicado", "Solicitante", "Dirección", "Proyecto", "Solicitud", "Modalidad",
        "Tipo Vivienda", "Usos", "Estrato", "Matrícula", "Ficha", "Curso del Proyecto",
        "Estado Actual", "Descripción del Proyecto",
    ]
    for col in texto:
        df[col] = df[col].astype("string").str.strip()

    return df[COLUMNAS]


def cargar_excel(fuente: str | Path | bytes) -> pd.DataFrame:
    """Lee todas las hojas cuyo nombre es un año y las une en un solo DataFrame."""
    if isinstance(fuente, (bytes, bytearray)):
        fuente = io.BytesIO(fuente)

    libro = pd.ExcelFile(fuente)
    hojas = []
    for nombre in libro.sheet_names:
        nombre_limpio = str(nombre).strip()
        if not nombre_limpio.isdigit():
            continue  # ignora hojas que no sean un año
        df = pd.read_excel(libro, sheet_name=nombre, dtype={0: str})
        hojas.append(_limpiar_hoja(df, int(nombre_limpio)))

    if not hojas:
        raise ValueError("El Excel no tiene hojas con nombre de año (ej. 2021, 2022...).")

    datos = pd.concat(hojas, ignore_index=True)
    datos["Tipo de Proyecto"] = pd.Categorical(
        datos["Tipo de Proyecto"], categories=ORDEN_TIPOS, ordered=True
    )
    return datos.sort_values(["Año", "Fecha", "Nro Radicado"]).reset_index(drop=True)
