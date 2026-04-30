#!/usr/bin/env python3
"""Build the gh-pages dashboard from a list of run records.

Inputs:
  --history    path to existing runs.jsonl (may not exist on first run)
  --run-json   path to results/run.json from the just-finished pytest invocation
  --report     path to results/report.html from pytest-html
  --out        directory to populate (gets pushed to gh-pages by CI)

Outputs in --out:
  runs.jsonl            full history with the new record appended
  index.html            most-recent runs as a table with status pills
  trends.html           pass-rate + duration over time (Chart.js)
  runs/<sha>/report.html   per-run pytest-html report
  runs/<sha>/run.json
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

INDEX_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SGCO Strapi tests — dashboard</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}}
h1{{margin-bottom:.25rem}}
.sub{{color:#666;margin-bottom:1.5rem}}
.summary{{background:#f4f6f8;border-radius:8px;padding:1rem 1.25rem;margin-bottom:1.5rem;display:flex;gap:2rem;flex-wrap:wrap}}
.summary div b{{font-size:1.4rem;display:block}}
table{{border-collapse:collapse;width:100%}}
th,td{{padding:.5rem .75rem;text-align:left;border-bottom:1px solid #e5e7eb;font-size:.92rem}}
th{{background:#fafafa;font-weight:600}}
.pill{{display:inline-block;padding:.15rem .55rem;border-radius:999px;font-size:.78rem;font-weight:600}}
.green{{background:#dcfce7;color:#166534}}
.red{{background:#fee2e2;color:#991b1b}}
.amber{{background:#fef3c7;color:#92400e}}
a{{color:#2563eb;text-decoration:none}}
a:hover{{text-decoration:underline}}
nav{{margin-bottom:1.5rem}}
nav a{{margin-right:1rem}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem;color:#444}}
</style>
</head>
<body>
<h1>SGCO Strapi tests</h1>
<p class="sub">Updated {generated} UTC · <a href="https://github.com/AjaySharvesh3/sgco-strapi-test">repo</a></p>
<nav><a href="index.html">Recent runs</a><a href="trends.html">Trends</a></nav>
<div class="summary">
  <div><b>{latest_total}</b>tests in latest run</div>
  <div><b style="color:#166534">{latest_passed}</b>passed</div>
  <div><b style="color:#991b1b">{latest_failed}</b>failed</div>
  <div><b style="color:#92400e">{latest_xfailed}</b>xfailed</div>
  <div><b>{latest_duration}s</b>duration</div>
  <div><b>{run_count}</b>runs tracked</div>
</div>
<table>
<thead><tr>
<th>When (UTC)</th><th>Status</th><th>Passed</th><th>Failed</th><th>xFail</th><th>Skipped</th>
<th>Duration</th><th>Branch</th><th>SHA</th><th>Report</th>
</tr></thead>
<tbody>
{rows}
</tbody></table>
</body></html>
"""

ROW_TMPL = (
    "<tr><td>{ts}</td><td>{pill}</td><td>{passed}</td><td>{failed}</td>"
    "<td>{xfailed}</td><td>{skipped}</td><td>{duration}s</td>"
    "<td><code>{branch}</code></td><td><code>{sha_short}</code></td>"
    "<td>{report_link}</td></tr>"
)

