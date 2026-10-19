# Consolidado Curaduría — App Streamlit

App protegida con contraseña que une las hojas anuales (2021–2026) del Excel
`MAXX Consolidado Cu2Fusa.xlsx` en una sola tabla, permite filtrar por **año** y
**tipo de proyecto**, descargar el resultado y ver gráficos por año.

## Estructura

```
curaduria-app/
├── app.py                        # La app (login, filtros, tabla, gráficos)
├── data_loader.py                # Lee y unifica las hojas del Excel
├── requirements.txt
├── data/
│   └── MAXX_Consolidado_Cu2Fusa.xlsx
├── .streamlit/
│   ├── config.toml               # Tema
│   ├── secrets.toml              # Contraseña (NO se sube a GitHub)
│   └── secrets.toml.example      # Plantilla
└── .gitignore
```

## Tipo de proyecto

El tipo se deriva de la columna `Tramites` del Excel:

| Código en el Excel | Tipo de proyecto |
|---|---|
| licenciaurbanizacion | Licencias de urbanización |
| licenciaparcelacion | Licencias de parcelación |
| licenciaconstruccion | Licencias de construcción |
| reconocimientos | Reconocimiento de edificaciones existentes |
| propiedadhorizontal | Autorización Propiedad Horizontal |
| conceptosuelo | Conceptos de uso del suelo |
| conceptonorma | Conceptos Norma Urbanística |
| movimientotierra, piscinas | Movimiento de Tierras y aprobación de Piscinas |
| subdivisionpredios | Otros: Subdivisión de predios |
| ajustedecotas | Otros: Ajuste de cotas |
| copiaplanos | Otros: Copia de planos |

Para cambiar nombres o agrupaciones, edita `TIPOS_PROYECTO` en `data_loader.py`.

## Probar en tu computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

La contraseña está en `.streamlit/secrets.toml`. Cámbiala antes de publicar.

## Publicar en Streamlit Community Cloud

1. Crea el repositorio en GitHub como **Private** (recomendado: el Excel tiene
   nombres de solicitantes y direcciones; la contraseña protege la app, pero no
   el archivo dentro de un repositorio público).
2. Sube la carpeta. Verifica que `.streamlit/secrets.toml` **no** quedó en el repo.
3. En share.streamlit.io → **Create app** → elige el repo, rama `main` y archivo `app.py`.
4. En **Advanced settings → Secrets** pega:
   ```toml
   password = "tu-contraseña"
   ```
5. Deploy. Puedes cambiar la contraseña después en *App → Settings → Secrets*.

## Actualizar los datos

- Reemplaza el archivo en `data/` (mismo formato: una hoja por año) y haz commit, **o**
- Usa "Reemplazar con otro Excel" en la barra lateral (solo para esa sesión).

Si prefieres no guardar el Excel en GitHub, borra la carpeta `data/`: la app pedirá
subir el archivo después de ingresar la contraseña.
