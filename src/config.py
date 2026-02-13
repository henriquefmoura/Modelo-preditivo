"""
Configurações globais do projeto.
"""

import os
from pathlib import Path

# Diretórios principais
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

# Criar diretórios se não existirem
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Arquivos de dados
RAW_DATA_FILE = RAW_DATA_DIR / "dados.csv"
PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / "dados_processados.csv"

# Arquivo do modelo
MODEL_FILE = MODELS_DIR / "modelo.pkl"

# Parâmetros do modelo
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Hiperparâmetros padrão (exemplo para Random Forest)
MODEL_PARAMS = {
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 5,
    'random_state': RANDOM_STATE
}
