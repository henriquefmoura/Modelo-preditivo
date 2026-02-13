"""
Feature engineering for the reformas-momento-ideal project.
Calculates features from events to predict the ideal moment for reform.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter

from .config import FEATURE_CONFIG
from .event_schema import Event, safe_parse_json


class FeatureEngineer:
    """Feature engineering for Ready-to-Reform scoring."""
    
    def __init__(self, config=FEATURE_CONFIG):
        """
        Initialize the feature engineer.
        
        Args:
            config: FeatureConfig instance with configuration parameters
        """
        self.config = config
    
    def calculate_features(
        self, 
        events: pd.DataFrame, 
        reference_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate features for each anon_id from events data.
        
        Args:
            events: DataFrame with columns: event_time, channel, anon_id, 
                    event_name, event_props
            reference_date: Date to use as reference (default: today)
            
        Returns:
            DataFrame with features for each anon_id
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        # Ensure event_time is datetime
        if not pd.api.types.is_datetime64_any_dtype(events['event_time']):
            events['event_time'] = pd.to_datetime(events['event_time'])
        
        # Parse event_props JSON
        events['event_props_parsed'] = events['event_props'].apply(safe_parse_json)
        
        # Extract category from event_props
        events['category'] = events['event_props_parsed'].apply(
            lambda x: x.get('category') if isinstance(x, dict) else None
        )
        
        # Calculate features by anon_id
        features_list = []
        
        for anon_id in events['anon_id'].unique():
            user_events = events[events['anon_id'] == anon_id].copy()
            user_events = user_events.sort_values('event_time')
            
            features = self._calculate_user_features(user_events, reference_date)
            features['anon_id'] = anon_id
            features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        
        # Fill NaN values with 0
        features_df = features_df.fillna(0)
        
        return features_df
    
    def _calculate_user_features(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate features for a single user.
        
        Args:
            user_events: DataFrame with events for one anon_id
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with calculated features
        """
        features = {}
        
        # Recency features
        features['recency_days'] = self._calculate_recency(user_events, reference_date)
        
        # Frequency features
        features['freq_7d'] = self._calculate_frequency(
            user_events, reference_date, self.config.window_7d
        )
        features['freq_14d'] = self._calculate_frequency(
            user_events, reference_date, self.config.window_14d
        )
        features['freq_30d'] = self._calculate_frequency(
            user_events, reference_date, self.config.window_30d
        )
        
        # High intent features
        features['high_intent_7d'] = self._calculate_high_intent(
            user_events, reference_date, self.config.window_7d
        )
        
        # Category diversity
        features['category_diversity_14d'] = self._calculate_category_diversity(
            user_events, reference_date, self.config.window_14d
        )
        
        # Cart abandonment
        features['cart_abandon_7d'] = self._calculate_cart_abandon(
            user_events, reference_date, self.config.window_7d
        )
        
        # Reform bundles
        features['reform_bundle_14d'] = self._calculate_reform_bundle(
            user_events, reference_date, self.config.window_14d
        )
        
        return features
    
    def _calculate_recency(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime
    ) -> float:
        """
        Calculate days since last relevant event.
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            
        Returns:
            Days since last event (lower is better)
        """
        if len(user_events) == 0:
            return 999.0  # Very high value for no events
        
        last_event = user_events['event_time'].max()
        days_diff = (reference_date - last_event).total_seconds() / 86400.0
        return max(0.0, days_diff)
    
    def _calculate_frequency(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime, 
        window_days: int
    ) -> int:
        """
        Count events in the specified time window.
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            window_days: Time window in days
            
        Returns:
            Number of events in window
        """
        cutoff_date = reference_date - timedelta(days=window_days)
        recent_events = user_events[user_events['event_time'] >= cutoff_date]
        return len(recent_events)
    
    def _calculate_high_intent(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime, 
        window_days: int
    ) -> int:
        """
        Count high-intent events in the time window.
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            window_days: Time window in days
            
        Returns:
            Number of high-intent events
        """
        cutoff_date = reference_date - timedelta(days=window_days)
        recent_events = user_events[user_events['event_time'] >= cutoff_date]
        
        high_intent_count = recent_events[
            recent_events['event_name'].isin(self.config.high_intent_events)
        ].shape[0]
        
        return high_intent_count
    
    def _calculate_category_diversity(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime, 
        window_days: int
    ) -> int:
        """
        Count distinct categories accessed in the time window.
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            window_days: Time window in days
            
        Returns:
            Number of distinct categories
        """
        cutoff_date = reference_date - timedelta(days=window_days)
        recent_events = user_events[user_events['event_time'] >= cutoff_date]
        
        categories = recent_events['category'].dropna().unique()
        return len(categories)
    
    def _calculate_cart_abandon(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime, 
        window_days: int
    ) -> int:
        """
        Count cart abandonment instances (add_to_cart without begin_checkout).
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            window_days: Time window in days
            
        Returns:
            Number of cart abandonments
        """
        cutoff_date = reference_date - timedelta(days=window_days)
        recent_events = user_events[user_events['event_time'] >= cutoff_date]
        
        # Find add_to_cart events
        cart_adds = recent_events[recent_events['event_name'] == 'add_to_cart']
        
        abandon_count = 0
        abandon_window_hours = self.config.cart_abandon_hours
        
        for _, cart_add in cart_adds.iterrows():
            add_time = cart_add['event_time']
            checkout_window_end = add_time + timedelta(hours=abandon_window_hours)
            
            # Check if there's a begin_checkout in the next 24 hours
            checkouts = recent_events[
                (recent_events['event_name'] == 'begin_checkout') &
                (recent_events['event_time'] >= add_time) &
                (recent_events['event_time'] <= checkout_window_end)
            ]
            
            if len(checkouts) == 0:
                abandon_count += 1
        
        return abandon_count
    
    def _calculate_reform_bundle(
        self, 
        user_events: pd.DataFrame, 
        reference_date: datetime, 
        window_days: int
    ) -> int:
        """
        Detect if user accessed typical reform product bundles.
        
        Args:
            user_events: User's events DataFrame
            reference_date: Reference date
            window_days: Time window in days
            
        Returns:
            1 if bundle detected, 0 otherwise
        """
        cutoff_date = reference_date - timedelta(days=window_days)
        recent_events = user_events[user_events['event_time'] >= cutoff_date]
        
        # Get categories accessed
        categories = set(recent_events['category'].dropna().str.lower())
        
        # Check for bundle patterns
        for bundle in self.config.reform_bundles:
            bundle_set = set(bundle)
            if bundle_set.issubset(categories):
                return 1
        
        return 0
