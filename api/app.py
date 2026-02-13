"""
FastAPI application for the Ready-to-Reform scoring API.
Provides endpoints to calculate scores for anonymous users.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_sample_events_path, validate_bq_config
from src.event_schema import Event
from src.features import FeatureEngineer
from src.scoring import ReadyToReformScorer
from src.bq_io import BigQueryIO, load_events_from_csv, BIGQUERY_AVAILABLE


# Initialize FastAPI app
app = FastAPI(
    title="Ready-to-Reform Scoring API",
    description="API for calculating Ready-to-Reform scores from omnichannel events",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class EventInput(BaseModel):
    """Input model for a single event."""
    event_time: str = Field(..., description="ISO timestamp of the event")
    channel: str = Field(..., description="Channel: web|app|store|whatsapp")
    anon_id: str = Field(..., description="Anonymous user identifier")
    event_name: str = Field(..., description="Event name")
    event_props: Dict[str, Any] = Field(default_factory=dict, description="Event properties")
    
    class Config:
        schema_extra = {
            "example": {
                "event_time": "2024-01-15T10:30:00",
                "channel": "web",
                "anon_id": "anon_12345",
                "event_name": "submit_quote",
                "event_props": {"category": "piso", "value": 1500.0}
            }
        }


class ScoreRequest(BaseModel):
    """Request model for scoring."""
    events: Optional[List[EventInput]] = Field(None, description="List of events to score")
    anon_ids: Optional[List[str]] = Field(None, description="List of anon_ids to score from BigQuery")
    use_sample: bool = Field(False, description="Use sample data for demo")
    
    class Config:
        schema_extra = {
            "example": {
                "events": [
                    {
                        "event_time": "2024-01-15T10:30:00",
                        "channel": "web",
                        "anon_id": "anon_12345",
                        "event_name": "submit_quote",
                        "event_props": {"category": "piso"}
                    }
                ]
            }
        }


class ScoreResponse(BaseModel):
    """Response model for a score."""
    anon_id: str
    score: float
    class_label: str
    top_drivers: Dict[str, float]
    
    class Config:
        schema_extra = {
            "example": {
                "anon_id": "anon_12345",
                "score": 75.5,
                "class_label": "MOMENTO IDEAL",
                "top_drivers": {
                    "recency": 30.0,
                    "high_intent": 25.0,
                    "frequency": 20.5
                }
            }
        }


class ScoreListResponse(BaseModel):
    """Response model for list of scores."""
    scores: List[ScoreResponse]
    count: int
    timestamp: str


# Global instances
engineer = FeatureEngineer()
scorer = ReadyToReformScorer()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Ready-to-Reform Scoring API",
        "version": "1.0.0",
        "endpoints": {
            "/score": "POST - Calculate scores from events",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bigquery_available": BIGQUERY_AVAILABLE
    }


@app.post("/score", response_model=ScoreListResponse)
async def calculate_score(request: ScoreRequest):
    """
    Calculate Ready-to-Reform scores.
    
    Supports three modes:
    1. Provide events directly in the request
    2. Provide anon_ids to fetch from BigQuery
    3. Use sample data for demo (use_sample=true)
    """
    try:
        # Determine data source
        if request.use_sample:
            # Use sample data
            sample_path = get_sample_events_path()
            if not sample_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Sample data not found. Generate it first with: python src/generate_sample_data.py"
                )
            
            events_df = load_events_from_csv(sample_path)
            
        elif request.events:
            # Use provided events
            events_data = []
            for event_input in request.events:
                event_dict = event_input.dict()
                events_data.append(event_dict)
            
            events_df = pd.DataFrame(events_data)
            events_df['event_time'] = pd.to_datetime(events_df['event_time'])
            
            # Convert event_props dict to JSON string
            import json
            events_df['event_props'] = events_df['event_props'].apply(json.dumps)
            
        elif request.anon_ids:
            # Fetch from BigQuery
            if not BIGQUERY_AVAILABLE:
                raise HTTPException(
                    status_code=500,
                    detail="BigQuery not available. Install google-cloud-bigquery"
                )
            
            if not validate_bq_config():
                raise HTTPException(
                    status_code=500,
                    detail="BigQuery configuration invalid. Set BQ_PROJECT_ID and BQ_CREDENTIALS_JSON"
                )
            
            bq = BigQueryIO()
            from datetime import timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            events_df = bq.read_events(
                start_date=start_date,
                end_date=end_date,
                anon_ids=request.anon_ids
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'events', 'anon_ids', or set 'use_sample=true'"
            )
        
        if len(events_df) == 0:
            raise HTTPException(
                status_code=404,
                detail="No events found for the given criteria"
            )
        
        # Calculate features
        features_df = engineer.calculate_features(events_df)
        
        # Calculate scores
        scores = scorer.calculate_scores(features_df)
        
        # Format response
        score_responses = []
        for score in scores:
            score_responses.append(
                ScoreResponse(
                    anon_id=score.anon_id,
                    score=score.score,
                    class_label=score.class_label,
                    top_drivers=score.top_drivers
                )
            )
        
        return ScoreListResponse(
            scores=score_responses,
            count=len(score_responses),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating scores: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
