#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


def load_scanner_module() -> Any:
    module_path = SCRIPT_DIR / "scan_unknown_target.py"
    spec = importlib.util.spec_from_file_location("scan_unknown_target", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scanner module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCANNER = load_scanner_module()


FAMILY_RESOLVER = {
    "redis": {
        "cve_candidates": ["CVE-2022-0543"],
        "modules": ["exploit/linux/redis/redis_debian_sandbox_escape"],
        "manual_poc": "Redis Lua sandbox escape precheck",
    },
    "grafana": {
        "cve_candidates": ["CVE-2021-43798"],
        "modules": ["auxiliary/scanner/http/grafana_plugin_traversal"],
        "manual_poc": "Grafana public plugin path traversal probe",
    },
    "solr_velocity": {
        "cve_candidates": ["CVE-2019-17558", "CVE-2017-12629"],
        "modules": ["exploit/multi/http/solr_velocity_rce"],
        "manual_poc": "Velocity template RCE probe",
    },
    "tomcat_put": {
        "cve_candidates": ["CVE-2017-12615"],
        "modules": ["exploit/multi/http/tomcat_jsp_upload_bypass"],
        "manual_poc": "HTTP PUT JSP upload precheck",
    },
    "tomcat_ajp": {
        "cve_candidates": ["CVE-2020-1938"],
        "modules": ["auxiliary/admin/http/tomcat_ghostcat"],
        "manual_poc": "AJP Ghostcat readable file probe",
    },
    "couchdb_auth": {
        "cve_candidates": ["CVE-2017-12635"],
        "modules": ["exploit/multi/http/apache_couchdb_cmd_exec"],
        "manual_poc": "CouchDB admin party/auth bypass probe",
    },
}


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def validate_local_target_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL ต้องขึ้นต้นด้วย http:// หรือ https://")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("demo นี้อนุญาตให้สแกนเฉพาะ localhost/127.0.0.1 เท่านั้น")
    if not parsed.netloc:
        raise ValueError("URL ไม่สมบูรณ์")
    return raw_url.rstrip("/")


def artifact_paths(out_dir: Path, target_id: str) -> dict[str, Path]:
    safe_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in target_id)
    run_dir = out_dir / safe_id
    return {
        "run_dir": run_dir,
        "feature": run_dir / "feature.json",
        "truth": run_dir / "ground-truth.json",
        "prediction": run_dir / "prediction.json",
        "verdict": run_dir / "verdict.json",
    }


def build_scanner_evidence(url: str, body: str, truth: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "local_http_demo_target",
        "scanner_tools": [
            {
                "name": "python urllib.request",
                "role_th": "ดึงหน้าเว็บ target แบบ HTTP GET เพื่อดูว่า endpoint ตอบไหมและอ่าน body",
                "output_used": ["http_body_bytes", "endpoint_reachable"],
            },
            {
                "name": "local lab ground-truth.json",
                "role_th": "ใช้เป็นเฉลยของ demo/lab เท่านั้น เพื่อเทียบว่า ML ทายถูกไหม",
                "output_used": ["target_id", "product", "family", "expected_gate_decision", "expected_final_decision"],
            },
            {
                "name": "scan_unknown_target.py feature builder",
                "role_th": "แปลงหลักฐานจาก scanner เป็น feature JSON ที่ ML อ่านได้",
                "output_used": ["unknown_product_detected", "unknown_family_signal_count", "known_family_signal_count"],
            },
            {
                "name": "scripts/predict_prototype.py",
                "role_th": "โหลด Gate model และ Family Ranker model แล้วสร้างผลตัดสิน runtime",
                "output_used": ["gate", "ranker", "final_decision", "reason_features", "schema_warnings"],
            },
        ],
        "target_url": url,
        "http_body_bytes": len(body.encode("utf-8")),
        "endpoint_reachable": bool(features.get("endpoint_reachable_count")),
        "ground_truth_endpoint": f"{url}/ground-truth.json",
        "product_seen_in_page": bool(features.get("unknown_product_detected")),
        "product": truth.get("product"),
        "family_from_lab_truth": truth.get("family"),
        "demo_cve_from_lab_truth": truth.get("demo_cve"),
        "service_port": features.get("service_port"),
    }


