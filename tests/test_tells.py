"""The rendered tells check: documented detectors, a self-contained page script and real-browser findings."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tests.test_observation import OBSERVER, browser_observation_available, node_executable

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill/snowe-ui-skill"
TELLS = SKILL / "scripts/tells.js"
CLI_REFERENCE = SKILL / "references/cli-reference.md"


def tell_ids():
    return re.findall(r"^\s*'([a-z-]+)': \['(?:tell|check)'", TELLS.read_text(encoding="utf-8"), re.MULTILINE)


SLOP = """<!doctype html><html><head><meta charset="utf-8"><title>Slop</title><style>
body{margin:0;font-family:Inter,system-ui,sans-serif;background:#f5efe4}
.top{position:fixed;top:0;left:0;right:0;height:56px;background:#1f2a37;color:#fff}
.side{position:fixed;top:56px;left:0;width:220px;bottom:0;background:#1f2a37}
.side a{display:block;padding:10px 16px;color:#e5e7eb;font-family:Georgia,serif}
.side a.active{border-left:3px solid #c2410c;background:#2b3a4a}
main{margin-left:220px;padding:80px 32px}
.card{position:relative;background:#fff;border-radius:8px;padding:16px;margin:12px 0}
.callout::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:#4f46e5}
.btn{background:#4f46e5;color:#fff;border:0;padding:8px 12px;border-radius:6px}
.shadow{box-shadow:0 10px 15px -3px rgba(0,0,0,.1),0 4px 6px -4px rgba(0,0,0,.1)}
.hero{background:linear-gradient(90deg,#7c3aed,#2563eb);color:#fff;padding:24px}
.grad{background:linear-gradient(90deg,#7c3aed,#db2777);-webkit-background-clip:text;background-clip:text;color:transparent}
.features{display:flex;gap:16px}.feature{flex:1}
.tile{width:48px;height:48px;border-radius:12px;background:#ede9fe;display:grid;place-items:center}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px}
.muted{color:#9ca3af}
.timeline{border-left:2px solid #444;padding-left:16px;list-style:none}
.reveal{opacity:0;transform:translateY(20px)}
.glass{backdrop-filter:blur(12px);background:rgba(255,255,255,.4);padding:8px}
.wide{width:600px;background:#fff}
</style></head><body>
<div class="top">Cabinet</div>
<nav class="side"><a class="active" href="#">Scans</a><a href="#">KvK setup</a><a href="#">Members</a><a href="#">Billing</a><a href="#">Profile</a></nav>
<main>
<p class="eyebrow">Overview</p><h1 class="grad">Scans</h1>
<div class="hero">Hero</div>
<div class="card callout shadow">Callout card text here</div>
<div class="card shadow">Second card</div><div class="card shadow">Third card</div>
<button class="btn">Run</button> <button>Plain</button> <button>\U0001F680 Launch</button>
<select><option>Siege of Orleans</option></select> <input type="date"> <input type="checkbox"> <input type="text">
<p class="eyebrow">Features</p><h2>01 / Fast</h2>
<div class="features">
<div class="feature"><div class="tile"><svg width="20" height="20"><circle cx="10" cy="10" r="8"/></svg></div><h3>One</h3><p class="muted">Muted body text here that is hard to read on white.</p></div>
<div class="feature"><div class="tile"><svg width="20" height="20"><circle cx="10" cy="10" r="8"/></svg></div><h3>Two</h3><p>Body text two.</p></div>
<div class="feature"><div class="tile"><svg width="20" height="20"><circle cx="10" cy="10" r="8"/></svg></div><h3>Three</h3><p>Body text three.</p></div>
</div>
<p class="eyebrow">Pricing</p><h2>02 / Plans</h2>
<ol class="timeline"><li>Week one: map the work</li><li>Week two: build the agent</li></ol>
<p class="eyebrow">Questions</p><h2>Answers</h2>
<div class="glass">a</div><div class="glass">b</div><div class="glass">c</div>
<div class="wide">wide block that overflows on phones</div>
<div style="height:1400px"></div>
<section class="reveal"><h2>Later section</h2><p>Text that waits for the scroll reveal to run.</p></section>
<section class="reveal"><h2>Another later section</h2><p>More text that waits for the scroll reveal.</p></section>
</main></body></html>"""

CLEAN = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Clean</title><style>
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 Inter,system-ui,sans-serif;background:#fafafa;color:#18181b}
.layout{display:grid;grid-template-columns:232px 1fr;min-height:100vh}
aside{background:#f4f4f5;border-right:1px solid #e4e4e7;padding:16px 12px}
aside a{display:block;padding:6px 10px;border-radius:6px;color:#18181b;text-decoration:none}
aside a[aria-current=page]{background:#e4e4e7;font-weight:600}
main{padding:32px;max-width:1100px}
h1{font-size:22px;margin:0 0 16px}
.panel{border:1px solid #e4e4e7;border-radius:10px;background:#fff;padding:16px;margin-bottom:16px}
.select{appearance:none;border:1px solid #d4d4d8;border-radius:8px;padding:6px 32px 6px 10px;font:inherit;background:#fff}
.field{border:1px solid #d4d4d8;border-radius:8px;padding:6px 10px;font:inherit}
.button{background:#18181b;color:#fff;border:0;border-radius:8px;padding:7px 12px;font:inherit}
input[type=checkbox]{accent-color:#18181b}
:focus-visible{outline:2px solid #2563eb;outline-offset:2px}
p{color:#52525b}
@media (max-width:700px){.layout{grid-template-columns:1fr}aside{display:none}main{padding:16px}}
</style></head><body><div class="layout">
<aside><a aria-current="page" href="#">Scans</a><a href="#">KvK setup</a><a href="#">KvK overview</a><a href="#">Members</a><a href="#">Billing</a></aside>
<main><h1>Scans</h1>
<div class="panel"><label>KvK <select class="select"><option>Siege of Orleans</option></select></label>
<input class="field" placeholder="Find a scan"> <label><input type="checkbox"> Only complete</label> <button class="button">New scan</button></div>
<div class="panel"><p>Stats count from the baseline scan to the latest complete scan.</p></div>
<table><tr><th>Scan</th><th>Status</th></tr><tr><td>After Zone 5</td><td>Completed</td></tr></table>
</main></div></body></html>"""

PROSE = ("""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Long</title>
<style>body{margin:0 auto;max-width:720px;font:16px/1.6 system-ui,sans-serif;color:#18181b;background:#fff}:focus-visible{outline:2px solid #000}</style>
</head><body><h1>A landing page that explains everything</h1>"""
         + "".join(f"<section><h2>Part {n}</h2><p>{'The product does a careful thing for your team every day. ' * 30}</p></section>" for n in range(1, 6))
         + "<a href='#'>Start</a></body></html>")

STRIPE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stripe</title>
<style>body{margin:0;padding:24px;font:14px system-ui,sans-serif;background:#fff;color:#111}:focus-visible{outline:2px solid #000}
.note{border-left:3px solid #2563eb;border-radius:6px;background:#eff6ff;padding:12px}</style></head>
<body><div class="note">A callout marked with a stripe on its left edge.</div></body></html>"""


class TellsContractTests(unittest.TestCase):
    """Static contracts that need neither Node nor a browser."""

    def test_every_tell_is_documented_and_no_retired_id_remains(self):
        ids = tell_ids()
        self.assertGreaterEqual(len(ids), 15)
        self.assertEqual(len(ids), len(set(ids)))
        text = CLI_REFERENCE.read_text(encoding="utf-8")
        section = text.split("## Check a Render for Common Tells", 1)[1].split("\n## ", 1)[0]
        documented = re.findall(r"^\| `([a-z-]+)` \| (?:tell|check) \|", section, re.MULTILINE)
        self.assertEqual(sorted(ids), sorted(documented))

    def test_page_script_is_self_contained(self):
        source = TELLS.read_text(encoding="utf-8")
        self.assertIn("function snoweTells(", source)
        for forbidden in ("import ", "require(", "fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "eval("):
            self.assertNotIn(forbidden, source)

    def test_skill_routes_the_check(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("observe.mjs tells", skill)
        self.assertIn("tells.js", skill)


class TellsBrowserTests(unittest.TestCase):
    """Real Chromium runs of `observe.mjs tells` against fixtures with known tells."""

    def setUp(self):
        if not node_executable() or not browser_observation_available():
            self.skipTest("Node 22+ and a system Chrome/Chromium/Edge are unavailable")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, html in {"slop.html": SLOP, "clean.html": CLEAN, "prose.html": PROSE, "stripe.html": STRIPE}.items():
            (self.root / name).write_text(html, encoding="utf-8")

    def run_tells(self, *arguments):
        result = subprocess.run([node_executable(), str(OBSERVER), "tells", str(self.root), *arguments],
                                capture_output=True, text=True, encoding="utf-8", timeout=240)
        report = json.loads(result.stdout) if result.stdout.strip() else None
        return result, report

    def test_every_detector_fires_on_a_page_built_from_tells(self):
        result, report = self.run_tells("slop.html")
        self.assertEqual(3, result.returncode, result.stderr)
        self.assertEqual("TELLS_FOUND", report["status"])
        self.assertEqual("app", report["kind"])
        self.assertEqual([1440, 390], report["widths"])
        found = {finding["id"] for finding in report["findings"]}
        self.assertEqual(set(tell_ids()) - {"prose-over-budget"}, found)
        stripes = next(f for f in report["findings"] if f["id"] == "left-stripe")
        selectors = " ".join(example["selector"] for example in stripes["examples"])
        self.assertIn("a.active", selectors)
        self.assertIn("callout", selectors)
        rules = next(f for f in report["findings"] if f["id"] == "left-rule")
        self.assertEqual("check", rules["severity"])
        self.assertIn("timeline", rules["examples"][0]["selector"])
        overflow = next(f for f in report["findings"] if f["id"] == "horizontal-overflow")
        self.assertEqual([390], overflow["widths"])
        chrome = next(f for f in report["findings"] if f["id"] == "admin-chrome")
        self.assertEqual([1440], chrome["widths"])

    def test_a_modern_app_page_is_clear(self):
        result, report = self.run_tells("clean.html")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("CLEAR", report["status"])
        self.assertEqual([], report["findings"])
        self.assertEqual("app", report["kind"])

    def test_copy_budget_applies_to_marketing_pages_only(self):
        result, report = self.run_tells("prose.html", "--width", "1440")
        self.assertEqual(3, result.returncode, result.stderr)
        self.assertEqual("marketing", report["kind"])
        self.assertEqual(["prose-over-budget"], [f["id"] for f in report["findings"]])
        self.assertGreater(report["metrics"]["1440"]["proseWords"], 1200)
        result, report = self.run_tells("prose.html", "--width", "1440", "--kind", "app")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], report["findings"])

    def test_an_allowed_tell_is_reported_but_does_not_fail(self):
        result, report = self.run_tells("stripe.html", "--width", "1024")
        self.assertEqual(3, result.returncode, result.stderr)
        self.assertEqual(["left-stripe"], [f["id"] for f in report["findings"]])
        result, report = self.run_tells("stripe.html", "--width", "1024", "--allow", "left-stripe")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("CLEAR", report["status"])
        self.assertEqual([{"id": "left-stripe", "count": 1}], report["allowed"])

    def test_bad_arguments_are_refused(self):
        result, _ = self.run_tells("stripe.html", "--allow", "left-stripes")
        self.assertEqual(1, result.returncode)
        self.assertIn("Unknown tell ID", result.stderr)
        result, _ = self.run_tells("../outside.html")
        self.assertEqual(1, result.returncode)
        result, _ = self.run_tells("stripe.html", "--kind", "poster")
        self.assertEqual(1, result.returncode)
        self.assertIn("--kind", result.stderr)
        result, _ = self.run_tells()
        self.assertEqual(2, result.returncode)
        self.assertIn("observe.mjs tells", result.stderr)


if __name__ == "__main__":
    unittest.main()
