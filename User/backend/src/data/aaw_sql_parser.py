"""
Parse aaw.sql dump and build a unified dataset for the chatbot (jobs, products, customers).
Output: CSV with columns compatible with aluminum_products (product_name, category, description, etc.)
"""
from __future__ import annotations

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Columns we need for the pipeline (preprocessor + retriever)
OUTPUT_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "description",
    "specifications",
    "applications",
    "price",
    "manufacturer",
]


def _parse_sql_value(s: str) -> Any:
    s = s.strip()
    if not s or s.upper() == "NULL":
        return None
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("''", "'").replace("\\r\\n", "\n").replace("\\n", "\n")
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _split_sql_values(row_str: str) -> List[str]:
    """Split a single row string (val1, val2, ...) into list of value strings, respecting quotes."""
    out: List[str] = []
    i = 0
    n = len(row_str)
    while i < n:
        while i < n and row_str[i] in " \t,":
            i += 1
        if i >= n:
            break
        if row_str[i] == "'":
            i += 1
            val = []
            while i < n:
                if row_str[i] == "'":
                    if i + 1 < n and row_str[i + 1] == "'":
                        val.append("'")
                        i += 2
                    else:
                        i += 1
                        break
                elif row_str[i] == "\\" and i + 1 < n:
                    val.append(row_str[i + 1])
                    i += 2
                else:
                    val.append(row_str[i])
                    i += 1
            out.append("'" + "".join(val) + "'")
        elif row_str[i] in "-" or row_str[i].isdigit():
            start = i
            if row_str[i] == "-":
                i += 1
            while i < n and (row_str[i].isdigit() or row_str[i] in "."):
                i += 1
            out.append(row_str[start:i])
        else:
            start = i
            while i < n and row_str[i] not in ",":
                i += 1
            out.append(row_str[start:i])
    return out


def _parse_values_block(col_names: List[str], values_str: str) -> List[List[Any]]:
    """Parse VALUES (...), (...) into list of rows."""
    rows_parsed: List[List[Any]] = []
    # Row boundary: "),\n(" or "), ("
    rows_raw = re.split(r"\),\s*\n?\s*\(", values_str)
    for r in rows_raw:
        r = r.strip().strip("()").strip()
        if not r:
            continue
        parts = _split_sql_values(r)
        if len(parts) == len(col_names):
            rows_parsed.append([_parse_sql_value(p) for p in parts])
        elif len(parts) > len(col_names):
            # Truncate if extra (e.g. trailing comma)
            rows_parsed.append([_parse_sql_value(p) for p in parts[: len(col_names)]])
    return rows_parsed


def _load_table(content: str, table_name: str) -> pd.DataFrame:
    """Load one table from SQL content; handle multiple INSERT blocks for same table."""
    all_cols: Optional[List[str]] = None
    all_rows: List[List[Any]] = []

    # Find every INSERT INTO `table_name` (...) VALUES ...
    pattern = re.compile(
        r"INSERT\s+INTO\s+[`\"]?" + re.escape(table_name) + r"[`\"]?\s*\(([^)]+)\)\s*VALUES\s*",
        re.IGNORECASE,
    )
    pos = 0
    while True:
        m = pattern.search(content, pos)
        if not m:
            break
        cols_str = m.group(1)
        col_names = [c.strip().strip("`").strip('"') for c in cols_str.split(",")]
        if all_cols is None:
            all_cols = col_names
        values_start = m.end()
        # End of block: next "INSERT INTO `table_name`" (same table) or end of file
        next_same = content.find("INSERT INTO `" + table_name + "`", values_start)
        if next_same < 0:
            next_same = content.find("INSERT INTO \"" + table_name + "\"", values_start)
        if next_same > 0:
            values_str = content[values_start:next_same].rstrip().rstrip(",").strip()
            pos = next_same
        else:
            values_str = content[values_start:].rstrip().rstrip(",").strip()
            # Remove trailing );
            if values_str.endswith(");"):
                values_str = values_str[:-2].rstrip().rstrip(",").strip()
            pos = len(content)
        rows = _parse_values_block(col_names, values_str)
        all_rows.extend(rows)
        if pos >= len(content):
            break

    if not all_cols or not all_rows:
        return pd.DataFrame()
    return pd.DataFrame(all_rows, columns=all_cols)