TRENDS_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SGCO Strapi tests — trends</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}}
nav a{{margin-right:1rem;color:#2563eb;text-decoration:none}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:1rem;margin-bottom:1.5rem}}
canvas{{max-height:320px}}
</style>
</head>
<body>
<h1>Trends</h1>
<nav><a href="index.html">Recent runs</a><a href="trends.html">Trends</a></nav>
<div class="card"><h3>Pass rate over time</h3><canvas id="pass"></canvas></div>
<div class="card"><h3>Counts per run</h3><canvas id="counts"></canvas></div>
<div class="card"><h3>Duration (seconds)</h3><canvas id="dur"></canvas></div>
<script>
const data = {data_json};
const labels = data.map(r => r.timestamp);
const passRate = data.map(r => {{
  const c = r.counts || {{}};
  const total = (c.passed||0)+(c.failed||0)+(c.error||0);
  return total ? Math.round(100*(c.passed||0)/total) : null;
}});
const passed = data.map(r => r.counts?.passed || 0);
const failed = data.map(r => r.counts?.failed || 0);
const xfailed = data.map(r => r.counts?.xfailed || 0);
const skipped = data.map(r => r.counts?.skipped || 0);
const durations = data.map(r => r.duration_seconds || 0);
const opts = {{responsive:true, scales:{{x:{{ticks:{{maxRotation:0,autoSkip:true}}}}}}}};
new Chart(document.getElementById('pass'), {{type:'line', data:{{labels, datasets:[{{label:'Pass rate %', data:passRate, borderColor:'#16a34a', tension:.2}}]}}, options:opts}});
new Chart(document.getElementById('counts'), {{type:'bar', data:{{labels, datasets:[
  {{label:'Passed', data:passed, backgroundColor:'#16a34a'}},
  {{label:'Failed', data:failed, backgroundColor:'#dc2626'}},
  {{label:'xFailed', data:xfailed, backgroundColor:'#d97706'}},
  {{label:'Skipped', data:skipped, backgroundColor:'#9ca3af'}},
]}}, options:{{...opts, scales:{{x:{{stacked:true}}, y:{{stacked:true}}}}}}}});
new Chart(document.getElementById('dur'), {{type:'line', data:{{labels, datasets:[{{label:'Seconds', data:durations, borderColor:'#2563eb', tension:.2}}]}}, options:opts}});
</script>
</body></html>
"""


def status_pill(rec: dict) -> str:
    c = rec.get("counts", {})
    failed = c.get("failed", 0) + c.get("error", 0)
    if failed:
        return '<span class="pill red">failed</span>'
    if c.get("passed", 0) == 0 and c.get("skipped", 0):
        return '<span class="pill amber">all-skipped</span>'
    if c.get("xfailed", 0):
        return '<span class="pill amber">passed (with xfail)</span>'
    return '<span class="pill green">passed</span>'


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history", required=True, help="existing runs.jsonl (or empty path)")
    p.add_argument("--run-json", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-rows", type=int, default=100, help="rows in index table")
    args = p.parse_args()

    history_path = Path(args.history)
    new_run = json.loads(Path(args.run_json).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    history: list[dict] = []
    if history_path.exists():
        for line in history_path.read_text().splitlines():
            line = line.strip()
            if line:
                history.append(json.loads(line))
    history.append(new_run)

    # Write history
    (out / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in history) + "\n")

    # Per-run report dir
    sha = new_run.get("git_sha", "unknown")[:12] or "unknown"
    run_dir = out / "runs" / sha
    run_dir.mkdir(parents=True, exist_ok=True)
    if Path(args.report).exists():
        shutil.copy(args.report, run_dir / "report.html")
    shutil.copy(args.run_json, run_dir / "run.json")

    # Build index rows (newest first)
    rows = []
    for rec in reversed(history[-args.max_rows:]):
        c = rec.get("counts", {})
        rec_sha = (rec.get("git_sha") or "")[:12]
        report_link = (
            f'<a href="runs/{rec_sha}/report.html">html</a>'
            if rec_sha and (out / "runs" / rec_sha / "report.html").exists()
            else "—"
        )
        rows.append(ROW_TMPL.format(
            ts=rec.get("timestamp", ""), pill=status_pill(rec),
            passed=c.get("passed", 0), failed=c.get("failed", 0),
            xfailed=c.get("xfailed", 0), skipped=c.get("skipped", 0),
            duration=rec.get("duration_seconds", 0),
            branch=rec.get("git_branch", "") or "—",
            sha_short=rec_sha or "—",
            report_link=report_link,
        ))

    latest = new_run.get("counts", {})
    total = sum(latest.get(k, 0) for k in ("passed", "failed", "skipped", "error", "xfailed", "xpassed"))
    (out / "index.html").write_text(INDEX_TMPL.format(
        generated=new_run.get("timestamp", ""),
        latest_total=total,
        latest_passed=latest.get("passed", 0),
        latest_failed=latest.get("failed", 0) + latest.get("error", 0),
        latest_xfailed=latest.get("xfailed", 0),
        latest_duration=new_run.get("duration_seconds", 0),
        run_count=len(history),
        rows="\n".join(rows),
    ))

    (out / "trends.html").write_text(TRENDS_TMPL.format(
        data_json=json.dumps(history),
    ))

    print(f"dashboard written to {out} ({len(history)} runs)")


if __name__ == "__main__":
    main()
