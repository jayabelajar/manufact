# Dashboard Notes

This folder contains the Inventara Streamlit dashboard for exploring production achievement, product quality, machine downtime, and production cost.

Run it from the project root:

```bash
python -m streamlit run dashboard/app.py
```

The app reads `data/processed/inventara_clean.csv`. If the processed file is missing, it falls back to the raw CSV and applies the Python cleaning pipeline.
