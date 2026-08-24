import json
from pathlib import Path


# =========================================================
# CONFIGURACIÓN
# =========================================================

ARCHIVO_NOTICIAS = Path("data/noticias.json")


# =========================================================
# COMPROBAR ARCHIVO
# =========================================================

if not ARCHIVO_NOTICIAS.exists():

    print("❌ No existe data/noticias.json")
    raise SystemExit(1)


# =========================================================
# LEER NOTICIAS
# =========================================================

try:

    with open(
        ARCHIVO_NOTICIAS,
        "r",
        encoding="utf-8"
    ) as archivo:

        noticias = json.load(archivo)

except Exception as error:

    print("❌ Error leyendo noticias.json:")
    print(error)

    raise SystemExit(1)


# =========================================================
# COMPROBACIONES
# =========================================================

if not isinstance(noticias, list):

    print("❌ noticias.json debe contener una lista.")

    raise SystemExit(1)


print("🤖 Automatización de Azulones News")
print("----------------------------------")
print(f"📰 Noticias encontradas: {len(noticias)}")


for noticia in noticias:

    titulo = noticia.get(
        "titulo",
        "Sin título"
    )

    print(f"• {titulo}")


# =========================================================
# GUARDAR
# =========================================================

with open(
    ARCHIVO_NOTICIAS,
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(
        noticias,
        archivo,
        ensure_ascii=False,
        indent=2
    )


print("----------------------------------")
print("✅ noticias.json comprobado correctamente.")