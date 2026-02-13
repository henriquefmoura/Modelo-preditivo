"""
Módulo para avaliação de modelos de machine learning.
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve
)
from config import MODEL_FILE, PROCESSED_DATA_FILE


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


def evaluate_model(model, X_test, y_test):
    """
    Avalia o modelo e retorna métricas.
    
    Args:
        model: Modelo treinado
        X_test: Features de teste
        y_test: Target de teste
    
    Returns:
        Dicionário com as métricas
    """
    print("Avaliando modelo...")
    
    # Predições
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
    
    # Calcular métricas
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted'),
        'recall': recall_score(y_test, y_pred, average='weighted'),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    if y_pred_proba is not None and len(np.unique(y_test)) == 2:
        metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
    
    return metrics, y_pred, y_pred_proba


def print_metrics(metrics):
    """
    Imprime as métricas de avaliação.
    
    Args:
        metrics: Dicionário com métricas
    """
    print("\n=== Métricas de Avaliação ===")
    for metric_name, metric_value in metrics.items():
        print(f"{metric_name.capitalize()}: {metric_value:.4f}")


def plot_confusion_matrix(y_test, y_pred, save_path=None):
    """
    Plota a matriz de confusão.
    
    Args:
        y_test: Target real
        y_pred: Predições
        save_path: Caminho para salvar o gráfico (opcional)
    """
    cm = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Matriz de Confusão')
    plt.ylabel('Valor Real')
    plt.xlabel('Valor Predito')
    
    if save_path:
        plt.savefig(save_path)
        print(f"Matriz de confusão salva em: {save_path}")
    else:
        plt.show()
    
    plt.close()


def print_classification_report(y_test, y_pred):
    """
    Imprime o relatório de classificação.
    
    Args:
        y_test: Target real
        y_pred: Predições
    """
    print("\n=== Relatório de Classificação ===")
    print(classification_report(y_test, y_pred))


def main():
    """
    Pipeline principal de avaliação.
    """
    print("=== Iniciando avaliação do modelo ===")
    
    # Carregar modelo
    model = load_model()
    
    # Carregar dados de teste
    # Nota: Você precisa ter salvo X_test e y_test ou recarregar os dados
    print("\nNota: Esta é uma versão simplificada.")
    print("Para avaliação completa, passe X_test e y_test como argumentos.")
    
    print("=== Avaliação concluída ===")


if __name__ == "__main__":
    main()
