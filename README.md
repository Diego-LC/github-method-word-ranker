# GitHub Method Word Ranker

Herramienta que mina repositorios Python y Java desde GitHub, extrae palabras desde nombres de funciones y metodos, y visualiza el ranking en tiempo casi real.

## Arquitectura

```
┌──────────┐     Redis Streams     ┌──────────────┐
│  Miner   │ ──── word_batch ────► │  Consumer    │
│ (Python) │ ── repo_processed ──► │ (background) │
└──────────┘                       └──────┬───────┘
      │                                    │
  GitHub API                       Sorted Set / Hash
                                          │
                                   ┌──────▼───────┐
                                   │  Streamlit   │
                                   │  Dashboard   │
                                   └──────────────┘
```

- **Miner**: recorre repositorios de GitHub en orden descendente de stars, parsea archivos `.py` y `.java`, divide nombres de funciones/metodos en palabras y publica eventos en Redis Streams.
- **Consumer**: proceso en segundo plano que consume eventos del stream y actualiza datos agregados en Redis (sorted set + hash).
- **Dashboard**: interfaz Streamlit que lee los datos agregados de Redis y se refresca automaticamente.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose
- (Opcional) Un [token de acceso personal de GitHub](https://github.com/settings/tokens) para evitar rate limits

## Ejecucion

1. Clonar el repositorio y entrar a la carpeta del proyecto:
   ```bash
   cd github-method-word-ranker
   ```

2. (Opcional) Configurar el token de GitHub:
   ```bash
   cp .env.example .env
   # Editar .env y agregar tu GITHUB_TOKEN
   ```

3. Ejecutar con un solo comando:
   ```bash
   docker compose up --build
   ```

4. Abrir el dashboard en el navegador:
   ```
   http://localhost:8501
   ```

5. Para detener el sistema:
   ```bash
   docker compose down
   ```

## Estructura del repositorio

```
github-method-word-ranker/
├── docker-compose.yml          # Orquestacion de contenedores
├── .env.example                # Variables de entorno de ejemplo
├── docs/
│   ├── architecture.md         # Arquitectura y flujo de datos
│   └── event-contract.md       # Contrato de eventos y claves Redis
├── miner/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src/miner/
│   │   ├── main.py             # Entry point del miner
│   │   ├── config.py           # Configuracion desde env vars
│   │   ├── github_client.py    # Cliente GitHub REST API
│   │   ├── parsers/
│   │   │   ├── python_parser.py  # Extraccion via ast (stdlib)
│   │   │   └── java_parser.py    # Extraccion via javalang
│   │   ├── splitter.py         # Division de nombres en palabras
│   │   ├── range_scheduler.py  # Generacion de rangos de stars
│   │   └── publisher.py        # Publicacion en Redis Stream
│   └── tests/                  # 40 tests unitarios
└── visualizer/
    ├── Dockerfile
    ├── entrypoint.sh           # Lanza consumer + streamlit
    ├── requirements.txt
    ├── src/visualizer/
    │   ├── app.py              # Dashboard Streamlit
    │   ├── charts.py           # Graficos Plotly
    │   ├── consumer.py         # Consumidor continuo de eventos
    │   ├── redis_store.py      # Lectura/escritura de agregados
    │   └── settings.py         # Configuracion del visualizer
    └── tests/                  # 4 tests unitarios
```

## Decisiones de diseño

| Decision | Justificacion |
| --- | --- |
| **Python + ast** para parsear Python | Parser oficial del lenguaje, cubre el 100% de la sintaxis sin dependencias externas |
| **javalang** para parsear Java | Parser AST completo para Java, mas robusto que regex para declaraciones de metodos |
| **Redis Streams** como broker | Modelo productor-consumidor ligero, persistente y con consumer groups |
| **Sorted set** para ranking | Operaciones O(log N) para incrementos, O(N) para top-N. Persiste entre reinicios |
| **Streamlit** para la UI | Dashboard interactivo con auto-refresh y graficos Plotly con minimo codigo |
| **Rangos de stars** en vez de paginacion simple | La API de GitHub limita a 1000 resultados por query. Dividir en rangos permite cubrir mas repositorios |
| **Filtrar dunder methods** | `__init__`, `__str__`, etc. son convenciones del lenguaje, no decisiones del programador |

## Variables de entorno

| Variable | Default | Descripcion |
| --- | --- | --- |
| `GITHUB_TOKEN` | (vacio) | Token de acceso personal de GitHub |
| `REDIS_HOST` | `redis` | Host de Redis |
| `REDIS_PORT` | `6379` | Puerto de Redis |
| `STREAM_NAME` | `mining_events` | Nombre del stream de Redis |
| `TOP_N_DEFAULT` | `10` | Top-N por defecto en el dashboard |
| `UI_REFRESH_SECONDS` | `3` | Intervalo de auto-refresh del dashboard |

## Tests

```bash
# Miner (requiere: pip install requests redis javalang pytest)
cd miner
PYTHONPATH=src pytest tests/ -v

# Visualizer (requiere: pip install streamlit redis plotly pytest)
cd visualizer
PYTHONPATH=src pytest tests/ -v
```
