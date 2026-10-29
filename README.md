# arxiv-digest

**Your personal arXiv alert: saved keyword/category/author searches turned into a ranked
Markdown digest containing only papers you have not seen yet.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Hundreds of preprints appear on arXiv every day. Browsing category listings takes time and
misses cross-listed work; e-mail alerts cannot rank by relevance. `arxiv-digest` runs your saved
queries through the official arXiv API, remembers what you have already seen, and writes a clean
digest you can read in your notes app, commit to a lab wiki, or send to a group channel.

## Features

- Query builder: keywords/phrases in title and abstract, categories, authors, AND/OR combination
- Parses the arXiv Atom API (IDs without version, PDF links, primary category, authors)
- Seen-ID state file, so every run reports only new papers
- Relevance ranking by keyword hits (title hits weighted double)
- JSON config for reusable topic profiles; schedule with cron or Windows Task Scheduler

## Usage

```bash
pip install .
arxiv-digest -k "retrieval augmented" -k "large language model" -c cs.CL --state seen.json -o digest.md
arxiv-digest --config examples/config.json --state seen.json
arxiv-digest -a "Yoshua Bengio" --mode OR -c cs.LG
```

Please respect the arXiv API terms of use: no more than one request every three seconds.

## Testing

Offline tests use a recorded Atom feed fixture:

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
