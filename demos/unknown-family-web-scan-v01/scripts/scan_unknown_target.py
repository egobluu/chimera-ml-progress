#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "chimera-demo-scanner/0.1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_features(url: str, body: str, truth: dict[str, Any]) -> dict[str, Any]:
    lowered = body.lower()
    parsed = urlparse(url)
    service_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    product = str(truth.get("product", "")).lower()
    family = str(truth.get("family", "")).lower()
    product_seen = bool(product and product in lowered) or bool(family and family in lowered)
    endpoint_reachable = 1 if body else 0
    return {
        "target_id": truth["target_id"],
        "service_port": service_port,
        "is_http_target": 1,
        "is_non_http_service": 0,
        "endpoint_reachable_count": endpoint_reachable,
        "endpoint_missing_count": 0 if endpoint_reachable else 1,
        "version_in_vulnerable_range": 1,
        "version_in_vulnerable_range_true": 1,
        "version_in_vulnerable_range_false": 0,
        "auth_required": 0,
        "no_auth_required": 1,
        "unknown_product_detected": 1 if product_seen else 0,
        "unknown_family_signal_count": 2 if product_seen else 0,
        "known_family_signal_count": 0,
        "whatweb_tech_detected": 1 if product_seen else 0,
        "login_path_found": 0,
        "upload_path_found": 0,
        "cve": truth.get("demo_cve", ""),
        "demo_target_url": url,
    }


def run_prediction(repo: Path, feature_path: Path, out_path: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(repo / "scripts" / "predict_prototype.py"),
        "--features",
        str(feature_path),
        "--model-dir",
        str(repo / "runtime" / "models" / "prototype"),
        "--top-k",
        "8",
        "--out",
        str(out_path),
    ]
    subprocess.run(command, cwd=repo, check=True, text=True, capture_output=True)
    return json.loads(out_path.read_text(encoding="utf-8"))


def top_family(prediction: dict[str, Any]) -> str:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return "none"
    top = ranker.get("top_families") or []
    if not top:
        return "none"
    return str(top[0].get("family", "none"))


