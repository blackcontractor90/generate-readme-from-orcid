# generate_readme_from_orcid.py — README

Overview
--------
This repository includes a small Python script, `generate_readme_from_orcid.py`, which queries the ORCID public API for a given ORCID iD and produces a `README.md` (or any output file you choose) containing a markdown table that lists publications with the following columns: Title, Authors, Venue, Year, DOI, Link.

The script is intentionally minimal and robust: it handles missing fields, guards against None values in the ORCID JSON, and falls back to summary fields where possible.

Requirements
------------
- Python 3.7+ (3.8+ recommended)
- requests library

Install requirements:
```bash
python -m pip install --upgrade pip
pip install requests
```

Files
-----
- generate_readme_from_orcid.py — main script (place this in repo root or a scripts/ directory)
- README.md — this file (documentation)

Quick usage
-----------
Basic run (example):
```bash
python generate_readme_from_orcid.py --orcid 0000-0001-9812-1078 --out README_ORCID.md
```

Options:
- --orcid : ORCID identifier (required). Example: 0000-0001-9812-1078
- --out   : Output markdown file path (default: README.md)
- --sleep : Seconds to sleep between per-work requests (default: 0.2). Increase this to reduce load or avoid transient rate limits.

What the script does
-------------------
1. Fetches the public ORCID record JSON at:
   `https://pub.orcid.org/v3.0/{ORCID}/record`
2. Iterates the works in `activities-summary -> works -> group`.
3. For each work group it fetches the detailed work JSON:
   `https://pub.orcid.org/v3.0/{ORCID}/work/{put-code}`
4. Extracts metadata: title, contributors (authors), journal/venue, publication year, DOI (if present), and a link (from external IDs or URL).
5. Writes a markdown table with one row per work.

Output format example
---------------------
The generated markdown starts with:
```
# Publications for ORCID 0000-0001-9812-1078

Source: https://orcid.org/0000-0001-9812-1078

| Title | Authors | Venue | Year | DOI | Link |
|---|---|---|---|---|---|
| Example title | A. Author, B. Collaborator | Example Journal | 2024 | [10.1234/example](https://doi.org/10.1234/example) | [link](https://doi.org/10.1234/example) |
```

Notes and troubleshooting
-------------------------
- AttributeError: 'NoneType' object has no attribute 'get'
  - Cause: Some ORCID records contain group/work-summary entries that can be None or missing nested fields. The script includes defensive checks and uses a `dict_safe_get` helper to avoid such errors.
  - If you still see this error, run the script with a short delay (increase `--sleep` to 0.5 or 1.0) and paste the full traceback here; I can further harden the script.

- Missing DOI / Venue / Authors:
  - ORCID records are user-supplied and can be incomplete. The script extracts what’s present in ORCID. You can enrich metadata using CrossRef or OpenAlex by querying with title or DOI when available.

- Rate limiting / network errors:
  - The script sleeps briefly between per-work requests; if you see HTTP 429 or transient network errors, increase the `--sleep` value.
  - If you need to process a large ORCID record, consider batching or caching results.

Customization ideas
-------------------
- Generate a consolidated `references.bib` (BibTeX) by querying CrossRef using DOIs.
- Add a `CITATION.cff` file so GitHub displays citation info.
- Create a GitHub Actions workflow to regenerate README periodically or on push.
- Add a `--format` option to output CSV, JSON, or HTML (site-friendly).
- Add command-line flags to include/exclude non-peer-reviewed works.

Security & copyright
--------------------
- This script only reads public ORCID data. It does not require authentication to read public records.
- The repository may contain PDFs or other files — ensure you have the right to redistribute any publisher PDFs before committing them.

Contact
-------
Maintainer: blackcontractor90  
ORCID: https://orcid.org/0000-0001-9812-1078

Acknowledgements
----------------
- ORCID public API and documentation
- Example helpers and parsing strategy inspired by community ORCID tools

--- 

Generated with the intent to be immediately useful. Drop this README.md into your repository root alongside `generate_readme_from_orcid.py` and run the example command to produce a publications table.

