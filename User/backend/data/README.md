# Dataset (AAW jobs & products)

- **aluminum_products.csv** – raw dataset from `aaw.sql`.
- **aluminum_products_preprocessed.csv** – cleaned data with `combined_text` (used at startup when present for more accurate embeddings).

## Rebuild from aaw.sql

From the project root:

```bash
python -m src.data.aaw_sql_parser --sql aaw.sql --output data/aluminum_products.csv --max-rows 3000
```

This parses the SQL dump, writes `aluminum_products.csv`, then runs the preprocessor and overwrites `aluminum_products_preprocessed.csv`. Use `--no-preprocess` to skip the preprocessed file.

## After rebuilding

Restart the app so it reloads the CSV, preprocesses it, and rebuilds embeddings:

```bash
python -m src.api.app
# or
python -m src.main
```

Restart the app to load the preprocessed CSV (when present) and rebuild embeddings; no separate train step.
