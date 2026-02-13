"""
Módulo para treinamento de modelos de machine learning.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from config import PROCESSED_DATA_FILE, MODEL_FILE, RANDOM_STATE, TEST_SIZE, MODEL_PARAMS


def load_processed_data(file_path=None):
    """
    Carrega dados processados.
    
    Args:
        file_path: Caminho para o arquivo processado (opcional)
    
    Returns:
        DataFrame com os dados processados
    """
    if file_path is None:
        file_path = PROCESSED_DATA_FILE
    
    print(f"Carregando dados processados de: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    return df


def prepare_train_test_split(df, target_column, test_size=TEST_SIZE):
    """
    Separa dados em treino e teste.
    
    Args:
        df: DataFrame com os dados
        target_column: Nome da coluna target
        test_size: Proporção de dados para teste
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    print(f"Preparando split treino/teste (test_size={test_size})...")
    
    # Separar features e target
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    # Split treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
    )
    
    print(f"Treino: {len(X_train)} amostras")
    print(f"Teste: {len(X_test)} amostras")
    
    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, model_params=None):
    """
    Treina o modelo de machine learning.
    
    Args:
        X_train: Features de treino
        y_train: Target de treino
        model_params: Hiperparâmetros do modelo (opcional)
    
    Returns:
        Modelo treinado
    """
    if model_params is None:
        model_params = MODEL_PARAMS
    
    print("Treinando modelo...")
    print(f"Hiperparâmetros: {model_params}")
    
    # Criar e treinar modelo
    model = RandomForestClassifier(**model_params)
    model.fit(X_train, y_train)
    
    print("Modelo treinado com sucesso!")
    return model


def save_model(model, file_path=None):
    """
    Salva o modelo treinado.
    
    Args:
        model: Modelo treinado
        file_path: Caminho para salvar o modelo (opcional)
    """
    if file_path is None:
        file_path = MODEL_FILE
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, file_path)
    print(f"Modelo salvo em: {file_path}")


def main(target_column='target'):
    """
    Pipeline principal de treinamento.
    
    Args:
        target_column: Nome da coluna target nos dados
    """
    print("=== Iniciando treinamento do modelo ===")
    
    # Carregar dados
    df = load_processed_data()
    
    # Preparar split
    X_train, X_test, y_train, y_test = prepare_train_test_split(df, target_column)
    
    # Treinar modelo
    model = train_model(X_train, y_train)
    
    # Salvar modelo
    save_model(model)
    
    # Avaliar no conjunto de treino
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"\nAcurácia no treino: {train_score:.4f}")
    print(f"Acurácia no teste: {test_score:.4f}")
    
    print("=== Treinamento concluído ===")
    
    return model, X_test, y_test


if __name__ == "__main__":
    main()
