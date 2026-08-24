document.addEventListener("DOMContentLoaded", async () => {

    try {

        const respuesta = await fetch("data/noticias.json");

        if (!respuesta.ok) {
            throw new Error("No se pudo cargar noticias.json");
        }

        const noticias = await respuesta.json();

        const noticiaPrincipal =
            document.querySelector(".noticia-principal");

        const miniNoticias =
            document.querySelectorAll(".mini-noticia");

        if (!noticias.length) return;


        /* ================================
           NOTICIA PRINCIPAL
        ================================= */

        if (noticiaPrincipal && noticias[0]) {

            const noticia = noticias[0];

            const enlace =
                noticiaPrincipal.closest("a");

            const imagen =
                noticiaPrincipal.querySelector("img");

            const categoria =
                noticiaPrincipal.querySelector(".categoria");

            const titulo =
                noticiaPrincipal.querySelector("h2");

            const fecha =
                noticiaPrincipal.querySelector("p");


            if (enlace)
                enlace.href = noticia.enlace;

            if (imagen) {
                imagen.src = noticia.imagen;
                imagen.alt = noticia.titulo;
            }

            if (categoria)
                categoria.textContent =
                    noticia.categoria;

            if (titulo)
                titulo.textContent =
                    noticia.titulo;

            if (fecha)
                fecha.textContent =
                    noticia.fecha +
                    " · Redacción Azulones News";
        }


        /* ================================
           NOTICIAS SECUNDARIAS
        ================================= */

        miniNoticias.forEach((bloque, index) => {

            const noticia =
                noticias[index + 1];

            if (!noticia) return;


            const enlace =
                bloque.closest("a");

            const imagen =
                bloque.querySelector("img");

            const categoria =
                bloque.querySelector("span");

            const titulo =
                bloque.querySelector("h5");


            if (enlace)
                enlace.href =
                    noticia.enlace;

            if (imagen) {
                imagen.src =
                    noticia.imagen;

                imagen.alt =
                    noticia.titulo;
            }

            if (categoria)
                categoria.textContent =
                    noticia.categoria;

            if (titulo)
                titulo.textContent =
                    noticia.titulo;

        });


    } catch (error) {

        console.error(
            "Error cargando las noticias:",
            error
        );

    }

});