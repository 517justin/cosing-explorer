"""Fetch the full current CosIng ingredient inventory (~33,654 entries).

Method, and why it is not "scrape 33,654 detail pages":

The CosIng UI is backed by a public search API. One POST returns up to 200
ingredient records complete with INCI name, CAS, EC, chemical description and
functions -- the same fields as the 2019 CSV, plus status, SCCS opinions and
conditions of use. So the whole inventory is ~170 requests, not ~34,000.

THE TRAP: the index caps deep paging at 10,000 records (page 50 at pageSize
200). Page 51 does not error -- it returns an empty result list AND
totalResults 0. A naive loop reads that as "done" and reports success holding
30% of the data. So the inventory is partitioned by substanceId range, each
partition kept under the cap, and the run fails loudly if the ids collected do
not match the total the API reports.

Provenance: European Commission, reused under CC BY 4.0 per Commission Decision
2011/833/EU. robots.txt carries no rule against this path. Requests are paced
one per second.

Output is written alongside, never over, the read-only 2019 snapshot:
`substanceId` is the same identifier as `COSING Ref No`, verified by INCI name
on a sample, so the two can be compared row by row.
"""

import csv
import json
import time
import urllib.request
import uuid
from datetime import date

from common import DATA

OUT = DATA / "cosing_2026"
BASE = ("https://webgate.ec.europa.eu/es/search-api/rest/search"
        "?apiKey=285a77fd-1257-4271-8507-f0c6b2961203&text=*"
        "&pageSize={size}&pageNumber={page}")
PAGE = 200
DEEP_PAGE_CAP = 10000          # index limit; partitions must stay under it
FIELDS = ["substanceId", "inciName", "innName", "phEurName", "casNo", "ecNo",
          "chemicalDescription", "chemicalName", "functionName", "status",
          "cosmeticRestriction", "otherRestrictions", "otherRegulations",
          "relatedRegulations", "maximumConcentration", "productTypeBodyParts",
          "wordingOfConditions", "sccsOpinion", "note", "perfuming",
          "annexNo", "officialJournalPublication", "currentVersion"]


def post(query, page=1, size=PAGE):
    boundary = "----cosing" + uuid.uuid4().hex
    parts = []
    for name, value in (("query", query), ("sort", "[]")):
        parts += [f"--{boundary}",
                  f'Content-Disposition: form-data; name="{name}"; filename="{name}"',
                  "Content-Type: application/json", "", value]
    parts += [f"--{boundary}--", ""]
    req = urllib.request.Request(
        BASE.format(size=size, page=page), data="\r\n".join(parts).encode(),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "User-Agent": "cosing-kg/0.1 (research; CC-BY-4.0 reuse)"})
    with urllib.request.urlopen(req, timeout=120) as fh:
        return json.load(fh)


def q_bucket(lo, hi):
    """Bucket query for substanceIds in the STRING range [lo, hi).

    substanceId is indexed as a string, so range comparison is lexicographic,
    not numeric. Numeric bounds give nonsense that looks plausible: lt:100000
    answers 0 while lt:110000 answers 4,722, because "79433" sorts after both
    "1..." forms. Partitioning on the leading character keeps the comparison
    entirely within string semantics, and the ten buckets sum to exactly the
    33,654 the API reports.
    """
    rng = {"gte": lo} if hi is None else {"gte": lo, "lt": hi}
    return json.dumps({"bool": {"must": [
        {"term": {"itemType": "ingredient"}},
        {"range": {"substanceId": rng}}]}})


def count(lo, hi):
    return post(q_bucket(lo, hi), page=1, size=1).get("totalResults", 0)


