import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from arxiv_digest.cli import main
from arxiv_digest.core import build_query, filter_new, parse_feed, query_url, render_markdown, score

with open(os.path.join(os.path.dirname(__file__), "fixture_feed.xml"), encoding="utf-8") as fh:
    FEED = fh.read()


class QueryTests(unittest.TestCase):
    def test_build_query_groups(self):
        q = build_query(["llm", "graph neural network"], ["cs.LG"], ["Hinton"])
        self.assertEqual(q, '(ti:llm OR abs:llm OR ti:"graph neural network" OR abs:"graph neural network") '
                            'AND (cat:cs.LG) AND (au:Hinton)')

    def test_or_mode_and_empty(self):
        self.assertIn(" OR (cat:cs.AI)", build_query(["x"], ["cs.AI"], mode="OR"))
        with self.assertRaises(ValueError):
            build_query()

    def test_url_sorted_by_date(self):
        self.assertIn("sortBy=submittedDate", query_url("cat:cs.LG", 5))


class FeedTests(unittest.TestCase):
    def test_parse_feed(self):
        papers = parse_feed(FEED)
        self.assertEqual(len(papers), 2)
        p = papers[0]
        self.assertEqual(p["id"], "2401.00001")
        self.assertEqual(p["title"], "Retrieval Augmented Generation for Science")
        self.assertEqual(p["authors"], ["Ada Lovelace", "Alan Turing"])
        self.assertEqual(p["primary"], "cs.CL")
        self.assertTrue(p["pdf"].endswith("2401.00001v2"))
        self.assertEqual(papers[1]["primary"], "")

    def test_filter_new_tracks_state(self):
        papers = parse_feed(FEED)
        with tempfile.TemporaryDirectory() as d:
            state = os.path.join(d, "seen.json")
            self.assertEqual(len(filter_new(papers, state)), 2)
            self.assertEqual(filter_new(papers, state), [])

    def test_ranking_and_render(self):
        papers = parse_feed(FEED)
        self.assertGreater(score(papers[0], ["retrieval"]), score(papers[1], ["retrieval"]))
        md = render_markdown(list(reversed(papers)), "Digest", ["retrieval"], max_summary=20)
        self.assertLess(md.index("Retrieval Augmented"), md.index("Unrelated Physics"))
        self.assertIn("[PDF](http://arxiv.org/pdf/2401.00001v2)", md)
        self.assertIn(" ...", md)

    def test_cli_with_fake_fetch(self):
        calls = []

        def fake(query, n):
            calls.append(query)
            return FEED
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["-k", "retrieval", "-c", "cs.CL"], fetch=fake), 0)
        self.assertIn("cat:cs.CL", calls[0])
        self.assertIn("2 new paper(s)", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
