"""
Streamlit dashboard for visualizing Ready-to-Reform scores.
Displays rankings, distributions, and score drivers.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_sample_events_path, validate_bq_config, DATA_DIR
from src.bq_io import BigQueryIO, load_events_from_csv, BIGQUERY_AVAILABLE


# Page configuration
st.set_page_config(
    page_title="Ready-to-Reform Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏠 Ready-to-Reform Dashboard")
st.markdown("Sistema de detecção do momento ideal para abordagem de reformas")

# Sidebar configuration
st.sidebar.header("⚙️ Configuração")

# Data source selection
data_source = st.sidebar.radio(
    "Fonte de dados:",
    ["Sample Local", "BigQuery"],
    help="Escolha entre dados de exemplo locais ou BigQuery"
)

use_bigquery = data_source == "BigQuery"


@st.cache_data(ttl=300)
def load_scores_data(use_bq: bool = False):
    """Load scores data from BigQuery or local CSV."""
    try:
        if use_bq:
            if not BIGQUERY_AVAILABLE:
                st.error("BigQuery não disponível. Instale: pip install google-cloud-bigquery")
                return None
            
            if not validate_bq_config():
                st.error("Configuração do BigQuery inválida. Configure BQ_PROJECT_ID e BQ_CREDENTIALS_JSON")
                return None
            
            bq = BigQueryIO()
            df = bq.get_latest_scores(limit=500)
            
            # Parse top_drivers JSON
            if 'top_drivers' in df.columns:
                df['top_drivers_parsed'] = df['top_drivers'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
        else:
            # Load from local CSV (latest processed file)
            processed_dir = DATA_DIR / "processed"
            csv_files = sorted(processed_dir.glob("scores_*.csv"), reverse=True)
            
            if not csv_files:
                st.warning("Nenhum arquivo de scores encontrado. Execute primeiro: python src/run_daily_score.py --local_sample")
                return None
            
            df = pd.read_csv(csv_files[0])
            
            # Parse top_drivers JSON
            if 'top_drivers' in df.columns:
                df['top_drivers_parsed'] = df['top_drivers'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else {}
                )
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


# Load data
with st.spinner("Carregando dados..."):
    scores_df = load_scores_data(use_bigquery)

if scores_df is None or len(scores_df) == 0:
    st.info("👈 Configure a fonte de dados na barra lateral")
    st.stop()

# Filters in sidebar
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros")

# Class filter
class_options = ["Todos"] + sorted(scores_df['class_label'].unique().tolist())
selected_class = st.sidebar.selectbox(
    "Classificação:",
    class_options
)

if selected_class != "Todos":
    filtered_df = scores_df[scores_df['class_label'] == selected_class]
else:
    filtered_df = scores_df

# Score range filter
min_score = float(scores_df['score'].min())
max_score = float(scores_df['score'].max())

score_range = st.sidebar.slider(
    "Faixa de score:",
    min_value=min_score,
    max_value=max_score,
    value=(min_score, max_score)
)

filtered_df = filtered_df[
    (filtered_df['score'] >= score_range[0]) & 
    (filtered_df['score'] <= score_range[1])
]

# Top N filter
top_n = st.sidebar.slider(
    "Top N usuários:",
    min_value=10,
    max_value=min(100, len(filtered_df)),
    value=50,
    step=10
)

# Main content
st.markdown("---")

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Usuários",
        len(filtered_df),
        delta=None
    )

with col2:
    ideal_count = len(filtered_df[filtered_df['class_label'] == 'MOMENTO IDEAL'])
    ideal_pct = (ideal_count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        "Momento Ideal",
        ideal_count,
        delta=f"{ideal_pct:.1f}%"
    )

with col3:
    nurture_count = len(filtered_df[filtered_df['class_label'] == 'NUTRIR'])
    nurture_pct = (nurture_count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        "Nutrir",
        nurture_count,
        delta=f"{nurture_pct:.1f}%"
    )

with col4:
    avg_score = filtered_df['score'].mean()
    st.metric(
        "Score Médio",
        f"{avg_score:.1f}",
        delta=None
    )

st.markdown("---")

# Two-column layout
col_left, col_right = st.columns([2, 1])

with col_left:
    # Top users ranking
    st.subheader(f"🏆 Top {top_n} Usuários por Score")
    
    top_users = filtered_df.nlargest(top_n, 'score').copy()
    
    # Create bar chart
    fig_ranking = px.bar(
        top_users,
        x='anon_id',
        y='score',
        color='class_label',
        color_discrete_map={
            'MOMENTO IDEAL': '#00CC66',
            'NUTRIR': '#FFB84D',
            'NÃO ABORDAR': '#FF6B6B'
        },
        title=f"Top {top_n} Scores",
        labels={'anon_id': 'Usuário Anônimo', 'score': 'Score', 'class_label': 'Classificação'}
    )
    
    fig_ranking.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig_ranking, use_container_width=True)
    
    # Detailed table
    st.subheader("📊 Detalhes dos Top Usuários")
    
    display_df = top_users[['anon_id', 'score', 'class_label']].copy()
    display_df['score'] = display_df['score'].round(2)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

with col_right:
    # Distribution by class
    st.subheader("📈 Distribuição por Classe")
    
    class_counts = filtered_df['class_label'].value_counts()
    
    fig_pie = px.pie(
        values=class_counts.values,
        names=class_counts.index,
        title="Distribuição de Classificações",
        color=class_counts.index,
        color_discrete_map={
            'MOMENTO IDEAL': '#00CC66',
            'NUTRIR': '#FFB84D',
            'NÃO ABORDAR': '#FF6B6B'
        }
    )
    
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Score distribution histogram
    st.subheader("📊 Distribuição de Scores")
    
    fig_hist = px.histogram(
        filtered_df,
        x='score',
        nbins=20,
        title="Histograma de Scores",
        labels={'score': 'Score', 'count': 'Contagem'}
    )
    
    fig_hist.update_layout(height=300)
    st.plotly_chart(fig_hist, use_container_width=True)

# Score drivers analysis
st.markdown("---")
st.subheader("🎯 Análise de Drivers do Score")

# User selection
selected_user = st.selectbox(
    "Selecione um usuário para ver os drivers:",
    top_users['anon_id'].tolist()
)

if selected_user:
    user_data = filtered_df[filtered_df['anon_id'] == selected_user].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"### {selected_user}")
        st.metric("Score", f"{user_data['score']:.2f}")
        st.metric("Classificação", user_data['class_label'])
    
    with col2:
        if 'top_drivers_parsed' in user_data and user_data['top_drivers_parsed']:
            drivers = user_data['top_drivers_parsed']
            
            # Create bar chart for drivers
            drivers_df = pd.DataFrame([
                {'driver': k, 'contribution': v}
                for k, v in drivers.items()
            ])
            
            fig_drivers = px.bar(
                drivers_df,
                x='contribution',
                y='driver',
                orientation='h',
                title="Top 3 Componentes do Score",
                labels={'contribution': 'Contribuição', 'driver': 'Componente'}
            )
            
            fig_drivers.update_layout(height=250)
            st.plotly_chart(fig_drivers, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    Ready-to-Reform Dashboard v1.0.0 | Sistema LGPD-safe | Dados 100% anônimos
    </div>
    """,
    unsafe_allow_html=True
)

# Refresh button
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
