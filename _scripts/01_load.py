"""Phase 1a — load the raw COSING CSV into DuckDB with format normalisation only.

No taxonomic decisions happen here. This step fixes encoding, column names, and
the CAS/date formatting problems catalogued in the plan (section 3.4), and
nothing else. Every original value is preserved alongside its normalised form.
"""

import csv
import datetime
import re
import sys

from common import DB, RAW_CSV, connect

# Source header -> snake_case. Note 'Ph.\xa0Eur. Name' carries a non-breaking
# space, so it can never be matched with a plain ASCII string.
COLUMNS = {
    "COSING Ref No": "ref_no",
    "INCI name": "inci_name",
    "INN name": "inn_name",
    "Ph.\xa0Eur. Name": "ph_eur_name",
    "CAS No": "cas_raw",
    "Chem/IUPAC Name / Description": "description",
    "Restriction": "restriction",
    "Function": "function_raw",
    "Update Date": "update_date_raw",
}

CAS_PLACEHOLDER = "999999-99-4"
CAS_TOKEN = re.compile(r"\d{2,7}-\d{2}-\d")
GENERIC_NOTE = re.compile(r"\(\s*generic\s*\)", re.IGNORECASE)


def split_cas(raw):
    """Return (cas_list, is_generic, had_placeholder, leftover_text).

    The source mixes ';', ' / ' and ',' as separators and appends '(generic)' /
    '(Generic)' notes. We extract every well-formed CAS token rather than trying
    to guess the separator, then keep whatever text did not parse so nothing is
    silently dropped.
    """
    is_generic = bool(GENERIC_NOTE.search(raw))
    cleaned = GENERIC_NOTE.sub(" ", raw)
    # A few rows carry a stray space inside the number itself
    # (ref 76681: '100209- 50-5'). Close those up before tokenising.
    cleaned = re.sub(r"(\d)\s*-\s*(\d)", r"\1-\2", cleaned)
    tokens = CAS_TOKEN.findall(cleaned)

    had_placeholder = CAS_PLACEHOLDER in tokens
    tokens = [t for t in tokens if t != CAS_PLACEHOLDER]

    leftover = CAS_TOKEN.sub(" ", cleaned)
    leftover = re.sub(r"[;,/\s]+", " ", leftover).strip()

    # de-duplicate, preserve order
    seen, out = set(), []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out, is_generic, had_placeholder, leftover


def parse_date(raw):
    raw = raw.strip()
    if not raw:
        return None
    return datetime.datetime.strptime(raw, "%d/%m/%Y").date()


def split_functions(raw):
    return [f.strip() for f in raw.split(",") if f.strip()]


def main():
    if not RAW_CSV.exists():
        sys.exit(f"missing {RAW_CSV}")

    with open(RAW_CSV, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = set(COLUMNS) - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"unexpected header, missing columns: {missing}")
        raw_rows = list(reader)

    rows = []
    stats = {"generic": 0, "placeholder": 0, "no_cas": 0, "leftover": 0}
    for r in raw_rows:
        rec = {new: r[old].strip() for old, new in COLUMNS.items()}
        cas, generic, placeholder, leftover = split_cas(rec["cas_raw"])

        stats["generic"] += generic
        stats["placeholder"] += placeholder
        stats["no_cas"] += not cas
        stats["leftover"] += bool(leftover)

        rec["ref_no"] = int(rec["ref_no"])
        rec["cas_raw"] = r["CAS No"]  # keep the original, spaces and all
        rec["cas_numbers"] = cas
        rec["cas_primary"] = cas[0] if cas else None
        rec["cas_is_generic"] = generic
        rec["cas_unparsed"] = leftover or None
        rec["functions"] = split_functions(rec["function_raw"])
        rec["update_date"] = parse_date(rec["update_date_raw"])
        for k in ("inn_name", "ph_eur_name", "restriction", "description"):
            rec[k] = rec[k] or None
        rows.append(rec)

    DB.unlink(missing_ok=True)
    con = connect()
    con.execute(
        """
        CREATE TABLE ingredient (
            ref_no           INTEGER PRIMARY KEY,
            inci_name        VARCHAR NOT NULL,
            inn_name         VARCHAR,
            ph_eur_name      VARCHAR,
            cas_raw          VARCHAR,
            cas_numbers      VARCHAR[],
            cas_primary      VARCHAR,
            cas_is_generic   BOOLEAN,
            cas_unparsed     VARCHAR,
            description      VARCHAR,
            restriction      VARCHAR,
            function_raw     VARCHAR,
            functions        VARCHAR[],
            update_date_raw  VARCHAR,
            update_date      DATE
        )
        """
    )
    cols = [
        "ref_no", "inci_name", "inn_name", "ph_eur_name", "cas_raw",
        "cas_numbers", "cas_primary", "cas_is_generic", "cas_unparsed",
        "description", "restriction", "function_raw", "functions",
        "update_date_raw", "update_date",
    ]
    con.executemany(
        f"INSERT INTO ingredient ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})",
        [[r[c] for c in cols] for r in rows],
    )

    n = con.execute("SELECT count(*) FROM ingredient").fetchone()[0]
    print(f"loaded {n} rows into {DB.name}")
    print(f"  CAS marked (generic)      : {stats['generic']}")
    print(f"  CAS placeholder dropped   : {stats['placeholder']}")
    print(f"  rows with no parseable CAS: {stats['no_cas']}")
    print(f"  rows with leftover CAS text: {stats['leftover']}")
    con.close()


if __name__ == "__main__":
    main()