def _safe_str(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _build_combined_text(row: dict, product_map: Dict[int, dict], customer_map: Dict[str, dict]) -> str:
    """Build searchable text for a job row."""
    parts = [
        _safe_str(row.get("job_name") or row.get("jobName")),
        _safe_str(row.get("job_description") or row.get("jobDescription")),
        _safe_str(row.get("category")),
        _safe_str(row.get("stageType")),
        _safe_str(row.get("product_summary")),
        _safe_str(row.get("customer_company") or row.get("company")),
        _safe_str(row.get("customer_name")),
    ]
    return " ".join(p for p in parts if p).lower()


def build_aaw_dataset(
    sql_path: Path,
    output_path: Path,
    max_rows: int = 3000,
) -> pd.DataFrame:
    """
    Read aaw.sql, parse jobs, products, jobcustomer (and jobproducts if needed),
    build unified rows with product_name, category, description, etc. Save to CSV.
    """
    logger.info("Reading %s", sql_path)
    content = sql_path.read_text(encoding="utf-8", errors="replace")

    # Load tables
    jobs_df = _load_table(content, "jobs")
    products_df = _load_table(content, "products")
    jobcustomer_df = _load_table(content, "jobcustomer")
    jobproducts_df = _load_table(content, "jobproducts")

    if jobs_df.empty:
        logger.warning("No jobs table found in SQL; check table name")
        return pd.DataFrame()

    # Job lookup: jobId -> job row
    job_map: Dict[str, dict] = {}
    for _, r in jobs_df.iterrows():
        jid = r.get("jobId") or r.get("job_id")
        if jid is not None:
            job_map[str(jid)] = r.to_dict()

    # Product lookup: product_id -> row
    product_map: Dict[int, dict] = {}
    if not products_df.empty and "product_id" in products_df.columns:
        for _, r in products_df.iterrows():
            pid = r.get("product_id")
            if pid is not None:
                product_map[int(pid)] = r.to_dict()

    # Customer lookup: customerId -> row
    customer_map: Dict[str, dict] = {}
    if not jobcustomer_df.empty:
        cid_col = "customerId" if "customerId" in jobcustomer_df.columns else "customer_id"
        for _, r in jobcustomer_df.iterrows():
            cid = r.get(cid_col)
            if cid is not None:
                customer_map[str(cid)] = r.to_dict()

    # Build one record per job (flatten product JSON into text); then optionally add jobproduct rows to reach max_rows
    records: List[dict] = []
    seen = 0
    for _, job in jobs_df.iterrows():
        if seen >= max_rows:
            break
        job_id = job.get("jobId") or job.get("job_id")
        job_name = _safe_str(job.get("jobName") or job.get("job_name"))
        job_desc = _safe_str(job.get("jobDescription") or job.get("job_description"))
        category = _safe_str(job.get("category")) or "Residential"
        stage_type = _safe_str(job.get("stageType"))
        quote_amount = job.get("quoteAmount") or job.get("quote_amount")
        try:
            price = float(quote_amount) if quote_amount is not None else 0.0
        except (TypeError, ValueError):
            price = 0.0

        customer_id = _safe_str(job.get("customerId") or job.get("customer_id"))
        customer_info = customer_map.get(customer_id) or {}
        customer_name = _safe_str(customer_info.get("firstName", "")) + " " + _safe_str(customer_info.get("lastName", ""))
        company = _safe_str(customer_info.get("company", ""))

        product_json = job.get("product") or job.get("product_json")
        product_summary_parts: List[str] = []
        if product_json:
            try:
                if isinstance(product_json, str):
                    items = json.loads(product_json)
                else:
                    items = product_json
                for it in items if isinstance(items, list) else [items]:
                    if not isinstance(it, dict):
                        continue
                    pname = it.get("productName") or it.get("product_name", "")
                    pcode = it.get("productCode") or it.get("product_code", "")
                    qty = it.get("quantity", 0)
                    color = it.get("color", "")
                    product_summary_parts.append(f"{pname} ({pcode}) x{qty} {color}")
            except (json.JSONDecodeError, TypeError):
                product_summary_parts.append(_safe_str(product_json)[:500])
        product_summary = "; ".join(product_summary_parts) if product_summary_parts else ""

        description = job_desc or product_summary or job_name
        specifications = product_summary
        applications = stage_type or "Supply Only"

        record = {
            "product_id": seen + 1,
            "product_name": job_name or f"Job {job_id}",
            "category": category,
            "description": description[:2000] if description else "",
            "specifications": specifications[:2000] if specifications else "",
            "applications": applications,
            "price": price,
            "manufacturer": company or "AAW",
            "job_id": job_id,
            "job_name": job_name,
            "job_description": job_desc,
            "stageType": stage_type,
            "product_summary": product_summary,
            "customer_name": customer_name,
            "customer_company": company,
            "expected_delivery": _safe_str(job.get("expectedDeliveryDate") or job.get("expected_delivery_date")),
            "status": _safe_str(job.get("status")),
        }
        records.append(record)
        seen += 1

    # If we need more rows, add one per job-product line (from jobproducts table)
    if len(records) < max_rows and not jobproducts_df.empty and "jobId" in jobproducts_df.columns:
        jp_seen = 0
        for _, jp in jobproducts_df.iterrows():
            if len(records) >= max_rows:
                break
            job_id = _safe_str(jp.get("jobId") or jp.get("job_id"))
            job = job_map.get(job_id)
            if not job:
                continue
            product_id = jp.get("productId") or jp.get("product_id")
            try:
                prod = (product_map.get(int(product_id)) or {}) if product_id is not None else {}
            except (TypeError, ValueError):
                prod = {}
            product_name = _safe_str(prod.get("product_name", "")) or _safe_str(jp.get("product_name", ""))
            qty = jp.get("quantity", 0)
            color = _safe_str(jp.get("color", ""))
            job_name = _safe_str(job.get("jobName") or job.get("job_name"))
            job_desc = _safe_str(job.get("jobDescription") or job.get("job_description"))
            category = _safe_str(job.get("category")) or "Residential"
            customer_id = _safe_str(job.get("customerId") or job.get("customer_id"))
            customer_info = customer_map.get(customer_id) or {}
            company = _safe_str(customer_info.get("company", ""))

            line_desc = f"{product_name} x{qty} {color}".strip()
            if job_desc:
                line_desc = job_desc[:500] + " | " + line_desc

            record = {
                "product_id": len(records) + 1,
                "product_name": job_name or f"Job {job_id}",
                "category": category,
                "description": line_desc[:2000],
                "specifications": f"{product_name} ({prod.get('product_code', '')}) x{qty} {color}",
                "applications": _safe_str(job.get("stageType")) or "Supply Only",
                "price": 0.0,
                "manufacturer": company or "AAW",
                "job_id": job_id,
                "job_name": job_name,
                "job_description": job_desc,
                "stageType": _safe_str(job.get("stageType")),
                "product_summary": line_desc,
                "customer_name": _safe_str(customer_info.get("firstName", "")) + " " + _safe_str(customer_info.get("lastName", "")),
                "customer_company": company,
                "expected_delivery": _safe_str(job.get("expectedDeliveryDate") or job.get("expected_delivery_date")),
                "status": _safe_str(job.get("status")),
            }
            records.append(record)
            jp_seen += 1
        logger.info("Added %d job-product rows (total %d)", jp_seen, len(records))

    df = pd.DataFrame(records)

    # Ensure required columns for pipeline
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col != "price" else 0.0

    df = df[OUTPUT_COLUMNS + [c for c in df.columns if c not in OUTPUT_COLUMNS]]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Wrote %d rows to %s", len(df), output_path)
    return df


def build_preprocessed_csv(raw_csv_path: Path, preprocessed_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw aluminum_products CSV, run preprocessor, save to aluminum_products_preprocessed.csv.
    Use this for consistent embeddings and more accurate answers.
    """
    from src.data.preprocessor import DataPreprocessor
    if preprocessed_path is None:
        preprocessed_path = raw_csv_path.parent / "aluminum_products_preprocessed.csv"
    df = pd.read_csv(raw_csv_path)
    preprocessor = DataPreprocessor(df)
    preprocessor.preprocess_all()
    out = preprocessor.get_processed_data()
    preprocessed_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(preprocessed_path, index=False)
    logger.info("Wrote preprocessed %d rows to %s", len(out), preprocessed_path)
    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build aluminum_products dataset from aaw.sql")
    parser.add_argument("--sql", type=Path, default=Path("aaw.sql"), help="Path to aaw.sql")
    parser.add_argument("--output", type=Path, default=Path("data/aluminum_products.csv"), help="Output CSV path")
    parser.add_argument("--max-rows", type=int, default=3000, help="Max rows to export")
    parser.add_argument("--no-preprocess", action="store_true", help="Do not write aluminum_products_preprocessed.csv")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    df = build_aaw_dataset(args.sql, args.output, args.max_rows)
    if not df.empty and not args.no_preprocess:
        build_preprocessed_csv(args.output, args.output.parent / "aluminum_products_preprocessed.csv")


if __name__ == "__main__":
    main()