def resolve_cve_modules(prediction: dict[str, Any]) -> dict[str, Any]:
    final_decision = prediction.get("final_decision")
    ranker = prediction.get("ranker") if isinstance(prediction.get("ranker"), dict) else {}
    top_families = ranker.get("top_families", []) if isinstance(ranker, dict) else []
    top_family = str(top_families[0].get("family", "none")) if top_families else "none"

    if final_decision != "ready_for_safe_verification":
        return {
            "used": False,
            "family_used": None,
            "reason_th": "ยังไม่ map ไป CVE/module เพราะผลสุดท้ายไม่ใช่ known-family ที่พร้อมตรวจต่อ",
            "raw_ranker_top_family": top_family,
            "cve_candidates": [],
            "metasploit_modules": [],
            "manual_poc": None,
        }

    mapped = FAMILY_RESOLVER.get(top_family, {})
    return {
        "used": True,
        "family_used": top_family,
        "reason_th": "ใช้ family อันดับหนึ่งที่ผ่าน guard แล้วไปเปิดตาราง resolver",
        "raw_ranker_top_family": top_family,
        "cve_candidates": mapped.get("cve_candidates", []),
        "metasploit_modules": mapped.get("modules", []),
        "manual_poc": mapped.get("manual_poc"),
    }


def run_scan(url: str, out_dir: Path) -> dict[str, Any]:
    body = SCANNER.fetch_text(url)
    truth = json.loads(SCANNER.fetch_text(url + "/ground-truth.json"))
    features = SCANNER.build_features(url, body, truth)
    scanner_evidence = build_scanner_evidence(url, body, truth, features)
    paths = artifact_paths(out_dir, str(features["target_id"]))
    paths["run_dir"].mkdir(parents=True, exist_ok=True)

    SCANNER.write_json(paths["feature"], features)
    SCANNER.write_json(paths["truth"], truth)
    prediction = SCANNER.run_prediction(REPO_ROOT, paths["feature"], paths["prediction"])
    resolver = resolve_cve_modules(prediction)
    verdict = SCANNER.judge(truth, prediction)
    SCANNER.write_json(paths["verdict"], verdict)

    return {
        "target_url": url,
        "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scanner_evidence": scanner_evidence,
        "truth": truth,
        "features": features,
        "prediction": prediction,
        "resolver": resolver,
        "verdict": verdict,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }


