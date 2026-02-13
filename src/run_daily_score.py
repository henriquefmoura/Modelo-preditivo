"""
Daily scoring job for the Ready-to-Reform score.
Reads events from BigQuery (or local CSV), calculates features and scores,
and writes results back to BigQuery (or local CSV).
"""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    validate_bq_config,
    get_sample_events_path,
    ensure_directories,
    DATA_DIR
)
from src.features import FeatureEngineer
from src.scoring import ReadyToReformScorer
from src.bq_io import (
    BigQueryIO, 
    load_events_from_csv, 
    save_scores_to_csv,
    BIGQUERY_AVAILABLE
)


def run_scoring_job(
    use_local_sample: bool = False,
    lookback_days: int = 30,
    output_csv: Path = None
) -> None:
    """
    Run the daily scoring job.
    
    Args:
        use_local_sample: If True, use local CSV instead of BigQuery
        lookback_days: Number of days to look back for events
        output_csv: Optional path to save scores as CSV
    """
    print("=" * 60)
    print("Ready-to-Reform Daily Scoring Job")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Mode: {'Local Sample' if use_local_sample else 'BigQuery'}")
    print(f"Lookback days: {lookback_days}")
    print()
    
    # Ensure directories exist
    ensure_directories()
    
    # Step 1: Load events
    print("Step 1: Loading events...")
    
    if use_local_sample:
        events_path = get_sample_events_path()
        
        if not events_path.exists():
            print(f"ERROR: Sample events file not found: {events_path}")
            print("Generate it first with: python src/generate_sample_data.py")
            sys.exit(1)
        
        events_df = load_events_from_csv(events_path)
        print(f"✓ Loaded {len(events_df)} events from {events_path}")
    else:
        if not BIGQUERY_AVAILABLE:
            print("ERROR: google-cloud-bigquery not installed")
            print("Install it with: pip install google-cloud-bigquery")
            sys.exit(1)
        
        if not validate_bq_config():
            print("ERROR: BigQuery configuration invalid")
            sys.exit(1)
        
        bq = BigQueryIO()
        
        # Test connection
        if not bq.test_connection():
            sys.exit(1)
        
        # Load events
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        events_df = bq.read_events(start_date, end_date)
        print(f"✓ Loaded {len(events_df)} events from BigQuery")
    
    if len(events_df) == 0:
        print("WARNING: No events found, nothing to score")
        sys.exit(0)
    
    print(f"  - Unique users: {events_df['anon_id'].nunique()}")
    print(f"  - Date range: {events_df['event_time'].min()} to {events_df['event_time'].max()}")
    print()
    
    # Step 2: Calculate features
    print("Step 2: Calculating features...")
    
    engineer = FeatureEngineer()
    features_df = engineer.calculate_features(events_df)
    
    print(f"✓ Calculated features for {len(features_df)} users")
    print(f"  - Features: {list(features_df.columns)}")
    print()
    
    # Step 3: Calculate scores
    print("Step 3: Calculating scores...")
    
    scorer = ReadyToReformScorer()
    scores = scorer.calculate_scores(features_df)
    
    print(f"✓ Calculated {len(scores)} scores")
    
    # Score distribution
    class_counts = {}
    for score in scores:
        class_counts[score.class_label] = class_counts.get(score.class_label, 0) + 1
    
    print(f"  - Distribution:")
    for class_label, count in sorted(class_counts.items()):
        percentage = (count / len(scores)) * 100
        print(f"    • {class_label}: {count} ({percentage:.1f}%)")
    
    # Top scores
    sorted_scores = sorted(scores, key=lambda x: x.score, reverse=True)
    print(f"  - Top 5 scores:")
    for i, score in enumerate(sorted_scores[:5], 1):
        print(f"    {i}. {score.anon_id}: {score.score:.2f} ({score.class_label})")
    print()
    
    # Step 4: Save scores
    print("Step 4: Saving scores...")
    
    if use_local_sample or output_csv:
        # Save to CSV
        if output_csv:
            csv_path = output_csv
        else:
            csv_path = DATA_DIR / "processed" / f"scores_{datetime.now().strftime('%Y%m%d')}.csv"
        
        save_scores_to_csv(scores, csv_path)
    else:
        # Save to BigQuery
        bq.write_scores(scores)
    
    print()
    print("=" * 60)
    print(f"✓ Job completed successfully at {datetime.now().isoformat()}")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run daily Ready-to-Reform scoring job"
    )
    
    parser.add_argument(
        "--local_sample",
        action="store_true",
        help="Use local sample CSV instead of BigQuery"
    )
    
    parser.add_argument(
        "--lookback_days",
        type=int,
        default=30,
        help="Number of days to look back for events (default: 30)"
    )
    
    parser.add_argument(
        "--output_csv",
        type=str,
        help="Optional path to save scores as CSV"
    )
    
    args = parser.parse_args()
    
    output_csv = Path(args.output_csv) if args.output_csv else None
    
    try:
        run_scoring_job(
            use_local_sample=args.local_sample,
            lookback_days=args.lookback_days,
            output_csv=output_csv
        )
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
