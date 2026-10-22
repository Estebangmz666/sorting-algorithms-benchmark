# Tiempo promedio por búsqueda según la posición de la clave (n = 1.000.000)

Cada valor es la media de 5 repeticiones de 1.000 búsquedas de la misma clave (media ± desviación estándar muestral, por búsqueda).

## C++

| Algoritmo | Inicio | Centro | Final |
|---|---|---|---|
| Lineal | 2.0 ns ± 0.8 ns | 134.24 µs ± 9.29 µs | 368.61 µs ± 90.62 µs |
| Binaria | 24.0 ns ± 1.0 ns | 24.5 ns ± 1.6 ns | 26.4 ns ± 5.6 ns |
| Ternaria | 28.5 ns ± 2.5 ns | 34.4 ns ± 5.4 ns | 25.6 ns ± 0.5 ns |
| Saltos | 3.4 ns ± 0.2 ns | 482.7 ns ± 78.7 ns | 1.73 µs ± 815.3 ns |
| Interpolación | 3.5 ns ± 1.1 ns | 19.2 ns ± 0.5 ns | 3.5 ns ± 0.8 ns |
| Exponencial | 1.9 ns ± 0.3 ns | 27.4 ns ± 0.7 ns | 34.6 ns ± 2.2 ns |

## Python

| Algoritmo | Inicio | Centro | Final |
|---|---|---|---|
| Lineal | 293.1 ns ± 107.3 ns | 17.62 ms ± 4.70 ms | 33.89 ms ± 3.80 ms |
| Binaria | 2.03 µs ± 96.8 ns | 2.41 µs ± 311.4 ns | 2.83 µs ± 763.4 ns |
| Ternaria | 2.10 µs ± 142.9 ns | 4.02 µs ± 2.15 µs | 2.41 µs ± 62.8 ns |
| Saltos | 377.9 ns ± 71.6 ns | 51.46 µs ± 7.15 µs | 200.19 µs ± 64.24 µs |
| Interpolación | 308.8 ns ± 91.1 ns | 1.98 µs ± 807.2 ns | 394.2 ns ± 135.0 ns |
| Exponencial | 112.8 ns ± 4.2 ns | 2.55 µs ± 59.4 ns | 3.38 µs ± 700.4 ns |