def render_page(default_url: str) -> str:
    safe_default = html.escape(default_url, quote=True)
    return f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Chimera ML Scan Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fa;
      --ink: #17212b;
      --muted: #5d6975;
      --line: #d8e0e7;
      --soft: #edf2f6;
      --panel: #ffffff;
      --accent: #275d8c;
      --accent-ink: #ffffff;
      --good: #0b6b3a;
      --bad: #a4161a;
      --warn: #8a5a00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      background: #1f2d3a;
      color: #fff;
      padding: 24px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px;
    }}
    h1 {{ margin: 0; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 30px 0 12px; font-size: 20px; letter-spacing: 0; }}
    p {{ line-height: 1.55; }}
    label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    .scan-band {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 18px;
    }}
    .scan-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: end;
    }}
    input {{
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 12px;
      font-size: 16px;
      color: var(--ink);
      background: var(--panel);
    }}
    button {{
      min-height: 44px;
      border: 0;
      border-radius: 6px;
      padding: 10px 16px;
      font-weight: 700;
      color: var(--accent-ink);
      background: var(--accent);
      cursor: pointer;
      white-space: nowrap;
    }}
    button:disabled {{ cursor: wait; opacity: 0.7; }}
    .hint {{ color: var(--muted); margin: 10px 0 0; }}
    .status {{
      margin-top: 12px;
      min-height: 24px;
      color: var(--muted);
      font-weight: 700;
    }}
    .error {{ color: var(--bad); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .flow {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 16px;
    }}
    .step {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 14px;
      min-height: 150px;
    }}
    .step strong {{
      display: block;
      margin-bottom: 8px;
    }}
    .step-value {{
      display: block;
      margin: 8px 0;
      font-size: 18px;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    th, td {{
      border-bottom: 1px solid #e6ebef;
      padding: 10px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ background: var(--soft); }}
    code, pre {{
      background: var(--soft);
      border-radius: 4px;
    }}
    code {{ padding: 2px 4px; }}
    pre {{
      padding: 14px;
      overflow: auto;
      max-height: 430px;
    }}
    iframe {{
      width: 100%;
      height: 320px;
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .pass {{ color: var(--good); font-weight: 700; }}
    .fail {{ color: var(--bad); font-weight: 700; }}
    .warn {{ color: var(--warn); font-weight: 700; }}
    .hidden {{ display: none; }}
    @media (max-width: 760px) {{
      main {{ padding: 14px; }}
      header {{ padding: 18px; }}
      h1 {{ font-size: 23px; }}
      .scan-row, .grid, .flow {{ grid-template-columns: 1fr; }}
      button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Chimera ML Scan Dashboard</h1>
    <p>ใส่ target URL ก่อน แล้วค่อยกด Scan เพื่อให้ระบบสร้าง feature, เรียก Gate/Ranker และโชว์เฉลยเทียบกับผล ML</p>
  </header>
  <main>
    <section class="scan-band" aria-labelledby="scan-title">
      <h2 id="scan-title">Scan target</h2>
      <form id="scan-form">
        <label for="target-url">Target URL</label>
        <div class="scan-row">
          <input id="target-url" name="target-url" value="{safe_default}" autocomplete="off" spellcheck="false">
          <button id="scan-button" type="submit">Scan</button>
        </div>
      </form>
      <p class="hint">demo นี้ล็อกให้สแกนเฉพาะ localhost/127.0.0.1 เพื่อกันการเอาหน้านี้ไปยิงเป้าข้างนอกโดยไม่ได้ตั้งใจ</p>
      <div id="status" class="status" aria-live="polite">ยังไม่ได้สแกน target</div>
    </section>

    <section id="results" class="hidden" aria-live="polite">
      <h2>สแกนจากอะไร</h2>
      <table id="evidence-table"></table>

      <h2>เครื่องมือที่ใช้ใน demo scan</h2>
      <table id="tool-table"></table>

      <h2>3 ชั้นของการตัดสินใจ</h2>
      <section class="flow">
        <div class="step">
          <strong>1. Gate</strong>
          <span id="gate-step" class="step-value"></span>
          <p>ตอบคำถามแรกว่า target นี้มี precondition พอให้ลองตรวจ exploit ต่อไหม</p>
        </div>
        <div class="step">
          <strong>2. Family Ranker</strong>
          <span id="ranker-step" class="step-value"></span>
          <p>ถ้า Gate ผ่าน จะจัดอันดับ exploit family ที่น่าจะตรง แต่ยังต้องผ่าน guard ก่อน</p>
        </div>
        <div class="step">
          <strong>3. CVE/Module Resolver</strong>
          <span id="resolver-step" class="step-value"></span>
          <p>เอา known family ที่ผ่าน guard แล้วไป map เป็น CVE, Metasploit module หรือ manual PoC</p>
        </div>
      </section>

      <section class="grid">
        <div class="panel">
          <h2>เฉลยของ Target</h2>
          <table id="truth-table"></table>
        </div>
        <div class="panel">
          <h2>ผลตัดสิน</h2>
          <table id="verdict-table"></table>
        </div>
      </section>

      <h2>ML Prediction</h2>
      <table id="prediction-table"></table>

      <h2>CVE/Module Resolver</h2>
      <table id="resolver-table"></table>

      <h2>Ranker Top Families</h2>
      <table id="families-table"></table>

      <h2>Target Preview</h2>
      <iframe id="target-preview" title="target preview"></iframe>

      <h2>Feature ที่ scanner ส่งเข้า ML</h2>
      <table id="feature-table"></table>

      <section class="grid">
        <div>
          <h2>Ground Truth JSON</h2>
          <pre id="truth-json"></pre>
        </div>
        <div>
          <h2>Prediction JSON</h2>
          <pre id="prediction-json"></pre>
        </div>
      </section>
    </section>
  </main>

  <script>
    const form = document.getElementById("scan-form");
    const input = document.getElementById("target-url");
    const button = document.getElementById("scan-button");
    const statusEl = document.getElementById("status");
    const resultsEl = document.getElementById("results");

    const esc = (value) => String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    const yesNo = (value) => value ? "true" : "false";
    const badge = (value) => value
      ? '<span class="pass">ถูก</span>'
      : '<span class="fail">ผิด</span>';

    const makeRows = (rows) => rows.map(([left, right]) =>
      `<tr><td>${{esc(left)}}</td><td>${{right}}</td></tr>`
    ).join("");

    function render(result) {{
      const truth = result.truth;
      const prediction = result.prediction;
      const evidence = result.scanner_evidence || {{}};
      const resolver = result.resolver || {{}};
      const verdict = result.verdict;
      const ranker = prediction.ranker || {{}};
      const families = ranker.top_families || [];

      document.getElementById("evidence-table").innerHTML =
        "<tr><th>หลักฐานที่ scanner ใช้</th><th>ค่า</th></tr>" + makeRows([
          ["แหล่งที่สแกน", `<code>${{esc(evidence.source || "unknown")}}</code>`],
          ["Target URL", `<code>${{esc(evidence.target_url || result.target_url)}}</code>`],
          ["หน้าเว็บตอบกลับไหม", esc(yesNo(evidence.endpoint_reachable))],
          ["ขนาด HTTP body", esc((evidence.http_body_bytes || 0) + " bytes")],
          ["Product ที่เห็นในหน้า", esc(evidence.product || "")],
          ["Family จากเฉลย lab", `<code>${{esc(evidence.family_from_lab_truth || "")}}</code>`],
          ["CVE demo จากเฉลย lab", `<code>${{esc(evidence.demo_cve_from_lab_truth || "")}}</code>`],
          ["Port ที่ส่งเป็น feature", `<code>${{esc(evidence.service_port || "")}}</code>`],
          ["Ground truth endpoint", `<code>${{esc(evidence.ground_truth_endpoint || "")}}</code>`],
        ]);

      document.getElementById("tool-table").innerHTML =
        "<tr><th>เครื่องมือ/ขั้นตอน</th><th>หน้าที่</th><th>ค่าที่เอาไปใช้</th></tr>" +
        (evidence.scanner_tools || []).map((tool) =>
          `<tr><td><code>${{esc(tool.name)}}</code></td><td>${{esc(tool.role_th)}}</td><td><code>${{esc((tool.output_used || []).join(", "))}}</code></td></tr>`
        ).join("");

      document.getElementById("truth-table").innerHTML =
        "<tr><th>รายการ</th><th>ค่า</th></tr>" + makeRows([
          ["Product", esc(truth.product)],
          ["Family จริง", `<code>${{esc(truth.family)}}</code>`],
          ["ML รู้จัก family นี้ไหม", esc(yesNo(truth.runtime_family_known_to_model))],
          ["ควรมองว่ายิงได้ไหมในระดับ Gate", esc(yesNo(truth.expected_exploitable))],
          ["Expected final", `<code>${{esc(truth.expected_final_decision)}}</code>`],
        ]);

      document.getElementById("verdict-table").innerHTML =
        "<tr><th>Pass</th><th>ผล</th></tr>" + makeRows([
          ["Pass 1: Gate ทาย exploitability ถูกไหม", badge(verdict.gate_correct)],
          ["Pass 2: Ranker/Unknown guard กัน family ที่ไม่รู้จักถูกไหม", badge(verdict.ranker_unknown_guard_correct)],
          ["Final decision ถูกไหม", badge(verdict.final_decision_correct)],
          ["Overall", badge(verdict.overall_correct)],
        ]);

      document.getElementById("prediction-table").innerHTML =
        "<tr><th>Field</th><th>Value</th></tr>" + makeRows([
          ["Gate decision", `<code>${{esc(prediction.gate.decision)}}</code>`],
          ["Gate score / threshold", `<code>${{esc(prediction.gate.score)}} / ${{esc(prediction.gate.threshold)}}</code>`],
          ["Ranker decision", `<code>${{esc(ranker.decision || "none")}}</code>`],
          ["Top ranked known family", `<code>${{esc(verdict.top_ranked_family)}}</code>`],
          ["Final decision", `<code>${{esc(prediction.final_decision)}}</code>`],
          ["ML บอกให้ยิง known-family verification ไหม", esc(yesNo(prediction.final_decision === "ready_for_safe_verification"))],
        ]);

      document.getElementById("gate-step").innerHTML = `<code>${{esc(prediction.gate.decision)}}</code>`;
      document.getElementById("ranker-step").innerHTML = `<code>${{esc(ranker.decision || "none")}}</code>`;
      document.getElementById("resolver-step").innerHTML = resolver.used
        ? `<code>${{esc(resolver.family_used)}}</code>`
        : '<span class="warn">ยังไม่ใช้ resolver</span>';

      document.getElementById("resolver-table").innerHTML =
        "<tr><th>Field</th><th>Value</th></tr>" + makeRows([
          ["Resolver ถูกใช้ไหม", esc(yesNo(resolver.used))],
          ["เหตุผล", esc(resolver.reason_th || "")],
          ["Family ที่ Ranker ให้คะแนนสูงสุด", `<code>${{esc(resolver.raw_ranker_top_family || "none")}}</code>`],
          ["Family ที่ใช้ map จริง", `<code>${{esc(resolver.family_used || "none")}}</code>`],
          ["CVE candidates", `<code>${{esc((resolver.cve_candidates || []).join(", ") || "none")}}</code>`],
          ["Metasploit modules", `<code>${{esc((resolver.metasploit_modules || []).join(", ") || "none")}}</code>`],
          ["Manual PoC", `<code>${{esc(resolver.manual_poc || "none")}}</code>`],
        ]);

      document.getElementById("families-table").innerHTML =
        "<tr><th>Family</th><th>Score</th><th>Positive signals</th><th>Specific positive</th></tr>" +
        families.map((row) =>
          `<tr><td>${{esc(row.family)}}</td><td>${{esc(row.score)}}</td><td>${{esc(row.positive_signals)}}</td><td>${{esc(row.specific_positive_signals)}}</td></tr>`
        ).join("");

      document.getElementById("feature-table").innerHTML =
        "<tr><th>Feature</th><th>Value</th></tr>" +
        Object.entries(result.features).sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) =>
          `<tr><td><code>${{esc(key)}}</code></td><td>${{esc(value)}}</td></tr>`
        ).join("");

      document.getElementById("target-preview").src = result.target_url;
      document.getElementById("truth-json").textContent = JSON.stringify(truth, null, 2);
      document.getElementById("prediction-json").textContent = JSON.stringify(prediction, null, 2);
      resultsEl.classList.remove("hidden");
      statusEl.textContent = `สแกนเสร็จ: ${{result.target_url}}`;
      statusEl.classList.remove("error");
    }}

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      resultsEl.classList.add("hidden");
      statusEl.textContent = "กำลังสแกน target และเรียก ML...";
      statusEl.classList.remove("error");
      button.disabled = true;
      try {{
        const response = await fetch("/api/scan", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ url: input.value }}),
        }});
        const payload = await response.json();
        if (!response.ok) {{
          throw new Error(payload.error || "scan failed");
        }}
        render(payload);
      }} catch (error) {{
        statusEl.textContent = `สแกนไม่สำเร็จ: ${{error.message}}`;
        statusEl.classList.add("error");
      }} finally {{
        button.disabled = false;
      }}
    }});
  </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "ChimeraDemoDashboard/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path in {"/", "/dashboard"}:
            body = render_page(self.server.default_url).encode("utf-8")  # type: ignore[attr-defined]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/healthz":
            send_json(self, 200, {"ok": True})
            return
        send_json(self, 404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/scan":
            send_json(self, 404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            url = validate_local_target_url(str(payload.get("url", "")))
            result = run_scan(url, self.server.out_dir)  # type: ignore[attr-defined]
            send_json(self, 200, result)
        except Exception as exc:
            send_json(self, 400, {"error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=18082, type=int)
    parser.add_argument("--default-url", default="http://127.0.0.1:18080")
    parser.add_argument(
        "--out-dir",
        default=Path("reports/demos/unknown-family-web-scan-v01/interactive"),
        type=Path,
    )
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    server.default_url = args.default_url
    server.out_dir = args.out_dir.resolve()
    server.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Serving Chimera ML scan dashboard on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
