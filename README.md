# Anotador de Imágenes (Windows)

Programa para marcar puntos sobre una imagen: haces clic en la imagen y en ese
punto se coloca una figura como las de Word (rayo, círculo, estrella, flechas…),
numerada automáticamente. Después puedes descargar la imagen o copiar la captura.

## Funciones

- **Barra de figuras** (arriba): rayo ⚡ (seleccionado por defecto), círculo,
  cuadrado, rectángulo, rectángulo redondeado, triángulos, rombo, pentágono,
  hexágono, octógono, paralelogramo, trapecio, estrellas de 4/5/6 puntas,
  explosión, sol, corazón, luna, nube, bocadillo, flechas (derecha, izquierda,
  arriba, abajo, doble), cheurón, cruz, aspa, visto ✓, anillo y marcador.
- **Colores**: color de contorno y color de relleno (selector completo o paleta
  rápida: clic izquierdo = relleno, clic derecho = contorno), botón *Sin
  relleno*, grosor del contorno y casilla para quitar el contorno.
- **Barra de tamaño** y **barra de giro**, con vista previa. Botones *Aplicar a
  la última* / *Aplicar a todas* para cambiar figuras ya colocadas.
- **Numeración**: casilla *Numerar puntos* y botón **⚙** para configurarla:
  número inicial, texto antes/después (p. ej. `P1`, `1.`), posición (derecha,
  izquierda, arriba, abajo, centro), tamaño, color y fondo del número.
  Al borrar un punto, los demás se renumeran solos.
- **Descargar imagen** (PNG, JPG, BMP, WEBP) a la resolución original, con
  bordes suavizados.
- **Copiar captura** al portapapeles para pegarla en Word, WhatsApp, Paint…
- Abrir imagen o **pegarla** desde el portapapeles (Ctrl+V).
- Deshacer / rehacer, zoom, mover figuras arrastrándolas, borrar con clic derecho.

## Atajos

| Acción | Atajo |
|---|---|
| Colocar figura | Clic izquierdo |
| Mover figura | Arrastrar la figura |
| Borrar figura | Clic derecho sobre ella |
| Borrar la última | Supr |
| Deshacer / Rehacer | Ctrl+Z / Ctrl+Y |
| Abrir / Pegar imagen | Ctrl+O / Ctrl+V |
| Descargar imagen | Ctrl+S |
| Copiar captura | Ctrl+C |
| Zoom | Ctrl + rueda del ratón |

## Cómo usarlo en Windows

**Opción A – Descargar el .exe ya compilado:** [AnotadorImagenes.exe](https://github.com/maarcos125/Proyectos/releases/latest/download/AnotadorImagenes.exe)
(también en la sección *Releases* del repositorio). No hace falta instalar nada.

**Opción B – Crear el .exe tú mismo:**
1. Instala [Python 3](https://www.python.org/downloads/) (marca *Add Python to PATH*).
2. Haz doble clic en `crear_exe.bat`.
3. El programa queda en `dist\AnotadorImagenes.exe`.

**Opción C – Ejecutarlo directamente con Python:** doble clic en `ejecutar.bat`.
