# GitHub Method Word Ranker

## Objetivo

Minar repositorios Python y Java desde GitHub, extraer palabras desde nombres de funciones y metodos, y visualizar el ranking en tiempo casi real.

## Componentes planificados

- `miner`: recorre repositorios de GitHub, parsea archivos fuente, divide palabras y publica eventos.
- `visualizer`: consume eventos, persiste agregados en Redis y renderiza el ranking con Streamlit.
- `redis`: broker compartido y almacenamiento de agregados.

## Estado actual

Esta carpeta contiene solo la estructura inicial, las dependencias base y la documentacion del proyecto. El comportamiento de runtime sigue pendiente de implementacion.

## Comando previsto de ejecucion

```bash
docker compose up --build
```

## Archivos clave

- `docs/architecture.md`
- `docs/event-contract.md`
- `AGENTS.md`

## Proximos pasos

1. Implementar el recorrido de GitHub con rangos de stars descendentes.
2. Implementar los parsers de Python y Java.
3. Implementar la publicacion de eventos en Redis y el consumo de agregados.
4. Implementar la interfaz de ranking en Streamlit.
