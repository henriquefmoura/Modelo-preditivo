"""
Generate sample fake events data for demo and testing.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random
from pathlib import Path


def generate_sample_events(
    num_users: int = 100,
    days_back: int = 30,
    output_path: Path = None
) -> pd.DataFrame:
    """
    Generate fake events data for demonstration.
    
    Args:
        num_users: Number of anonymous users
        days_back: Number of days of history to generate
        output_path: Optional path to save CSV
        
    Returns:
        DataFrame with sample events
    """
    # Event types with probabilities
    event_types = [
        ("page_view", 0.30),
        ("product_view", 0.20),
        ("add_to_cart", 0.15),
        ("submit_quote", 0.08),
        ("whatsapp_quote_request", 0.07),
        ("scan_qr_service", 0.05),
        ("talk_to_consultant", 0.05),
        ("begin_checkout", 0.05),
        ("search", 0.05)
    ]
    
    # Product categories
    categories = [
        "piso", "rodape", "tinta", "massa", "lixa",
        "azulejo", "rejunte", "porta", "fechadura",
        "janela", "persiana", "lampada", "tomada",
        "cimento", "areia", "ferramentas"
    ]
    
    # Channels
    channels = ["web", "app", "store", "whatsapp"]
    
    events = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Generate users with different behavior patterns
    for user_id in range(num_users):
        anon_id = f"anon_{user_id:05d}"
        
        # Determine user engagement level
        engagement = random.choice(["high", "medium", "low"])
        
        if engagement == "high":
            num_events = random.randint(15, 50)
            high_intent_prob = 0.3
        elif engagement == "medium":
            num_events = random.randint(5, 15)
            high_intent_prob = 0.15
        else:
            num_events = random.randint(1, 5)
            high_intent_prob = 0.05
        
        # Generate events for this user
        for _ in range(num_events):
            # Random timestamp
            days_offset = random.uniform(0, days_back)
            event_time = end_date - timedelta(days=days_offset)
            
            # Select event type
            if random.random() < high_intent_prob:
                # High intent event
                high_intent_events = [
                    "submit_quote", "whatsapp_quote_request", 
                    "scan_qr_service", "talk_to_consultant", "begin_checkout"
                ]
                event_name = random.choice(high_intent_events)
            else:
                # Regular event based on probabilities
                event_name = random.choices(
                    [e[0] for e in event_types],
                    weights=[e[1] for e in event_types]
                )[0]
            
            # Channel
            channel = random.choice(channels)
            
            # Event properties
            event_props = {}
            
            # Add category for product-related events
            if event_name in ["product_view", "add_to_cart", "submit_quote"]:
                # Higher chance of bundle categories for engaged users
                if engagement == "high" and random.random() < 0.4:
                    # Generate bundle (e.g., piso + rodape)
                    bundle_categories = random.choice([
                        ["piso", "rodape"],
                        ["tinta", "massa", "lixa"],
                        ["azulejo", "rejunte"]
                    ])
                    event_props["category"] = random.choice(bundle_categories)
                else:
                    event_props["category"] = random.choice(categories)
                
                # Add value
                event_props["value"] = round(random.uniform(50, 5000), 2)
            
            # Add search query for search events
            if event_name == "search":
                search_terms = [
                    "piso laminado", "tinta parede", "azulejo banheiro",
                    "porta madeira", "janela aluminio", "reforma completa"
                ]
                event_props["query"] = random.choice(search_terms)
            
            # Create event
            event = {
                "event_time": event_time.isoformat(),
                "channel": channel,
                "anon_id": anon_id,
                "event_name": event_name,
                "event_props": json.dumps(event_props),
                "ingestion_time": event_time.isoformat()
            }
            
            events.append(event)
    
    # Create DataFrame
    df = pd.DataFrame(events)
    df = df.sort_values("event_time", ascending=False)
    
    # Save to CSV if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Generated {len(df)} sample events for {num_users} users")
        print(f"Saved to: {output_path}")
    
    return df


if __name__ == "__main__":
    # Generate sample data
    from config import SAMPLE_DIR
    
    output_file = SAMPLE_DIR / "events_sample.csv"
    generate_sample_events(
        num_users=100,
        days_back=30,
        output_path=output_file
    )
