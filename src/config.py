"""
Configuration management for the reformas-momento-ideal project.
Handles environment variables and project settings.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"
SQL_DIR = PROJECT_ROOT / "sql"

# BigQuery configuration
BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", "")
BQ_DATASET = os.getenv("BQ_DATASET", "reformas")
BQ_EVENTS_TABLE = "events"
BQ_SCORES_TABLE = "scores_ready"

# Credentials
BQ_CREDENTIALS_JSON = os.getenv("BQ_CREDENTIALS_JSON", "")


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    
    # Time windows for feature calculation (days)
    window_7d: int = 7
    window_14d: int = 14
    window_30d: int = 30
    
    # High intent events
    high_intent_events: tuple = (
        "submit_quote",
        "whatsapp_quote_request",
        "scan_qr_service",
        "talk_to_consultant",
        "begin_checkout"
    )
    
    # Reform bundle patterns (category combinations)
    reform_bundles: tuple = (
        ("piso", "rodape"),
        ("tinta", "massa", "lixa"),
        ("azulejo", "rejunte"),
        ("porta", "fechadura"),
        ("janela", "persiana")
    )
    
    # Cart abandonment window (hours)
    cart_abandon_hours: int = 24


@dataclass
class ScoringConfig:
    """Configuration for the Ready-to-Reform score."""
    
    # Score weights (must sum to 1.0)
    weight_recency: float = 0.30
    weight_high_intent: float = 0.25
    weight_frequency: float = 0.20
    weight_diversity: float = 0.15
    weight_bundles: float = 0.10
    
    # Score thresholds for classification
    threshold_ideal: float = 70.0  # >= 70: MOMENTO IDEAL
    threshold_nurture: float = 40.0  # 40-69: NUTRIR, <40: NÃO ABORDAR
    
    # Maximum score
    max_score: float = 100.0
    
    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = (self.weight_recency + self.weight_high_intent + 
                 self.weight_frequency + self.weight_diversity + 
                 self.weight_bundles)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


# Default configurations
FEATURE_CONFIG = FeatureConfig()
SCORING_CONFIG = ScoringConfig()


def get_bq_credentials_path() -> Optional[Path]:
    """
    Get path to BigQuery credentials file.
    
    Returns:
        Path to credentials JSON file if available, None otherwise.
    """
    if BQ_CREDENTIALS_JSON:
        creds_path = Path(BQ_CREDENTIALS_JSON)
        if creds_path.exists():
            return creds_path
    return None


def validate_bq_config() -> bool:
    """
    Validate that BigQuery configuration is properly set.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    if not BQ_PROJECT_ID:
        print("ERROR: BQ_PROJECT_ID environment variable not set")
        return False
    
    if not BQ_DATASET:
        print("ERROR: BQ_DATASET environment variable not set")
        return False
    
    if not BQ_CREDENTIALS_JSON:
        print("WARNING: BQ_CREDENTIALS_JSON not set, will try default credentials")
    
    return True


def get_sample_events_path() -> Path:
    """Get path to sample events CSV file."""
    return SAMPLE_DIR / "events_sample.csv"


def ensure_directories():
    """Ensure all required directories exist."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
