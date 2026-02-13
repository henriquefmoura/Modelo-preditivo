"""
Scoring module for the Ready-to-Reform score.
Calculates a 0-100 score indicating how ready a user is for a reform.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime

from .config import SCORING_CONFIG
from .event_schema import Score


class ReadyToReformScorer:
    """Calculate Ready-to-Reform scores from features."""
    
    def __init__(self, config=SCORING_CONFIG):
        """
        Initialize the scorer.
        
        Args:
            config: ScoringConfig instance with scoring parameters
        """
        self.config = config
    
    def calculate_scores(
        self, 
        features: pd.DataFrame,
        score_date: datetime = None
    ) -> List[Score]:
        """
        Calculate Ready-to-Reform scores for all users.
        
        Args:
            features: DataFrame with features for each anon_id
            score_date: Date for the score (default: today)
            
        Returns:
            List of Score objects
        """
        if score_date is None:
            score_date = datetime.now()
        
        scores = []
        
        for _, row in features.iterrows():
            score_value, components = self._calculate_user_score(row)
            class_label = self._classify_score(score_value)
            top_drivers = self._get_top_drivers(components)
            
            score = Score(
                anon_id=row['anon_id'],
                score=score_value,
                class_label=class_label,
                score_date=score_date,
                top_drivers=top_drivers
            )
            scores.append(score)
        
        return scores
    
    def _calculate_user_score(
        self, 
        features: pd.Series
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate score for a single user.
        
        Args:
            features: Series with user features
            
        Returns:
            Tuple of (total_score, component_scores)
        """
        components = {}
        
        # 1. Recency component (30%)
        # Lower recency is better, scale to 0-100
        recency_days = features.get('recency_days', 999)
        if recency_days >= 30:
            recency_score = 0
        elif recency_days <= 1:
            recency_score = 100
        else:
            # Linear decay from 100 at day 1 to 0 at day 30
            recency_score = 100 * (1 - (recency_days - 1) / 29)
        components['recency'] = recency_score * self.config.weight_recency
        
        # 2. High intent component (25%)
        # More high intent events = higher score
        high_intent = features.get('high_intent_7d', 0)
        high_intent_score = min(100, high_intent * 25)  # Cap at 100, each event worth 25 pts
        components['high_intent'] = high_intent_score * self.config.weight_high_intent
        
        # 3. Frequency component (20%)
        # Combine frequencies with more weight on recent
        freq_7d = features.get('freq_7d', 0)
        freq_14d = features.get('freq_14d', 0)
        freq_30d = features.get('freq_30d', 0)
        
        # Weighted average: 50% 7d, 30% 14d, 20% 30d
        weighted_freq = (0.5 * freq_7d + 0.3 * freq_14d + 0.2 * freq_30d)
        freq_score = min(100, weighted_freq * 5)  # Each weighted event worth 5 pts
        components['frequency'] = freq_score * self.config.weight_frequency
        
        # 4. Category diversity component (15%)
        # More categories = more engagement
        diversity = features.get('category_diversity_14d', 0)
        diversity_score = min(100, diversity * 20)  # Each category worth 20 pts
        components['diversity'] = diversity_score * self.config.weight_diversity
        
        # 5. Bundles/Abandonment component (10%)
        # Reform bundle is very positive, cart abandon is slightly positive (shows interest)
        reform_bundle = features.get('reform_bundle_14d', 0)
        cart_abandon = features.get('cart_abandon_7d', 0)
        
        bundle_score = 0
        if reform_bundle > 0:
            bundle_score += 70  # Bundle is strong signal
        if cart_abandon > 0:
            bundle_score += min(30, cart_abandon * 15)  # Each abandon adds some signal
        
        bundle_score = min(100, bundle_score)
        components['bundles_abandon'] = bundle_score * self.config.weight_bundles
        
        # Total score
        total_score = sum(components.values())
        total_score = min(self.config.max_score, max(0, total_score))
        
        return round(total_score, 2), components
    
    def _classify_score(self, score: float) -> str:
        """
        Classify score into categories.
        
        Args:
            score: Numeric score (0-100)
            
        Returns:
            Classification label
        """
        if score >= self.config.threshold_ideal:
            return "MOMENTO IDEAL"
        elif score >= self.config.threshold_nurture:
            return "NUTRIR"
        else:
            return "NÃO ABORDAR"
    
    def _get_top_drivers(
        self, 
        components: Dict[str, float],
        top_n: int = 3
    ) -> Dict[str, float]:
        """
        Get the top N score drivers.
        
        Args:
            components: Dictionary of score components
            top_n: Number of top drivers to return
            
        Returns:
            Dictionary with top N drivers and their contributions
        """
        # Sort components by value
        sorted_components = sorted(
            components.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Take top N
        top_drivers = dict(sorted_components[:top_n])
        
        # Round values
        top_drivers = {k: round(v, 2) for k, v in top_drivers.items()}
        
        return top_drivers
    
    def scores_to_dataframe(self, scores: List[Score]) -> pd.DataFrame:
        """
        Convert list of Score objects to DataFrame.
        
        Args:
            scores: List of Score objects
            
        Returns:
            DataFrame with score data
        """
        return pd.DataFrame([s.to_dict() for s in scores])
