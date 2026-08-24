import json
import re
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


# =========================================================
# CONFIGURACIÓN
# =========================================================

ARCHIVO = Path("data/noticias.json")
CARPETA_IMAGENES = Path("img/noticias/auto")

MAX_NOTICIAS = 10
MAX_NUEVAS = 5

IMAGEN_GENERICA = "img/noticias/noticia-generica.jpg"

FEEDS = [
    "Getafe CF",
    "Getafe fútbol",
    '"Getafe CF" fichajes',
    '"Getafe CF" Bordalás',
]


# =========================================================
# UTILIDADES
# =========================================================

def limpiar_texto(texto):
    texto = re.sub(r"<[^>]+>", "", texto or "")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def nombre_archivo_seguro(texto):
    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9áéíóúüñ\s-]",
        "",
        texto
    )

    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("ü", "u")
    texto = texto.replace("ñ", "n")

    texto = re.sub(r"\s+", "-", texto)
    texto = re.sub(r"-+", "-", texto)

    return texto[:70].strip("-")


def clave(titulo):
    texto = titulo.lower()

    texto = re.sub(
        r"[^a-záéíóúüñ0-9 ]",
        "",
        texto
    )

    palabras = texto.split()

    return " ".join(palabras[:10])


# =========================================================
# GOOGLE NEWS RSS
# =========================================================

def descargar_feed(busqueda):

    params = urllib.parse.urlencode({
        "q": busqueda,
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es"
    })

    url = (
        "https://news.google.com/rss/search?"
        + params
    )

    solicitud = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; AzulonesNews/1.0)"
            )
        }
    )

    with urllib.request.urlopen(
        solicitud,
        timeout=20
    ) as respuesta:

        return respuesta.read()


def obtener_noticias():

    resultados = []

    for busqueda in FEEDS:

        print(f"🔎 Buscando: {busqueda}")

        try:

            contenido = descargar_feed(
                busqueda
            )

            raiz = ET.fromstring(
                contenido
            )

        except Exception as error:

            print(
                f"⚠️ Error en la búsqueda: {error}"
            )

            continue

        for item in raiz.findall(
            ".//item"
        ):

            titulo = limpiar_texto(
                item.findtext(
                    "title",
                    ""
                )
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


# =========================================================
# FILTROS
# =========================================================

def es_noticia_getafe(noticia):

    texto = (
        noticia["titulo"]
        + " "
        + noticia["descripcion"]
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


def crear_resumen(
    titulo,
    descripcion
):

    descripcion = limpiar_texto(
        descripcion
    )

    if descripcion:

        return descripcion[:300]

    return (
        titulo
        + ". Toda la actualidad y "
        "última hora del Getafe CF."
    )


# =========================================================
# IMÁGENES
# =========================================================

def buscar_og_image(url):

    try:

        solicitud = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; AzulonesNews/1.0)"
                )
            }
        )

        with urllib.request.urlopen(
            solicitud,
            timeout=15
        ) as respuesta:

            contenido = respuesta.read(
                500000
            ).decode(
                "utf-8",
                errors="ignore"
            )

        patrones = [

            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',

            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',

            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',

            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]

        for patron in patrones:

            resultado = re.search(
                patron,
                contenido,
                re.IGNORECASE
            )

            if resultado:

                imagen = resultado.group(1)

                return urllib.parse.urljoin(
                    url,
                    imagen
                )

    except Exception as error:

        print(
            f"⚠️ No se pudo obtener la imagen: {error}"
        )

    return None


def descargar_imagen(
    url,
    titulo
):

    if not url:

        return IMAGEN_GENERICA

    try:

        CARPETA_IMAGENES.mkdir(
            parents=True,
            exist_ok=True
        )

        nombre = nombre_archivo_seguro(
            titulo
        )

        if not nombre:

            nombre = "noticia"

        ruta = (
            CARPETA_IMAGENES
            / f"{nombre}.jpg"
        )

        imagen_url = buscar_og_image(
            url
        )

        if not imagen_url:

            print(
                "⚠️ No se encontró og:image"
            )

            return IMAGEN_GENERICA

        print(
            f"🖼️ Imagen encontrada: {imagen_url}"
        )

        solicitud = urllib.request.Request(
            imagen_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; AzulonesNews/1.0)"
                )
            }
        )

        with urllib.request.urlopen(
            solicitud,
            timeout=20
        ) as respuesta:

            datos = respuesta.read()

        if len(datos) < 5000:

            print(
                "⚠️ Imagen demasiado pequeña"
            )

            return IMAGEN_GENERICA

        with open(
            ruta,
            "wb"
        ) as archivo:

            archivo.write(datos)

        print(
            f"✅ Imagen guardada: {ruta}"
        )

        return str(
            ruta
        ).replace(
            "\\",
            "/"
        )

    except Exception as error:

        print(
            f"⚠️ Error descargando imagen: {error}"
        )

        return IMAGEN_GENERICA


# =========================================================
# JSON
# =========================================================

def cargar_actuales():

    if not ARCHIVO.exists():

        return []

    try:

        with open(
            ARCHIVO,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

        if isinstance(
            datos,
            list
        ):

            return datos

    except Exception as error:

        print(
            f"⚠️ Error leyendo noticias.json: {error}"
        )

    return []


# =========================================================
# PROGRAMA PRINCIPAL
# =========================================================

def main():

    print("")
    print("🤖 AZULONES NEWS")
    print("==============================")

    actuales = cargar_actuales()

    claves_existentes = {
        clave(
            noticia.get(
                "titulo",
                ""
            )
        )
        for noticia in actuales
    }

    noticias = obtener_noticias()

    print("")
    print(
        f"📰 Resultados encontrados: "
        f"{len(noticias)}"
    )

    nuevas = 0

    for noticia in noticias:

        if not es_noticia_getafe(
            noticia
        ):

            continue

        titulo = limpiar_titulo(
            noticia["titulo"]
        )

        identificador = clave(
            titulo
        )

        if not identificador:

            continue

        if identificador in claves_existentes:

            continue

        print("")
        print(
            f"🆕 Nueva noticia: {titulo}"
        )

        imagen = descargar_imagen(
            noticia["enlace"],
            titulo
        )

        noticia_final = {

            "titulo": titulo,

            "categoria": categoria(
                titulo
            ),

            "fecha": noticia[
                "fecha_objeto"
            ].astimezone().strftime(
                "%d %B %Y"
            ),

            "imagen": imagen,

            "resumen": crear_resumen(
                titulo,
                noticia["descripcion"]
            ),

            "enlace": noticia[
                "enlace"
            ]
        }

        actuales.insert(
            0,
            noticia_final
        )

        claves_existentes.add(
            identificador
        )

        nuevas += 1

        if nuevas >= MAX_NUEVAS:

            break

    actuales = actuales[
        :MAX_NOTICIAS
    ]

    ARCHIVO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

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

    print("")
    print("==============================")
    print(
        f"🆕 Noticias nuevas: {nuevas}"
    )

    print(
        f"📚 Total guardadas: "
        f"{len(actuales)}"
    )

    print(
        "🖼️ Sistema de imágenes activado"
    )

    print(
        "✅ noticias.json actualizado"
    )

    print("==============================")


if __name__ == "__main__":

    main()