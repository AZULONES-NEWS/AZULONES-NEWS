import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


ARCHIVO = Path("data/noticias.json")
MAX_NOTICIAS = 10

FEEDS = [
    "Getafe CF",
    "Getafe fútbol",
    '"Getafe CF" fichajes',
    '"Getafe CF" Bordalás',
]


def limpiar_texto(texto):
    texto = re.sub(r"<[^>]+>", "", texto or "")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def descargar_feed(busqueda):
    params = urllib.parse.urlencode({
        "q": busqueda,
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es"
    })

    url = f"https://news.google.com/rss/search?{params}"

    solicitud = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Azulones-News"
        }
    )

    with urllib.request.urlopen(solicitud, timeout=20) as respuesta:
        return respuesta.read()


def obtener_noticias():
    resultados = []

    for busqueda in FEEDS:

        print(f"🔎 Buscando: {busqueda}")

        try:
            contenido = descargar_feed(busqueda)
            raiz = ET.fromstring(contenido)

        except Exception as error:
            print(f"⚠️ Error en la búsqueda: {error}")
            continue

        for item in raiz.findall(".//item"):

            titulo = limpiar_texto(
                item.findtext("title", "")
            )

            enlace = item.findtext(
                "link",
                ""
            )

            fecha_raw = item.findtext(
                "pubDate",
                ""
            )

            descripcion = limpiar_texto(
                item.findtext(
                    "description",
                    ""
                )
            )

            if not titulo or not enlace:
                continue

            # Google News suele añadir el nombre del medio
            # después del título.
            if " - " in titulo:
                titulo = titulo.rsplit(
                    " - ",
                    1
                )[0]

            fecha = datetime.now(
                timezone.utc
            )

            if fecha_raw:
                try:
                    fecha = parsedate_to_datetime(
                        fecha_raw
                    )
                except Exception:
                    pass

            resultados.append({
                "titulo": titulo,
                "enlace": enlace,
                "descripcion": descripcion,
                "fecha_objeto": fecha
            })

    return resultados


def es_noticia_getafe(noticia):

    texto = (
        noticia["titulo"] + " " +
        noticia["descripcion"]
    ).lower()

    palabras_validas = [
        "getafe",
        "azulón",
        "azulones",
        "bordalás",
        "bordalas",
        "coliseum",
    ]

    return any(
        palabra in texto
        for palabra in palabras_validas
    )


def limpiar_titulo(titulo):

    titulo = titulo.strip()

    reemplazos = {
        " - Getafe": "",
        " | Getafe": "",
    }

    for antiguo, nuevo in reemplazos.items():
        titulo = titulo.replace(
            antiguo,
            nuevo
        )

    return titulo.strip()


def categoria(titulo):

    texto = titulo.lower()

    if any(
        palabra in texto
        for palabra in [
            "fichaje",
            "fichajes",
            "firma",
            "incorpora",
            "llega",
            "mercado",
        ]
    ):
        return "FICHAJES"

    if any(
        palabra in texto
        for palabra in [
            "victoria",
            "vence",
            "ganó",
            "gana",
            "triunfo",
            "partido",
        ]
    ):
        return "PARTIDO"

    if any(
        palabra in texto
        for palabra in [
            "lesión",
            "lesionado",
            "baja",
            "enfermería",
        ]
    ):
        return "ACTUALIDAD"

    if any(
        palabra in texto
        for palabra in [
            "soria",
            "portero",
            "portería",
            "penalti",
        ]
    ):
        return "PORTERÍA"

    return "ACTUALIDAD"


def resumen(titulo, descripcion):

    descripcion = limpiar_texto(
        descripcion
    )

    if descripcion:
        return descripcion[:300]

    return (
        titulo +
        ". Toda la actualidad y "
        "última hora del Getafe CF."
    )


def clave(titulo):

    texto = titulo.lower()

    texto = re.sub(
        r"[^a-záéíóúüñ0-9 ]",
        "",
        texto
    )

    palabras = texto.split()

    return " ".join(
        palabras[:10]
    )


def cargar_actuales():

    if not ARCHIVO.exists():
        return []

    try:
        with open(
            ARCHIVO,
            "r",
            encoding="utf-8"
        ) as archivo:
            datos = json.load(archivo)

        if isinstance(datos, list):
            return datos

    except Exception as error:
        print(
            f"⚠️ No se pudo leer noticias.json: {error}"
        )

    return []


def main():

    print("🤖 AZULONES NEWS")
    print("========================")

    actuales = cargar_actuales()

    claves_existentes = {
        clave(noticia.get("titulo", ""))
        for noticia in actuales
    }

    nuevas = obtener_noticias()

    print(
        f"📰 Resultados encontrados: {len(nuevas)}"
    )

    añadidas = 0

    for noticia in nuevas:

        if not es_noticia_getafe(noticia):
            continue

        titulo = limpiar_titulo(
            noticia["titulo"]
        )

        identificador = clave(titulo)

        if not identificador:
            continue

        if identificador in claves_existentes:
            continue

        noticia_final = {
            "titulo": titulo,
            "categoria": categoria(titulo),
            "fecha": noticia[
                "fecha_objeto"
            ].astimezone().strftime(
                "%d %B %Y"
            ),
            "imagen": "img/noticias/noticia-generica.jpg",
            "resumen": resumen(
                titulo,
                noticia["descripcion"]
            ),
            "enlace": noticia["enlace"]
        }

        actuales.insert(
            0,
            noticia_final
        )

        claves_existentes.add(
            identificador
        )

        añadidas += 1

        print(
            f"✅ Nueva noticia: {titulo}"
        )

        if añadidas >= 5:
            break

    actuales = actuales[:MAX_NOTICIAS]

    with open(
        ARCHIVO,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            actuales,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print("========================")
    print(
        f"🆕 Noticias nuevas: {añadidas}"
    )
    print(
        f"📚 Total guardadas: {len(actuales)}"
    )
    print("✅ noticias.json actualizado")


if __name__ == "__main__":
    main()