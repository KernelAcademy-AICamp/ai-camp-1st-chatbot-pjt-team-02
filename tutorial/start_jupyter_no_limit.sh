#!/bin/bash

# Jupyter Notebook을 출력 제한 없이 시작하는 스크립트

echo "🚀 Jupyter Notebook을 출력 제한 없이 시작합니다..."

# 환경 변수 설정
export JUPYTER_NOTEBOOK_OUTPUT_LIMIT=200

# Jupyter 시작 (출력 제한 해제)
jupyter notebook \
    --NotebookApp.iopub_data_rate_limit=1e10 \
    --NotebookApp.iopub_msg_rate_limit=1e10 \
    --NotebookApp.rate_limit_window=10 \
    --ServerApp.iopub_data_rate_limit=1e10 \
    --ServerApp.iopub_msg_rate_limit=1e10 \
    --ServerApp.rate_limit_window=10

# 또는 JupyterLab을 사용하는 경우:
# jupyter lab \
#     --NotebookApp.iopub_data_rate_limit=1e10 \
#     --NotebookApp.iopub_msg_rate_limit=1e10