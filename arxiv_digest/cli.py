"""Command-line interface for arxiv-digest."""
import argparse
import datetime
import json
import sys

from .core import build_query, fetch_feed, filter_new, parse_feed, render_markdown


def main(argv=None, fetch=fetch_feed):
    ap = argparse.ArgumentParser(prog="arxiv-digest", description="Markdown digest of new arXiv papers.")
    ap.add_argument("-k", "--keyword", action="append", default=[], help="keyword or phrase (repeatable)")
    ap.add_argument("-c", "--category", action="append", default=[], help="arXiv category, e.g. cs.LG (repeatable)")
    ap.add_argument("-a", "--author", action="append", default=[], help="author name (repeatable)")
    ap.add_argument("--config", help="JSON file with keys keywords/categories/authors/title")
    ap.add_argument("--mode", choices=["AND", "OR"], default="AND", help="how to combine keyword/category/author groups")
    ap.add_argument("-n", "--max-results", type=int, default=50)
    ap.add_argument("--state", help="JSON file of already-seen IDs (only new papers are reported)")
    ap.add_argument("-o", "--output", help="Markdown output file")
    args = ap.parse_args(argv)

    cfg = {}
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
    keywords = args.keyword + cfg.get("keywords", [])
    query = build_query(keywords, args.category + cfg.get("categories", []),
                        args.author + cfg.get("authors", []), args.mode)
    papers = parse_feed(fetch(query, args.max_results))
    if args.state:
        papers = filter_new(papers, args.state)
    title = cfg.get("title", "arXiv digest") + " - " + datetime.date.today().isoformat()
    md = render_markdown(papers, title, keywords)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(md)
    else:
        sys.stdout.write(md)
    print("%d new paper(s)" % len(papers), file=sys.stderr)
    return 0
