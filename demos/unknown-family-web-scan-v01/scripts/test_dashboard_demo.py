#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


def load_dashboard_module() -> Any:
    module_path = SCRIPT_DIR / "demo_dashboard_server.py"
    spec = importlib.util.spec_from_file_location("demo_dashboard_server", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load dashboard module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Unknown-family Dashboard Demo Regression",
        "",
        "| target | product | port | gate | ranker | resolver used | final | overall |",
        "|---|---|---:|---|---|---:|---|---:|",
    ]
    for row in results:
        evidence = row["scanner_evidence"]
        prediction = row["prediction"]
        resolver = row["resolver"]
        verdict = row["verdict"]
        lines.append(
            "| {target} | {product} | {port} | {gate} | {ranker} | {resolver_used} | {final} | {overall} |".format(
                target=row["truth"]["target_id"],
                product=evidence["product"],
                port=evidence["service_port"],
                gate=prediction["gate"]["decision"],
                ranker=prediction["ranker"]["decision"],
                resolver_used=resolver["used"],
                final=prediction["final_decision"],
                overall=verdict["overall_correct"],
            )
        )
    lines.extend(
        [
            "",
            "## Expected behavior",
            "",
            "- Gate should return `likely_exploitable` for these synthetic vulnerable-looking targets.",
            "- Family Ranker is allowed to produce a raw known-family top score.",
            "- Unknown-family guard must block known-family trust and return `unknown_family`.",
            "- CVE/Module Resolver must not run unless final decision is `ready_for_safe_verification`.",
            "- Final decision should be `unknown_family_triage`.",
        ]
    )
    return "\n".join(lines) + "\n"


def assert_expected(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    target = result["truth"]["target_id"]
    if result["prediction"]["gate"]["decision"] != result["truth"]["expected_gate_decision"]:
        errors.append(f"{target}: gate decision mismatch")
    if result["prediction"]["ranker"]["decision"] != "unknown_family":
        errors.append(f"{target}: ranker guard did not return unknown_family")
    if result["prediction"]["final_decision"] != result["truth"]["expected_final_decision"]:
        errors.append(f"{target}: final decision mismatch")
    if result["resolver"]["used"]:
        errors.append(f"{target}: resolver should not run for unknown-family triage")
    if not result["verdict"]["overall_correct"]:
        errors.append(f"{target}: overall_correct is false")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        default=[],
        help="Target URL. Can be passed multiple times.",
    )
    parser.add_argument(
        "--out-dir",
        default=Path("reports/demos/unknown-family-web-scan-v01/regression"),
        type=Path,
    )
    args = parser.parse_args()

    urls = args.urls or [
        "http://127.0.0.1:18080",
        "http://127.0.0.1:18083",
        "http://127.0.0.1:18084",
    ]

    dashboard = load_dashboard_module()
    out_dir = (REPO_ROOT / args.out_dir).resolve() if not args.out_dir.is_absolute() else args.out_dir
    results = [dashboard.run_scan(url, out_dir / "runs") for url in urls]
    errors = [error for result in results for error in assert_expected(result)]

    write_json(out_dir / "dashboard-demo-regression-results.json", {"results": results, "errors": errors})
    (out_dir / "dashboard-demo-regression-summary.md").write_text(render_markdown(results), encoding="utf-8")

    print(
        json.dumps(
            {
                "targets": len(results),
                "passed": len(errors) == 0,
                "errors": errors,
                "summary": str(out_dir / "dashboard-demo-regression-summary.md"),
                "results": str(out_dir / "dashboard-demo-regression-results.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
