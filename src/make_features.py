"""
Módulo para criação de features a partir dos dados brutos.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from config import RAW_DATA_FILE, PROCESSED_DATA_FILE


def load_raw_data(file_path=None):
    """
    Carrega dados brutos do CSV.
    
    Args:
        file_path: Caminho para o arquivo CSV (opcional)
    
    Returns:
        DataFrame com os dados brutos
    """
    if file_path is None:
        file_path = RAW_DATA_FILE
    
    print(f"Carregando dados de: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    return df


def clean_data(df):
    """
    Limpa os dados removendo valores nulos e duplicatas.
    
    Args:
        df: DataFrame com dados brutos
    
    Returns:
        DataFrame limpo
    """
    print("Limpando dados...")
    
    # Remover duplicatas
    initial_rows = len(df)
    df = df.drop_duplicates()
    print(f"Duplicatas removidas: {initial_rows - len(df)}")
    
    # Tratar valores nulos
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print(f"Valores nulos encontrados:\n{null_counts[null_counts > 0]}")
        df = df.dropna()
        print(f"Linhas após remoção de nulos: {len(df)}")
    
    return df


def create_features(df):
    """
    Cria novas features a partir dos dados existentes.
    
    Args:
        df: DataFrame com dados limpos
    
    Returns:
        DataFrame com features adicionais
    """
    print("Criando features...")
    
    # Exemplo: adicionar features derivadas
    # Customize de acordo com seus dados
    
    # df['nova_feature'] = df['coluna1'] * df['coluna2']
    
    return df


def save_processed_data(df, file_path=None):
    """
    Salva dados processados em CSV.
    
    Args:
        df: DataFrame processado
        file_path: Caminho para salvar (opcional)
    """
    if file_path is None:
        file_path = PROCESSED_DATA_FILE
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    print(f"Dados processados salvos em: {file_path}")


def main():
    """
    Pipeline principal de processamento de features.
    """
    print("=== Iniciando processamento de features ===")
    
    # Carregar dados
    df = load_raw_data()
    
    # Limpar dados
    df = clean_data(df)
    
    # Criar features
    df = create_features(df)
    
    # Salvar dados processados
    save_processed_data(df)
    
    print("=== Processamento concluído ===")


if __name__ == "__main__":
    main()
