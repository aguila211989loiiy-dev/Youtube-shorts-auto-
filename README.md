# YouTube Shorts automático y gratuito

Crea MP4 de 1080×1920 (9:16), con voz española de eSpeak NG, imagen y subtítulos incrustados mediante FFmpeg. No usa Descript, créditos, API de IA ni claves de pago. La voz es sintética y básica.

## Programación

`.github/workflows/daily-shorts.yml` ejecuta el generador diariamente a las **10:00 de São Paulo** (`America/Sao_Paulo`, actualmente UTC−3; cron `0 13 * * *`). GitHub puede retrasar ejecuciones; no garantiza precisión al minuto. El workflow debe estar en la rama predeterminada `main`, con Actions habilitado. En repositorios públicos inactivos, GitHub puede desactivar los schedules después de 60 días. Si cambia el huso legal, actualizar el cron.

En **Actions → Shorts diarios gratuitos → Run workflow**, también puedes ejecutarlo manualmente. Descarga el resultado desde los artefactos de la ejecución: MP4, SRT y JSON con título y créditos. Los artefactos se conservan 7 días.

## Contenido

`content.json` incluye dos guiones educativos de ejemplo sobre la Tierra, con una fotografía de NASA de dominio público. El catálogo rota por fecha de São Paulo y se repite al agotarse. Añade tus propios guiones e imágenes para ampliar la variedad; no inventa contenido nuevo con IA.

Cada entrada requiere `title`, `sentences` y `image_url` HTTPS o `image_path` local. Conserva `image_credit` y `source` para documentar permisos y atribución. Usa frases cortas (máximo 180 caracteres cada una) y un total de voz inferior a 60 segundos. Puedes usar imágenes locales para eliminar la dependencia de Wikimedia.

## Protección obligatoria

Si la imagen falta, no se descarga o no se decodifica, se detiene antes de crear voz o MP4. Si cualquier segmento de voz falta, está corrupto o silencioso, se detiene antes del renderizado. Se comprueban el audio combinado, las dimensiones 9:16 y la decodificación completa del MP4. El MP4 solo aparece en la carpeta de salida después de superar todas las comprobaciones. El workflow solo guarda artefactos cuando el proceso termina correctamente.

No contiene publicación a YouTube ni credenciales: produce archivos para descargar. Para añadir publicación en el futuro, el cargador deberá ejecutarse únicamente después de estas mismas validaciones y con OAuth del canal.

## Uso local

En Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
python3 -m unittest discover -s tests -v
python3 shorts.py
```

Python 3.10 o posterior; sin dependencias pip. FFmpeg debe incluir libx264 y el filtro subtitles/libass. El generador descarga imágenes por HTTPS, pero sintetiza la voz y monta el vídeo localmente. GitHub Actions está sujeto a los límites y condiciones de su plan gratuito.
