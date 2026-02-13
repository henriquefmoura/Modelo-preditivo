"""
Módulo para fazer predições com modelo treinado.
"""

import pandas as pd
import numpy as np
import joblib
from config import MODEL_FILE


def load_model(file_path=None):
    """
    Carrega modelo treinado.
    
    Args:
        file_path: Caminho para o arquivo do modelo (opcional)
    
    Returns:
        Modelo carregado
    """
    if file_path is None:
        file_path = MODEL_FILE
    
    print(f"Carregando modelo de: {file_path}")
    model = joblib.load(file_path)
    return model


def load_data_for_prediction(file_path):
    """
    Carrega dados para predição.
    
    Args:
        file_path: Caminho para arquivo CSV com dados
    
    Returns:
        DataFrame com os dados
    """
    print(f"Carregando dados de: {file_path}")
    df = pd.read_csv(file_path)
    print(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    return df


def make_predictions(model, X):
    """
    Faz predições com o modelo.
    
    Args:
        model: Modelo treinado
        X: Features para predição (DataFrame ou array)
    
    Returns:
        Array com predições
    """
    print("Fazendo predições...")
    predictions = model.predict(X)
    
    # Se o modelo suporta probabilidades
    if hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(X)
        return predictions, probabilities
    
    return predictions, None


def save_predictions(predictions, probabilities=None, output_file='predictions.csv'):
    """
    Salva predições em arquivo CSV.
    
    Args:
        predictions: Array com predições
        probabilities: Array com probabilidades (opcional)
        output_file: Caminho para arquivo de saída
    """
    result_df = pd.DataFrame({
        'prediction': predictions
    })
    
    if probabilities is not None:
        for i in range(probabilities.shape[1]):
            result_df[f'prob_class_{i}'] = probabilities[:, i]
    
    result_df.to_csv(output_file, index=False)
    print(f"Predições salvas em: {output_file}")


def predict_single(model, features):
    """
    Faz predição para uma única amostra.
    
    Args:
        model: Modelo treinado
        features: Lista ou array com features
    
    Returns:
        Predição e probabilidade (se disponível)
    """
    # Converter para formato esperado pelo modelo
    X = np.array(features).reshape(1, -1)
    
    prediction = model.predict(X)[0]
    
    if hasattr(model, 'predict_proba'):
        probability = model.predict_proba(X)[0]
        return prediction, probability
    
    return prediction, None


def main(data_file=None):
    """
    Pipeline principal de predição.
    
    Args:
        data_file: Caminho para arquivo com dados para predição
    """
    print("=== Iniciando predições ===")
    
    # Carregar modelo
    model = load_model()
    
    if data_file:
        # Carregar dados
        df = load_data_for_prediction(data_file)
        
        # Fazer predições
        predictions, probabilities = make_predictions(model, df)
        
        # Salvar resultados
        save_predictions(predictions, probabilities)
        
        print(f"\nTotal de predições: {len(predictions)}")
        print(f"Distribuição de classes preditas:")
        print(pd.Series(predictions).value_counts())
    else:
        print("\nNenhum arquivo de dados fornecido.")
        print("Use: python predict.py <caminho_para_dados.csv>")
    
    print("=== Predições concluídas ===")


if __name__ == "__main__":
    import sys
    
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(data_file)
