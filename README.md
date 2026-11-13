# Libreta de calificaciones · Segundo I

Unidad Educativa PCEI Tungurahua · 2026–2027 · Ciclo 1 · Primera etapa.

**Portal:** https://libreta-calificaciones-2do-pcei.onrender.com/

**Acceso de GitHub Pages:** https://javo1979.github.io/libreta_calificaciones_2do/

Consulta por cédula, lista colorida de 13 asignaturas, sello institucional, mensajes breves e impresión/guardado en PDF A4 de una sola hoja. Proyecto independiente de la libreta de Primero I.

## Importación de notas

```sh
python -m pip install -r requirements.txt
python importar_notas.py --resumen "ruta/Cuadro de resumen  2do I.xlsx" --registro "ruta/Registro_Calificaciones_Paralelo_I.xlsx"
python app.py
```

Abrir http://127.0.0.1:5001. El importador toma las notas directas de **I ETAPA**, columnas **C:O**, y las cédulas de **2do I Matemática**. No utiliza las notas del registro ni recalcula promedios. La hoja II ETPA está vacía y no se publica. Los nombres se cotejan ignorando acentos, mayúsculas y espacios, sin coincidencias aproximadas. Una discrepancia impide la importación.

Celdas vacías o «SN»: **Sin nota**; un cero numérico sí se conserva. Los estudiantes sin cédula se guardan localmente en `datos/pendientes_identificacion.json` y no pueden consultarse hasta completar el padrón y volver a importar. No se inventan identificaciones.

## Publicación

GitHub Pages no ejecuta Python. `render.yaml` configura un servicio Python gratuito. Build: `pip install -r requirements.txt`. Start: `waitress-serve --listen=0.0.0.0:$PORT app:app`. Ruta de comprobación: `/`.

En Render, cargar `calificaciones.json` como **Secret File**; configurar `CALIFICACIONES_PATH=/etc/secrets/calificaciones.json` y `TRUST_PROXY=1` solo detrás de su proxy de confianza. **No subir `datos/` ni los Excel al repositorio público.** El alojamiento gratuito puede tardar al iniciar tras inactividad.

El registro de Segundo debe cargarse exclusivamente en su propio servicio, nunca sobre el de Primero.

## Privacidad

El servidor devuelve solo el reporte consultado, oculta parte de la cédula, evita guardar el reporte en el navegador e incluye un límite básico por IP. **La cédula no demuestra identidad**: quien la conozca puede consultar la nota. Para mayor protección se necesita verificación o contraseña adicional. El límite en memoria no garantiza impedir consultas automatizadas.

## Impresión y pruebas

Tras consultar, pulsar **Imprimir / Guardar PDF**. En el diálogo elegir impresora o **Guardar como PDF**. Usar A4 vertical, escala 100 %, sin encabezados/pies del navegador.

```sh
python -m unittest discover -s tests -v
```

Las pruebas usan datos ficticios; el padrón real permanece fuera del repositorio.
