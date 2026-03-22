#!/bin/sh
set -eu

python -m visualizer.consumer &
exec streamlit run src/visualizer/app.py --server.address=0.0.0.0 --server.port=8501
