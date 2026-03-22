# Arquitectura

## Resumen

El sistema se divide en tres piezas de runtime:

- `miner`: produce eventos de mineria desde repositorios de GitHub.
- `redis`: transporta eventos y almacena contadores agregados.
- `visualizer`: consume eventos y renderiza la interfaz del ranking.

## Flujo de datos

1. El miner obtiene repositorios desde GitHub en orden descendente de stars.
2. El miner parsea archivos Python y Java y emite lotes de palabras normalizadas.
3. El consumidor del visualizer lee el stream y actualiza claves agregadas en Redis.
4. La interfaz de Streamlit lee solo claves agregadas y se refresca en un intervalo corto.

## Notas de diseño

- El miner y el visualizer deben mantenerse desacoplados.
- Redis Streams define el limite productor-consumidor.
- Las claves agregadas de Redis permiten que la UI sobreviva a reinicios del visualizer.
- La UI no debe contener logica de ingesta de larga duracion.
