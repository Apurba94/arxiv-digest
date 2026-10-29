"""Query construction, Atom parsing, de-duplication against seen IDs, and rendering."""
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def build_query(keywords=(), categories=(), authors=(), mode="AND"):
    """Build an arXiv search_query string.

    keywords are searched in title and abstract; phrases are quoted. Groups are combined with
    `mode` (AND/OR); terms within a group are OR-ed.
    """
    groups = []
    if keywords:
        terms = []
        for k in keywords:
            q = '"%s"' % k if " " in k else k
            terms.append("ti:%s OR abs:%s" % (q, q))
        groups.append("(" + " OR ".join(terms) + ")")
    if categories:
        groups.append("(" + " OR ".join("cat:" + c for c in categories) + ")")
    if authors:
        groups.append("(" + " OR ".join('au:"%s"' % a if " " in a else "au:" + a for a in authors) + ")")
    if not groups:
        raise ValueError("give at least one keyword, category or author")
    return (" %s " % mode).join(groups)


def query_url(query, max_results=50):
    params = {"search_query": query, "start": 0, "max_results": max_results,
              "sortBy": "submittedDate", "sortOrder": "descending"}
    return API + "?" + urllib.parse.urlencode(params)


def fetch_feed(query, max_results=50, timeout=30):
    req = urllib.request.Request(query_url(query, max_results), headers={"User-Agent": "arxiv-digest/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _text(el, path):
    found = el.find(path, NS)
    return " ".join(found.text.split()) if found is not None and found.text else ""


def parse_feed(xml_text):
    """Parse an arXiv Atom feed into a list of paper dicts."""
    root = ET.fromstring(xml_text)
    papers = []
    for e in root.findall("a:entry", NS):
        url = _text(e, "a:id")
        m = re.search(r"abs/(.+?)(v\d+)?$", url)
        pdf = next((l.get("href") for l in e.findall("a:link", NS) if l.get("title") == "pdf"), "")
        papers.append({
            "id": m.group(1) if m else url,
            "url": url,
            "pdf": pdf,
            "title": _text(e, "a:title"),
            "summary": _text(e, "a:summary"),
            "published": _text(e, "a:published")[:10],
            "authors": [_text(a, "a:name") for a in e.findall("a:author", NS)],
            "categories": [c.get("term") for c in e.findall("a:category", NS)],
            "primary": (e.find("arxiv:primary_category", NS).get("term")
                        if e.find("arxiv:primary_category", NS) is not None else ""),
        })
    return papers


def filter_new(papers, state_path):
    """Return papers whose IDs are not in the JSON state file, and record them as seen."""
    seen = set()
    if state_path and os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as fh:
            seen = set(json.load(fh))
    new = [p for p in papers if p["id"] not in seen]
    if state_path:
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(sorted(seen | {p["id"] for p in papers}), fh, indent=0)
    return new


def score(paper, keywords):
    """Count keyword hits (title hits count double) for ranking."""
    t, s = paper["title"].lower(), paper["summary"].lower()
    return sum(2 * t.count(k.lower()) + s.count(k.lower()) for k in keywords)


def render_markdown(papers, title="arXiv digest", keywords=(), max_summary=400):
    lines = ["# %s" % title, "", "%d new paper(s)" % len(papers), ""]
    ranked = sorted(papers, key=lambda p: -score(p, keywords)) if keywords else papers
    for i, p in enumerate(ranked, 1):
        authors = ", ".join(p["authors"][:5]) + (" et al." if len(p["authors"]) > 5 else "")
        summary = p["summary"]
        if len(summary) > max_summary:
            summary = summary[:max_summary].rsplit(" ", 1)[0] + " ..."
        lines += ["## %d. [%s](%s)" % (i, p["title"], p["url"]),
                  "*%s* | %s | `%s`%s" % (authors, p["published"], p["primary"] or ",".join(p["categories"][:2]),
                                          " | [PDF](%s)" % p["pdf"] if p["pdf"] else ""),
                  "", summary, ""]
    return "\n".join(lines)
