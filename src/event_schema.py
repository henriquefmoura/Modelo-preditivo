"""
Event schema definitions and validation for the reformas-momento-ideal project.
Defines the structure of events and provides utilities for parsing and validation.
"""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any


@dataclass
class Event:
    """
    Represents a single event in the omnichannel system.
    All events are anonymous (LGPD-safe) with no personal data.
    """
    event_time: datetime
    channel: str  # web|app|store|whatsapp
    anon_id: str  # anonymous identifier
    event_name: str
    event_props: Dict[str, Any]
    ingestion_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate event data."""
        valid_channels = {"web", "app", "store", "whatsapp"}
        if self.channel not in valid_channels:
            raise ValueError(f"Invalid channel: {self.channel}. Must be one of {valid_channels}")
        
        if not self.anon_id:
            raise ValueError("anon_id cannot be empty")
        
        if not self.event_name:
            raise ValueError("event_name cannot be empty")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create an Event from a dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            Event instance
        """
        # Parse event_time
        event_time = data.get("event_time")
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
        elif not isinstance(event_time, datetime):
            raise ValueError("event_time must be a datetime or ISO string")
        
        # Parse ingestion_time
        ingestion_time = data.get("ingestion_time")
        if ingestion_time:
            if isinstance(ingestion_time, str):
                ingestion_time = datetime.fromisoformat(ingestion_time.replace('Z', '+00:00'))
        
        # Parse event_props if it's a JSON string
        event_props = data.get("event_props", {})
        if isinstance(event_props, str):
            try:
                event_props = json.loads(event_props) if event_props else {}
            except json.JSONDecodeError:
                event_props = {}
        
        return cls(
            event_time=event_time,
            channel=data["channel"],
            anon_id=data["anon_id"],
            event_name=data["event_name"],
            event_props=event_props or {},
            ingestion_time=ingestion_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Event to dictionary for serialization.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "event_time": self.event_time.isoformat(),
            "channel": self.channel,
            "anon_id": self.anon_id,
            "event_name": self.event_name,
            "event_props": json.dumps(self.event_props) if self.event_props else "{}",
            "ingestion_time": self.ingestion_time.isoformat() if self.ingestion_time else None
        }
    
    def get_category(self) -> Optional[str]:
        """Extract category from event_props if available."""
        return self.event_props.get("category") if self.event_props else None
    
    def get_value(self) -> Optional[float]:
        """Extract value from event_props if available."""
        if self.event_props and "value" in self.event_props:
            try:
                return float(self.event_props["value"])
            except (ValueError, TypeError):
                return None
        return None


@dataclass
class Score:
    """
    Represents a Ready-to-Reform score for an anonymous user.
    """
    anon_id: str
    score: float
    class_label: str  # MOMENTO IDEAL | NUTRIR | NÃO ABORDAR
    score_date: datetime
    top_drivers: Dict[str, float]  # Top 3 score components
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Score to dictionary for serialization.
        
        Returns:
            Dictionary representation of the score
        """
        return {
            "anon_id": self.anon_id,
            "score": self.score,
            "class_label": self.class_label,
            "score_date": self.score_date.date().isoformat() if isinstance(self.score_date, datetime) else self.score_date,
            "top_drivers": json.dumps(self.top_drivers)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Score":
        """
        Create a Score from a dictionary.
        
        Args:
            data: Dictionary containing score data
            
        Returns:
            Score instance
        """
        score_date = data.get("score_date")
        if isinstance(score_date, str):
            score_date = datetime.fromisoformat(score_date)
        
        top_drivers = data.get("top_drivers", {})
        if isinstance(top_drivers, str):
            try:
                top_drivers = json.loads(top_drivers)
            except json.JSONDecodeError:
                top_drivers = {}
        
        return cls(
            anon_id=data["anon_id"],
            score=float(data["score"]),
            class_label=data["class_label"],
            score_date=score_date,
            top_drivers=top_drivers
        )


def safe_parse_json(json_str: Optional[str]) -> Dict[str, Any]:
    """
    Safely parse JSON string, returning empty dict on failure.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed dictionary or empty dict if parsing fails
    """
    if not json_str:
        return {}
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}