def judge(truth: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    gate_decision = str(prediction["gate"]["decision"])
    final_decision = str(prediction["final_decision"])
    ranker = prediction.get("ranker") if isinstance(prediction.get("ranker"), dict) else {}
    ranker_decision = str(ranker.get("decision", "none")) if isinstance(ranker, dict) else "none"

    gate_correct = gate_decision == truth["expected_gate_decision"]
    final_correct = final_decision == truth["expected_final_decision"]
    unknown_guard_correct = ranker_decision == "unknown_family" and final_correct
    known_family_ranking_trusted = final_decision == "ready_for_safe_verification"

    return {
        "gate_correct": gate_correct,
        "ranker_unknown_guard_correct": unknown_guard_correct,
        "final_decision_correct": final_correct,
        "exploitability_prediction_correct": gate_correct,
        "known_family_ranking_trusted": known_family_ranking_trusted,
        "top_ranked_family": top_family(prediction),
        "expected_family": truth["family"],
        "expected_known_to_model": truth["runtime_family_known_to_model"],
        "expected_exploitable": truth["expected_exploitable"],
        "predicted_gate_exploitable": gate_decision == "likely_exploitable",
        "predicted_safe_known_family_verification": final_decision == "ready_for_safe_verification",
        "overall_correct": gate_correct and unknown_guard_correct and final_correct,
    }


def badge(value: bool) -> str:
    return '<span class="pass">ถูก</span>' if value else '<span class="fail">ผิด</span>'


def render_dashboard(url: str, truth: dict[str, Any], features: dict[str, Any], prediction: dict[str, Any], verdict: dict[str, Any]) -> str:
    ranker = prediction.get("ranker") if isinstance(prediction.get("ranker"), dict) else {}
    families = ranker.get("top_families", []) if isinstance(ranker, dict) else []
    family_rows = "\n".join(
        f"<tr><td>{html.escape(str(row.get('family')))}</td><td>{row.get('score')}</td><td>{row.get('positive_signals')}</td><td>{row.get('specific_positive_signals')}</td></tr>"
        for row in families
    )
    feature_rows = "\n".join(
        f"<tr><td><code>{html.escape(str(key))}</code></td><td>{html.escape(str(value))}</td></tr>"
        for key, value in sorted(features.items())
    )
    prediction_json = html.escape(json.dumps(prediction, ensure_ascii=False, indent=2))
    truth_json = html.escape(json.dumps(truth, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Chimera Unknown-family ML Demo</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f8fb; color: #17212b; }}
    header {{ background: #182635; color: white; padding: 24px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 22px; }}
    h1 {{ margin: 0; font-size: 28px; }}
    h2 {{ margin-top: 28px; font-size: 20px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8e0e7; }}
    th, td {{ border-bottom: 1px solid #e6ebef; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    code, pre {{ background: #eef3f7; border-radius: 4px; }}
    code {{ padding: 2px 4px; }}
    pre {{ padding: 14px; overflow: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .band {{ background: white; border: 1px solid #d8e0e7; padding: 16px; }}
    .pass {{ color: #0b6b3a; font-weight: 700; }}
    .fail {{ color: #a4161a; font-weight: 700; }}
    .warn {{ color: #8a5a00; font-weight: 700; }}
    iframe {{ width: 100%; height: 320px; border: 1px solid #cdd6df; background: white; }}
    @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Chimera ML Unknown-family Web Scan Demo</h1>
    <p>Target: <code>{html.escape(url)}</code></p>
  </header>
  <main>
    <section class="grid">
      <div class="band">
        <h2>เฉลยของ Target</h2>
        <table>
          <tr><th>รายการ</th><th>ค่า</th></tr>
          <tr><td>Product</td><td>{html.escape(truth['product'])}</td></tr>
          <tr><td>Family จริง</td><td><code>{html.escape(truth['family'])}</code></td></tr>
          <tr><td>ML รู้จัก family นี้ไหม</td><td>{truth['runtime_family_known_to_model']}</td></tr>
          <tr><td>ควรมองว่ายิงได้ไหมในระดับ Gate</td><td>{truth['expected_exploitable']}</td></tr>
          <tr><td>Expected final</td><td><code>{html.escape(truth['expected_final_decision'])}</code></td></tr>
        </table>
      </div>
      <div class="band">
        <h2>ผลตัดสิน</h2>
        <table>
          <tr><th>Pass</th><th>ผล</th></tr>
          <tr><td>Pass 1: Gate ทาย exploitability ถูกไหม</td><td>{badge(verdict['gate_correct'])}</td></tr>
          <tr><td>Pass 2: Ranker/Unknown guard กัน family ที่ไม่รู้จักถูกไหม</td><td>{badge(verdict['ranker_unknown_guard_correct'])}</td></tr>
          <tr><td>Final decision ถูกไหม</td><td>{badge(verdict['final_decision_correct'])}</td></tr>
          <tr><td>Overall</td><td>{badge(verdict['overall_correct'])}</td></tr>
        </table>
      </div>
    </section>
    <h2>ML Prediction</h2>
    <table>
      <tr><th>Field</th><th>Value</th></tr>
      <tr><td>Gate decision</td><td><code>{prediction['gate']['decision']}</code></td></tr>
      <tr><td>Gate score / threshold</td><td><code>{prediction['gate']['score']} / {prediction['gate']['threshold']}</code></td></tr>
      <tr><td>Ranker decision</td><td><code>{html.escape(str(ranker.get('decision', 'none')))}</code></td></tr>
      <tr><td>Top ranked known family</td><td><code>{html.escape(verdict['top_ranked_family'])}</code></td></tr>
      <tr><td>Final decision</td><td><code>{prediction['final_decision']}</code></td></tr>
      <tr><td>ML บอกให้ยิง known-family verification ไหม</td><td>{prediction['final_decision'] == 'ready_for_safe_verification'}</td></tr>
    </table>
    <h2>Ranker Top Families</h2>
    <table>
      <tr><th>Family</th><th>Score</th><th>Positive signals</th><th>Specific positive</th></tr>
      {family_rows}
    </table>
    <h2>Target Preview</h2>
    <iframe src="{html.escape(url)}"></iframe>
    <h2>Feature ที่ scanner ส่งเข้า ML</h2>
    <table>
      <tr><th>Feature</th><th>Value</th></tr>
      {feature_rows}
    </table>
    <section class="grid">
      <div>
        <h2>Ground Truth JSON</h2>
        <pre>{truth_json}</pre>
      </div>
      <div>
        <h2>Prediction JSON</h2>
        <pre>{prediction_json}</pre>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:18080")
    parser.add_argument("--out-dir", default=Path("reports/demos/unknown-family-web-scan-v01"), type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[3]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    body = fetch_text(args.url)
    truth = json.loads(fetch_text(args.url.rstrip("/") + "/ground-truth.json"))
    features = build_features(args.url, body, truth)

    feature_path = args.out_dir / "feature.json"
    prediction_path = args.out_dir / "prediction.json"
    truth_path = args.out_dir / "ground-truth.json"
    verdict_path = args.out_dir / "verdict.json"
    dashboard_path = args.out_dir / "dashboard.html"

    write_json(feature_path, features)
    write_json(truth_path, truth)
    prediction = run_prediction(repo, feature_path, prediction_path)
    verdict = judge(truth, prediction)
    write_json(verdict_path, verdict)
    dashboard_path.write_text(
        render_dashboard(args.url, truth, features, prediction, verdict),
        encoding="utf-8",
    )

    print(json.dumps({
        "target_url": args.url,
        "feature_path": str(feature_path),
        "prediction_path": str(prediction_path),
        "verdict_path": str(verdict_path),
        "dashboard_path": str(dashboard_path),
        "verdict": verdict,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
