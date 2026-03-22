# Contrato de eventos

## Variables de entorno compartidas

- `REDIS_HOST`
- `REDIS_PORT`
- `STREAM_NAME`
- `GITHUB_TOKEN`
- `TOP_N_DEFAULT`
- `UI_REFRESH_SECONDS`

## Stream

- Nombre del stream: `mining_events`
- Consumer group: `visualizer_group`

## Tipos de evento

### `word_batch`

Campos requeridos:

- `event_type`
- `repo_full_name`
- `repo_stars`
- `language`
- `path`
- `word_counts_json`
- `functions_found`
- `emitted_at`

### `repo_processed`

Campos requeridos:

- `event_type`
- `repo_full_name`
- `repo_stars`
- `python_files`
- `java_files`
- `status`
- `emitted_at`

## Claves agregadas

- `word_ranking`: sorted set de Redis con conteos globales por palabra.
- `mining_stats`: hash de Redis con totales y metadatos del ultimo repositorio procesado.

## Regla del contrato

Si cambia cualquier campo de evento o clave de Redis, este archivo y la logica del consumidor deben actualizarse en el mismo cambio.
