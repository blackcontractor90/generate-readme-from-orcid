#!/usr/bin/env python3
"""
Generate a README.md listing publications from a public ORCID record.

Usage:
  pip install requests
  python3 generate_readme_from_orcid.py --orcid 0000-0001-9812-1078 --out README.md

This script:
 - Fetches https://pub.orcid.org/v3.0/{ORCID}/record (public)
 - Iterates works in activities-summary -> works -> group
 - For each work, fetches the detailed work endpoint:
    https://pub.orcid.org/v3.0/{ORCID}/work/{put-code}
 - Extracts: title, contributors (authors), journal/venue, year, DOI (if present), link
 - Writes a markdown file with a table of publications.
"""
# Author: blackcontractor90
# Date: October 29, 2025
import argparse
import requests
import time
import sys
from urllib.parse import quote_plus

HEADERS = {
    "Accept": "application/json"
}

def fetch_json(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def extract_title(work):
    # Detailed work uses 'title' -> 'title' -> 'value'
    if not work:
        return ''
    return (work.get('title', {}) or {}).get('title', {}).get('value') or ''

def extract_contributors(work):
    if not work:
        return []
    contribs = []
    for c in (work.get('contributors', {}) or {}).get('contributor', []) or []:
        name = (c.get('credit-name') or {}).get('value')
        if name:
            contribs.append(name)
    return contribs

def extract_journal(work):
    if not work:
        return ''
    # Some records use 'journal-title' for venue
    jt = (work.get('journal-title') or {}).get('value')
    if jt:
        return jt
    # Some records embed 'short-description' or 'work-type' info — fall back to empty
    return ''

def extract_year(work, summary_ws=None):
    # Prefer detailed publication-date, fallback to summary's publication-date
    if work:
        pd = work.get('publication-date') or {}
        year = (pd.get('year') or {}).get('value')
        if year:
            return year
    if summary_ws:
        pd = (summary_ws.get('publication-date') or {}) if isinstance(summary_ws, dict) else {}
        return (pd.get('year') or {}).get('value') or ''
    return ''

def extract_doi_and_url(work):
    doi = ''
    url = ''
    if not work:
        return doi, url
    ext = work.get('external-ids') or {}
    for e in ext.get('external-id', []) or []:
        t = (e.get('external-id-type') or '').lower()
        val = e.get('external-id-value') or ''
        if t == 'doi' or ('doi' in t):
            doi = val.strip()
            doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
            if doi.startswith('doi:'):
                doi = doi.split(':',1)[1]
        if not url:
            url = (e.get('external-id-url') or {}).get('value') or ''
    if not url:
        url = (work.get('url') or {}).get('value') or ''
    return doi, url

def sanitize_markdown(text):
    if not isinstance(text, str):
        return ''
    return text.replace('\n', ' ').strip()

def dict_safe_get(d, *keys, default=''):
    """Safe nested get helper: dict_safe_get(d, 'a', 'b') -> d.get('a', {}).get('b', default)"""
    cur = d if isinstance(d, dict) else {}
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, {})
    if isinstance(cur, dict):
        return default
    return cur or default

def main():
    parser = argparse.ArgumentParser(description="Generate README.md from ORCID public record")
    parser.add_argument('--orcid', required=True, help='ORCID iD (e.g. 0000-0001-9812-1078)')
    parser.add_argument('--out', default='README.md', help='Output README filename')
    parser.add_argument('--sleep', type=float, default=0.2, help='Seconds to sleep between per-work requests')
    args = parser.parse_args()

    orcid = args.orcid.strip()
    base_record_url = f'https://pub.orcid.org/v3.0/{quote_plus(orcid)}/record'

    print(f"Fetching ORCID record for {orcid} ...")
    try:
        record = fetch_json(base_record_url)
    except Exception as e:
        print("Failed to fetch ORCID record:", e, file=sys.stderr)
        sys.exit(1)

    groups = (record.get('activities-summary', {}) or {}).get('works', {}) or {}
    groups_list = groups.get('group', []) or []

    rows = []
    for g in groups_list:
        work_summaries = g.get('work-summary') or []
        if not work_summaries:
            continue
        ws = work_summaries[0] or {}
        put_code = ws.get('put-code')
        if put_code is None:
            continue

        work_url = f'https://pub.orcid.org/v3.0/{quote_plus(orcid)}/work/{put_code}'
        try:
            detailed = fetch_json(work_url) or {}
        except Exception as e:
            print(f"Warning: failed to fetch work {put_code}: {e}", file=sys.stderr)
            continue

        # Use detailed values where available, fallback to summary (ws)
        title = sanitize_markdown(extract_title(detailed) or dict_safe_get(ws, 'title', 'title', 'value', default='') or dict_safe_get(ws, 'title', default=''))
        authors = extract_contributors(detailed)
        if not authors:
            # attempt to extract authors from the summary 'author' fields if present
            # the summary representation varies; try a few keys safely
            author_str = ws.get('author') or ws.get('credit-name') or ''
            if isinstance(author_str, str) and author_str:
                authors = [author_str]
        authors_md = ', '.join(authors) if authors else ''

        journal = sanitize_markdown(extract_journal(detailed) or dict_safe_get(ws, 'journal-title', 'value', default=''))
        year = extract_year(detailed, summary_ws=ws)
        doi, link = extract_doi_and_url(detailed)
        doi_md = f"[{doi}](https://doi.org/{doi})" if doi else ''
        if not link and doi:
            link = f"https://doi.org/{doi}"

        rows.append({
            'title': title or '(no title)',
            'authors': authors_md,
            'journal': journal,
            'year': year,
            'doi': doi_md,
            'link': link
        })
        time.sleep(args.sleep)

    def sort_key(r):
        try:
            return int(r.get('year') or 0)
        except:
            return 0
    rows.sort(key=sort_key, reverse=True)

    md_lines = []
    md_lines.append(f"# Publications for ORCID {orcid}")
    md_lines.append("")
    md_lines.append(f"Source: https://orcid.org/{orcid}")
    md_lines.append("")
    md_lines.append("| Title | Authors | Venue | Year | DOI | Link |")
    md_lines.append("|---|---|---|---|---|---|")
    for r in rows:
        title = (r['title'] or '').replace("|", "\\|")
        authors = (r['authors'] or '').replace("|", "\\|")
        journal = (r['journal'] or '').replace("|", "\\|")
        year = r['year'] or ''
        doi = r['doi'] or ''
        link = f"[link]({r['link']})" if r['link'] else ''
        md_lines.append(f"| {title} | {authors} | {journal} | {year} | {doi} | {link} |")

    md_lines.append("")
    md_lines.append("Generated with generate_readme_from_orcid.py — edit entries where additional metadata or PDFs/paths are available.")
    md_text = "\n".join(md_lines)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"Wrote {args.out} with {len(rows)} publications.")

if __name__ == "__main__":
    main()