def partition(prefix, out):
    """One bucket per leading character, split further only if still too big."""
    lo = prefix
    hi = None if prefix == "9" else str(int(prefix) + 1)
    n = count(lo, hi)
    time.sleep(0.4)
    if n == 0:
        return
    if n <= DEEP_PAGE_CAP:
        out.append((lo, hi, n))
        print(f"    bucket [{lo}, {hi}) -> {n}")
        return
    # Still over the cap: extend the prefix by one digit and recurse.
    for d in "0123456789":
        sub = prefix + d
        sub_hi = sub[:-1] + str(int(d) + 1) if d != "9" else (
            None if hi is None else hi)
        m = count(sub, sub_hi)
        time.sleep(0.4)
        if m:
            out.append((sub, sub_hi, m))
            print(f"    bucket [{sub}, {sub_hi}) -> {m}")


def flatten(v):
    if isinstance(v, list):
        return " | ".join(str(x) for x in v if x not in (None, ""))
    return "" if v is None else str(v)


def main(limit_partitions=None):
    OUT.mkdir(parents=True, exist_ok=True)
    total = post(json.dumps({"bool": {"must": [{"term": {"itemType": "ingredient"}}]}}),
                 size=1).get("totalResults", 0)
    print(f"live inventory: {total} ingredients")

    print("  planning partitions...")
    buckets = []
    for c in "0123456789":
        partition(c, buckets)
    planned = sum(n for _, _, n in buckets)
    print(f"  {len(buckets)} partitions covering {planned} records")
    if planned != total:
        raise SystemExit(f"partition plan covers {planned} but API reports {total}")

    if limit_partitions:
        buckets = sorted(buckets, key=lambda b: b[2])[:limit_partitions]
        print(f"  DRY RUN: fetching only the first {len(buckets)} partition(s)")

    seen, rows, requests, dup = set(), [], 0, 0
    for lo, hi, n in buckets:
        page = 1
        got = 0
        while got < n:
            data = post(q_bucket(lo, hi), page=page)
            requests += 1
            batch = data.get("results", [])
            if not batch:
                raise SystemExit(
                    f"partition [{lo},{hi}) returned empty at page {page} "
                    f"after {got}/{n} -- deep-paging cap hit")
            for r in batch:
                md = r.get("metadata", {})
                rec = {f: flatten(md.get(f)) for f in FIELDS}
                sid = rec["substanceId"]
                if sid and sid not in seen:
                    seen.add(sid)
                    rows.append(rec)
                elif sid:
                    dup += 1
            got += len(batch)
            page += 1
            time.sleep(1.0)
        print(f"    [{lo}, {hi}) {got}/{n} in {page - 1} pages "
              f"(running total {len(rows)})")

    # totalResults counts index documents, not distinct ingredients: a handful
    # of records were ingested twice (same substanceId, same content, differing
    # only in Elasticsearch's own esST_REFERENCE / esDA_FirstIngestDate). So the
    # completeness test is that every bucket delivered its full document count
    # -- checked in the loop above -- and that distinct + duplicate reconciles.
    expected = planned if not limit_partitions else sum(n for _, _, n in buckets)
    if len(rows) + dup != expected:
        raise SystemExit(
            f"collected {len(rows)} distinct + {dup} duplicate = "
            f"{len(rows) + dup}, expected {expected}")
    if dup:
        print(f"  {dup} duplicate documents collapsed "
              f"({expected} documents -> {len(rows)} distinct ingredients)")

    stamp = date.today().isoformat()
    name = "inventory_sample" if limit_partitions else "inventory"
    with open(OUT / f"{name}.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: int(r["substanceId"] or 0)))
    (OUT / f"{name}_meta.json").write_text(json.dumps({
        "fetched": stamp, "records": len(rows), "api_total": total,
        "duplicate_documents": dup,
        "note": ("api_total counts index documents; duplicates are the same "
                 "ingredient ingested twice and differ only in Elasticsearch "
                 "internal fields, so records is the distinct ingredient count"),
        "requests": requests + len(buckets), "partitions": len(buckets),
        "licence": "CC BY 4.0, Commission Decision 2011/833/EU",
        "source": "European Commission CosIng",
        "join_key": "substanceId == COSING Ref No",
    }, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / (name + '.csv')}  "
          f"({len(rows)} records in {requests + len(buckets)} requests)")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit_partitions=n)
