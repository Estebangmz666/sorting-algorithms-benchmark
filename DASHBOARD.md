# Dashboard de algoritmos de ordenamiento

El dashboard permite explorar resultados y comparar, por ejemplo, MergeSort en C++ con RadixSort en Python.
Es un único archivo HTML que funciona sin internet.

## Generar y abrir

Desde la carpeta del proyecto, en PowerShell:

```powershell
python scripts/plotResults.py
```

Genera los seis PNG previstos, según los resultados disponibles, y `charts/dashboard.html`.
Los PNG requieren `matplotlib`, `pandas` y `numpy`.

Para generar únicamente el dashboard con la biblioteca estándar de Python:

```powershell
python scripts/buildDashboard.py
```

Estos comandos no vuelven a ejecutar la suite ni modifican sus CSV.
Abre `charts/dashboard.html` con doble clic en el navegador.
El profesor solo necesita recibir ese HTML; no necesita Python ni dependencias.

## Comparar y explorar

- En **Comparador**, elige algoritmo y lenguaje para las series A y B.
- Selecciona una variante compartida: aleatoria, ascendente o descendente.
- La curva muestra todos los tamaños; **Tamaño para el detalle** cambia las tarjetas,
  la comparación y la línea vertical.
- En **Explorador**, activa los algoritmos y lenguajes que quieras visualizar juntos.
- Alterna entre tiempo en escala logarítmica o lineal. El eje de tamaño es logarítmico.
- Las estimaciones están excluidas inicialmente. **Incluir estimaciones** las muestra
  con rombos huecos y las identifica en los detalles; no equivalen a mediciones.
- **Detalle** permite consultar repeticiones, desviación estándar, método, modelo,
  referencia de extrapolación y error, cuando estén registrados.
- Puedes descargar la gráfica en SVG o el CSV de la vista.

## Actualizar y compartir

El HTML es una instantánea: puede estar incompleto mientras la suite sigue corriendo.
Al terminar, ejecuta nuevamente uno de los comandos para actualizarlo.

También puedes usar **Cargar CSV** con `results_cpp.csv` y/o `results_py.csv` de `results/`.
Cada archivo reemplaza los datos de su lenguaje en el dashboard, sin cambiar el CSV original.
El archivo antiguo `sorting_results.csv` no se mezcla con estos resultados.
**Guardar HTML** descarga un archivo autónomo con los datos actuales, incluidos los CSV
importados. Al abrirlo de nuevo, conserva esos datos y restablece la selección inicial
(MergeSort/C++ frente a RadixSort/Python, entrada aleatoria y estimaciones desactivadas).
Los datos ficticios usados en las pruebas no forman parte de los resultados de la suite.

## Interpretar los resultados

En datos medidos, media y desviación muestral corresponden a cinco ejecuciones sobre el mismo dataset.
Se cronometra el ordenamiento; la lectura, la copia y la validación quedan fuera.
Una razón de tiempos compara estas implementaciones, entrada y entorno concretos;
no demuestra que un lenguaje siempre sea más rápido. Los CSV no registran hardware,
versión del compilador ni identificador de corrida. Pendiente o fallido no significa cero.

## Verificar el generador

`python -m unittest discover -s scripts/tests -p 'test_dashboard_*.py' -v`

Las pruebas usan archivos temporales; no ejecutan los benchmarks ni alteran sus resultados.
