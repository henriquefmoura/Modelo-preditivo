# Modelo-preditivo
Doutorado

## Estrutura do Projeto

```
reformas-ia/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ data/
│  ├─ raw/            # coloca o CSV bruto aqui (não commitar se tiver dados sensíveis)
│  └─ processed/
├─ src/
│  ├─ config.py
│  ├─ make_features.py
│  ├─ train.py
│  ├─ evaluate.py
│  └─ predict.py
└─ models/
   └─ (arquivos .pkl gerados)
```

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### 1. Processar Features

```bash
cd src
python make_features.py
```

### 2. Treinar Modelo

```bash
cd src
python train.py
```

### 3. Avaliar Modelo

```bash
cd src
python evaluate.py
```

### 4. Fazer Predições

```bash
cd src
python predict.py <caminho_para_dados.csv>
```

## Configuração

As configurações do projeto podem ser ajustadas em `src/config.py`.
