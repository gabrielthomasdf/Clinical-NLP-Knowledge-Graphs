"""Check article-level Creative Commons URLs without downloading case text to disk.

Reads the versioned MultiCaRe metadata, requests each public Europe PMC XML,
and writes only article IDs, recorded licenses, license URLs and statuses.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

DEFAULT_METADATA = Path(__file__).resolve().parents[1] / "data" / "raw" / "metadata.csv"
CC_URL = re.compile(r"https?://creativecommons\.org/licenses/([a-z-]+)/([0-9.]+)/?", re.IGNORECASE)
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def inspect_article(row: dict[str, str]) -> dict[str, object]:
    article_id = row["article_id"]
    result: dict[str, object] = {"article_id": article_id, "recorded_license": row["license"],
                                 "source_url": f"https://www.ebi.ac.uk/europepmc/webservices/rest/{article_id}/fullTextXML"}
    try:
        request = Request(result["source_url"], headers={"User-Agent": "mc896-portfolio-license-audit/1.0"})
        with urlopen(request, timeout=25) as response:
            xml = response.read()
        root = ET.fromstring(xml)
        urls = set()
        license_texts = []
        for license_element in root.findall(".//license"):
            license_text = " ".join("".join(license_element.itertext()).split())
            license_texts.append(license_text)
            values = [license_element.attrib.get(XLINK_HREF, ""), license_text]
            for value in values:
                urls.update(match.group(0) for match in CC_URL.finditer(value))
        result["license_urls"] = sorted(urls)
        observed = {"CC " + match.group(1).upper() for url in urls
                    if (match := CC_URL.search(url))}
        versions = {match.group(2) for url in urls if (match := CC_URL.search(url))}
        if not observed:
            license_text = " | ".join(license_texts)
            result["license_text_excerpt"] = license_text[:350]
            normalized = re.sub(r"[^a-z0-9]+", "", license_text.lower())
            if "attributionnoncommercialsharealike" in normalized:
                observed = {"CC BY-NC-SA"}
            elif "attributionnoncommercial" in normalized:
                observed = {"CC BY-NC"}
            elif "creativecommonsattribution" in normalized:
                observed = {"CC BY"}
            versions = set(re.findall(r"\b[234]\.0\b", license_text))
        result["observed_license_families"] = sorted(observed)
        result["observed_versions"] = sorted(versions)
        result["matches_recorded_family"] = row["license"] in observed if observed else None
        result["status"] = "verified_url" if urls else ("verified_text" if observed else "unresolved")
    except (HTTPError, URLError, TimeoutError, ET.ParseError) as error:
        result["status"] = "source_unavailable"
        result["error_type"] = type(error).__name__
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, help="Write a summary without license text excerpts")
    args = parser.parse_args()
    contents = args.metadata.read_bytes()
    rows = list(csv.DictReader(contents.decode("utf-8-sig").splitlines()))
    if len({row["article_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate article_id in metadata")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = sorted(pool.map(inspect_article, rows), key=lambda item: item["article_id"])
    report = {"schema_version": 1, "metadata_sha256": hashlib.sha256(contents).hexdigest(),
              "articles": len(rows), "results": results,
              "counts": {"verified": sum(row["status"] in ("verified_url", "verified_text") for row in results),
                         "verified_url": sum(row["status"] == "verified_url" for row in results),
                         "verified_text": sum(row["status"] == "verified_text" for row in results),
                         "version_known": sum(bool(row.get("observed_versions")) for row in results),
                         "unavailable": sum(row["status"] == "source_unavailable" for row in results),
                         "unresolved": sum(row["status"] == "unresolved" for row in results),
                         "mismatches": sum(row["matches_recorded_family"] is False for row in results)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.public_output is not None:
        public = {**report, "results": [{key: value for key, value in row.items() if key != "license_text_excerpt"}
                                         for row in results]}
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
