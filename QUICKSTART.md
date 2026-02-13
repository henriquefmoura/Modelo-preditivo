# Reformas-Momento-Ideal - Quick Reference

## 🚀 Quick Start Commands

### Local Development (Sample Data)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data
python src/generate_sample_data.py

# 3. Run scoring job
python src/run_daily_score.py --local_sample

# 4. Start API (in one terminal)
uvicorn api.app:app --reload --port 8000

# 5. Start Dashboard (in another terminal)
streamlit run dashboard/streamlit_app.py
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Score with sample data
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"use_sample": true}'

# Score custom events
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "event_time": "2024-01-15T10:30:00",
        "channel": "web",
        "anon_id": "test_user",
        "event_name": "submit_quote",
        "event_props": {"category": "piso"}
      }
    ]
  }'
```

## 📊 System Overview

### Features (8 per user)
- `recency_days` - Days since last event
- `freq_7d`, `freq_14d`, `freq_30d` - Event frequencies
- `high_intent_7d` - High-intent events
- `category_diversity_14d` - Category exploration
- `cart_abandon_7d` - Cart abandonments
- `reform_bundle_14d` - Bundle detection

### Scoring (0-100)
- 30% Recency
- 25% High Intent
- 20% Frequency
- 15% Diversity
- 10% Bundles/Abandon

### Classification
- ≥70: **MOMENTO IDEAL**
- 40-69: **NUTRIR**
- <40: **NÃO ABORDAR**

## 🔧 Configuration

### Environment Variables

```bash
# BigQuery (optional for production)
export BQ_PROJECT_ID="your-gcp-project"
export BQ_DATASET="reformas"
export BQ_CREDENTIALS_JSON="/path/to/credentials.json"
```

### Adjusting Scoring Weights

Edit `src/config.py`:

```python
SCORING_CONFIG = ScoringConfig(
    weight_recency=0.30,      # 30%
    weight_high_intent=0.25,  # 25%
    weight_frequency=0.20,    # 20%
    weight_diversity=0.15,    # 15%
    weight_bundles=0.10,      # 10%
    threshold_ideal=70.0,     # ≥70 = IDEAL
    threshold_nurture=40.0    # 40-69 = NUTRIR
)
```

## 🗄️ BigQuery Setup

1. Create tables:
```bash
bq query --use_legacy_sql=false < sql/bigquery_events.sql
```

2. Ingest events to `events` table
3. Run scoring to populate `scores_ready` table

## 🤖 GitHub Actions

### Setup Secrets
In GitHub repository settings:
- `BQ_PROJECT_ID` - Your GCP project ID
- `BQ_DATASET` - Dataset name (default: "reformas")
- `BQ_CREDENTIALS_JSON` - Service account JSON key

### Manual Trigger
Actions → Daily Ready-to-Reform Scoring → Run workflow

## 📈 Dashboard Features

- Top 50 users ranking
- Class distribution (pie chart)
- Score histogram
- Driver analysis per user
- Filters: class, score range
- Data source: Local CSV or BigQuery

## 🔒 LGPD Compliance

✅ No personal data:
- ❌ No name, CPF, phone, email, address
- ✅ Only anonymous IDs (`anon_id`)
- ✅ Behavioral events only

## 📝 File Structure

```
reformas-momento-ideal/
├── src/               # Core logic
├── api/               # REST API
├── dashboard/         # UI
├── sql/               # Database schemas
├── data/sample/       # Sample data
└── .github/workflows/ # Automation
```

## 🐛 Troubleshooting

### "Sample data not found"
```bash
python src/generate_sample_data.py
```

### "BigQuery not available"
```bash
pip install google-cloud-bigquery
export BQ_CREDENTIALS_JSON="/path/to/creds.json"
```

### "Module not found"
```bash
pip install -r requirements.txt
```

## 📞 Support

For issues or questions, check:
1. README.md - Full documentation
2. API docs - http://localhost:8000/docs
3. GitHub Issues

---

**Version:** 1.0.0  
**Last Updated:** 2024-02-13
