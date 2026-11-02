#!/usr/bin/env python3
"""Build _publications.md from the public ORCID record.

ORCID gives the list of works; Crossref (by DOI) fills in authors, volume
and pages, which are often missing on ORCID. If the network fails, the
existing _publications.md is kept so the site still builds.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ORCID_ID = "0000-0003-1756-0162"
MY_NAMES = ("Takashi Yoshino", "T. Yoshino", "Yoshino, Takashi")
OUT = Path(__file__).resolve().parent.parent / "_publications.md"
UA = "takashiyoshino.random-walk.org publication list (stdlib urllib)"

TYPE_LABELS = {
    "journal-article": "論文 / Journal articles",
    "preprint": "プレプリント / Preprints",
    "book-chapter": "本の章 / Book chapters",
    "book": "本 / Books",
    "conference-paper": "会議録 / Conference papers",
}

# Crossref has no server name for these preprints; recognise them by DOI prefix
PREPRINT_SERVERS = {
    "10.31223": "EarthArXiv",
    "10.48550": "arXiv",
    "10.1101": "bioRxiv",
    "10.31219": "OSF Preprints",
}


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def orcid_works():
    base = f"https://pub.orcid.org/v3.0/{ORCID_ID}"
    groups = get_json(f"{base}/works")["group"]
    codes = [str(g["work-summary"][0]["put-code"]) for g in groups]
    works = []
    # The bulk endpoint accepts up to 100 put-codes at a time
    for i in range(0, len(codes), 100):
        works += [b["work"] for b in get_json(f"{base}/works/{','.join(codes[i:i + 100])}")["bulk"]]
    return works


def doi_of(work):
    ids = {e["external-id-type"]: e["external-id-value"]
           for e in (work.get("external-ids") or {}).get("external-id", [])}
    if "doi" in ids:
        return ids["doi"].lower()
    # Works added by arXiv ID only: every arXiv paper has a DataCite DOI
    if "arxiv" in ids:
        aid = ids["arxiv"].lower().removeprefix("arxiv:")
        return f"10.48550/arxiv.{re.sub(r'v[0-9]+$', '', aid)}"
    return None


def crossref(doi):
    try:
        return get_json(f"https://api.crossref.org/works/{doi}")["message"]
    except Exception:  # not a Crossref DOI (arXiv uses DataCite), network error, ...
        return datacite(doi)


def datacite(doi):
    """Fetch DataCite metadata in the shape of a Crossref record."""
    try:
        a = get_json(f"https://api.datacite.org/dois/{doi}")["data"]["attributes"]
    except Exception as e:
        print(f"crossref/datacite: {doi}: {e}", file=sys.stderr)
        return {}
    # arXiv records the first submission (v1) as "Submitted"
    dates = {}
    for d in a.get("dates", []):
        if d.get("dateInformation") in (None, "v1"):
            dates.setdefault(d["dateType"], d["date"])
    first = dates.get("Submitted") or dates.get("Issued") or ""
    parts = [int(p) for p in re.findall(r"\d+", first[:10])]
    return {"author": [{"given": c.get("givenName"), "family": c.get("familyName"), "name": c.get("name")}
                       for c in a.get("creators", [])],
            "issued": {"date-parts": [parts or [None]]}}


def authors_of(work, cr):
    if cr.get("author"):
        names = [" ".join(p for p in (a.get("given"), a.get("family")) if p) or a.get("name", "")
                 for a in cr["author"]]
    else:
        names = [(c.get("credit-name") or {}).get("value", "")
                 for c in (work.get("contributors") or {}).get("contributor", [])]
    names = [n for n in names if n]
    return ", ".join(f"**{n}**" if n in MY_NAMES else n for n in names)


def entry(work):
    doi = doi_of(work)
    cr = crossref(doi) if doi else {}
    title = work["title"]["title"]["value"]
    pd = work.get("publication-date") or {}
    year, month, day = ((pd.get(k) or {}).get("value", "") for k in ("year", "month", "day"))
    # Crossref/DataCite records carry the full date when ORCID has only the year
    issued = (cr.get("issued") or {}).get("date-parts", [[None]])[0]
    if not month and issued and str(issued[0]) == year and len(issued) > 1:
        month, day = f"{issued[1]:02d}", f"{issued[2]:02d}" if len(issued) > 2 else ""
    sort_key = f"{year}-{month or '00'}-{day or '00'}"
    journal = (work.get("journal-title") or {}).get("value") or (cr.get("container-title") or [""])[0]
    if work["type"] == "preprint" and not journal:
        journal = PREPRINT_SERVERS.get((doi or "").split("/")[0], "Preprint")
    vol, pages = cr.get("volume"), cr.get("page") or cr.get("article-number")

    parts = []
    if a := authors_of(work, cr):
        parts.append(f"{a} ({year}).")
    else:
        parts.append(f"({year}).")
    parts.append(f"{title}.")
    src = f"*{journal}*" if journal else ""
    if vol:
        src += f", {vol}"
    if pages:
        src += f", {pages}"
    if src:
        parts.append(src + ".")
    if doi:
        parts.append(f"[doi:{doi}](https://doi.org/{doi})")
    return sort_key, work["type"], " ".join(parts)


def main():
    # Quarto sets this only when the whole project is rendered; skip the
    # network round trip on preview and single-page renders
    if not os.environ.get("QUARTO_PROJECT_RENDER_ALL") and OUT.exists():
        print(f"orcid: partial render, keeping the existing {OUT.name}", file=sys.stderr)
        return
    try:
        entries = [entry(w) for w in orcid_works()]
    except Exception as e:
        print(f"orcid: {e}; keeping the existing {OUT.name}", file=sys.stderr)
        return

    lines = [f"<!-- Generated by scripts/orcid.py from ORCID {ORCID_ID}. Do not edit. -->", ""]
    order = list(TYPE_LABELS) + sorted({t for _, t, _ in entries} - set(TYPE_LABELS))
    for t in order:
        items = sorted((e for e in entries if e[1] == t), key=lambda e: e[0], reverse=True)
        if not items:
            continue
        lines += [f"## {TYPE_LABELS.get(t, t)}", ""]
        lines += [f"1. {text}" for _, _, text in items]
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"orcid: wrote {len(entries)} works to {OUT.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
