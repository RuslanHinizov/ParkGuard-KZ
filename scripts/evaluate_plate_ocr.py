"""
evaluate_plate_ocr.py — Gercek OCR accuracy degerlendirme araci

Kullanim:
  1) Ground truth template export et:
     python scripts/evaluate_plate_ocr.py --export-template

  2) CSV'de expected_plate kolonunu doldur:
     alarm_id, expected_plate, ...

  3) Accuracy raporu al:
     python scripts/evaluate_plate_ocr.py --ground-truth backend/artifacts/ocr_eval/ground_truth_template.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import DATA_DIR, DB_PATH  # noqa: E402


GT_FIELD_CANDIDATES = ("expected_plate", "ground_truth", "gt_plate", "true_plate")


@dataclass
class AlarmSample:
    alarm_id: str
    created_at: str
    predicted_plate: str
    predicted_conf: float
    screenshot: str | None
    plate_screenshot: str | None

    @property
    def screenshot_abs(self) -> str | None:
        return resolve_data_path(self.screenshot)

    @property
    def plate_screenshot_abs(self) -> str | None:
        return resolve_data_path(self.plate_screenshot)


def resolve_data_path(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    path = DATA_DIR / relative_path
    return str(path.resolve())


def normalize_plate(value: str | None) -> str:
    if not value:
        return ""
    cleaned = "".join(ch for ch in value.upper().strip() if ch.isalnum())
    return cleaned


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    prev = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        curr = [i]
        for j, right_char in enumerate(right, start=1):
            ins = curr[j - 1] + 1
            delete = prev[j] + 1
            replace = prev[j - 1] + (left_char != right_char)
            curr.append(min(ins, delete, replace))
        prev = curr
    return prev[-1]


def char_accuracy(expected: str, predicted: str) -> float:
    max_len = max(len(expected), len(predicted), 1)
    distance = levenshtein(expected, predicted)
    return max(0.0, 1.0 - (distance / max_len))


def load_alarm_samples(limit: int) -> list[AlarmSample]:
    query = """
        SELECT id, created_at, plate, plate_conf, screenshot, plate_screenshot
        FROM alarms
        WHERE plate IS NOT NULL
          AND plate_screenshot IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        rows = conn.execute(query, (limit,)).fetchall()

    samples = [
        AlarmSample(
            alarm_id=row[0],
            created_at=row[1],
            predicted_plate=normalize_plate(row[2]),
            predicted_conf=float(row[3] or 0.0),
            screenshot=row[4],
            plate_screenshot=row[5],
        )
        for row in rows
    ]
    return samples


def export_template(samples: list[AlarmSample], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "alarm_id",
                "created_at",
                "predicted_plate",
                "predicted_conf",
                "screenshot",
                "plate_screenshot",
                "expected_plate",
                "notes",
            ],
        )
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "alarm_id": sample.alarm_id,
                    "created_at": sample.created_at,
                    "predicted_plate": sample.predicted_plate,
                    "predicted_conf": f"{sample.predicted_conf:.3f}",
                    "screenshot": sample.screenshot_abs or "",
                    "plate_screenshot": sample.plate_screenshot_abs or "",
                    "expected_plate": "",
                    "notes": "",
                }
            )


def read_ground_truth(ground_truth_csv: Path) -> dict[str, str]:
    if not ground_truth_csv.exists():
        raise FileNotFoundError(f"Ground truth CSV bulunamadi: {ground_truth_csv}")

    mapping: dict[str, str] = {}
    with ground_truth_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Ground truth CSV bos veya header yok")

        gt_field = next((field for field in GT_FIELD_CANDIDATES if field in reader.fieldnames), None)
        if not gt_field:
            raise ValueError(
                f"Ground truth CSV icinde beklenen kolonlardan biri yok: {', '.join(GT_FIELD_CANDIDATES)}"
            )

        for row in reader:
            expected = normalize_plate(row.get(gt_field))
            if not expected:
                continue

            alarm_id = normalize_plate(row.get("alarm_id"))
            plate_path = (row.get("plate_screenshot") or "").strip()
            basename = Path(plate_path).name if plate_path else ""

            if alarm_id:
                mapping[f"alarm:{alarm_id}"] = expected
            if plate_path:
                mapping[f"path:{plate_path}"] = expected
            if basename:
                mapping[f"base:{basename}"] = expected

    return mapping


def find_expected_plate(sample: AlarmSample, gt_mapping: dict[str, str]) -> str | None:
    keys = [
        f"alarm:{normalize_plate(sample.alarm_id)}",
        f"path:{sample.plate_screenshot_abs or ''}",
        f"base:{Path(sample.plate_screenshot_abs).name if sample.plate_screenshot_abs else ''}",
    ]
    for key in keys:
        if key in gt_mapping:
            return gt_mapping[key]
    return None


def evaluate(samples: list[AlarmSample], gt_mapping: dict[str, str]) -> dict:
    matched = []
    missing_ground_truth = 0

    for sample in samples:
        expected = find_expected_plate(sample, gt_mapping)
        if not expected:
            missing_ground_truth += 1
            continue
        predicted = normalize_plate(sample.predicted_plate)
        exact = predicted == expected
        char_acc = char_accuracy(expected, predicted)
        matched.append(
            {
                "alarm_id": sample.alarm_id,
                "created_at": sample.created_at,
                "expected_plate": expected,
                "predicted_plate": predicted,
                "predicted_conf": round(sample.predicted_conf, 4),
                "exact_match": exact,
                "char_accuracy": round(char_acc, 4),
                "plate_screenshot": sample.plate_screenshot_abs,
                "screenshot": sample.screenshot_abs,
            }
        )

    exact_matches = sum(1 for item in matched if item["exact_match"])
    char_acc_values = [item["char_accuracy"] for item in matched]

    correct_conf = [item["predicted_conf"] for item in matched if item["exact_match"]]
    wrong_conf = [item["predicted_conf"] for item in matched if not item["exact_match"]]

    confusion_counter: Counter[str] = Counter()
    position_confusion: dict[int, Counter[str]] = defaultdict(Counter)
    mismatches = []

    for item in matched:
        expected = item["expected_plate"]
        predicted = item["predicted_plate"]
        if expected == predicted:
            continue
        mismatches.append(item)
        max_len = max(len(expected), len(predicted))
        for idx in range(max_len):
            exp_ch = expected[idx] if idx < len(expected) else "-"
            pred_ch = predicted[idx] if idx < len(predicted) else "-"
            if exp_ch != pred_ch:
                pair = f"{exp_ch}->{pred_ch}"
                confusion_counter[pair] += 1
                position_confusion[idx][pair] += 1

    report = {
        "summary": {
            "total_samples_loaded": len(samples),
            "matched_samples": len(matched),
            "missing_ground_truth": missing_ground_truth,
            "exact_accuracy": round((exact_matches / len(matched)) if matched else 0.0, 4),
            "char_accuracy": round((sum(char_acc_values) / len(char_acc_values)) if char_acc_values else 0.0, 4),
            "avg_conf_correct": round((sum(correct_conf) / len(correct_conf)) if correct_conf else 0.0, 4),
            "avg_conf_wrong": round((sum(wrong_conf) / len(wrong_conf)) if wrong_conf else 0.0, 4),
        },
        "top_confusions": [
            {"pair": pair, "count": count}
            for pair, count in confusion_counter.most_common(12)
        ],
        "position_confusions": {
            str(idx): [{"pair": pair, "count": count} for pair, count in counter.most_common(6)]
            for idx, counter in sorted(position_confusion.items())
        },
        "mismatches": mismatches[:50],
    }
    return report


def write_json_report(report: dict, output_json: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_report(report: dict, output_md: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    summary = report["summary"]
    lines = [
        "# Plate OCR Evaluation",
        "",
        f"- matched_samples: `{summary['matched_samples']}`",
        f"- exact_accuracy: `{summary['exact_accuracy']:.2%}`",
        f"- char_accuracy: `{summary['char_accuracy']:.2%}`",
        f"- avg_conf_correct: `{summary['avg_conf_correct']:.3f}`",
        f"- avg_conf_wrong: `{summary['avg_conf_wrong']:.3f}`",
        "",
        "## Top Confusions",
    ]

    if report["top_confusions"]:
        for item in report["top_confusions"]:
            lines.append(f"- `{item['pair']}` x `{item['count']}`")
    else:
        lines.append("- mismatch yok")

    lines.extend(["", "## Mismatches"])
    if report["mismatches"]:
        for item in report["mismatches"][:20]:
            lines.append(
                f"- `{item['alarm_id']}` expected=`{item['expected_plate']}` "
                f"predicted=`{item['predicted_plate']}` conf=`{item['predicted_conf']:.3f}` "
                f"char_acc=`{item['char_accuracy']:.2%}`"
            )
    else:
        lines.append("- mismatch yok")

    output_md.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plate OCR accuracy evaluator")
    parser.add_argument("--limit", type=int, default=200, help="DB'den alinacak son alarm sayisi")
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=None,
        help="expected_plate kolonu olan CSV dosyasi",
    )
    parser.add_argument(
        "--export-template",
        type=Path,
        default=REPO_ROOT / "backend" / "artifacts" / "ocr_eval" / "ground_truth_template.csv",
        help="label icin template CSV cikti yolu",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=REPO_ROOT / "backend" / "artifacts" / "ocr_eval" / "report.json",
        help="JSON rapor cikti yolu",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=REPO_ROOT / "backend" / "artifacts" / "ocr_eval" / "report.md",
        help="Markdown rapor cikti yolu",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    samples = load_alarm_samples(args.limit)

    if not samples:
        print("Alarm DB icinde plate_screenshot bulunan sample yok.")
        return 1

    export_template(samples, args.export_template)
    print(f"Template export edildi: {args.export_template}")
    print(f"Sample sayisi: {len(samples)}")

    if not args.ground_truth:
        print("Ground truth verilmedi. CSV icinde expected_plate kolonunu doldurup yeniden calistir.")
        return 0

    gt_mapping = read_ground_truth(args.ground_truth)
    report = evaluate(samples, gt_mapping)
    write_json_report(report, args.report_json)
    write_markdown_report(report, args.report_md)

    summary = report["summary"]
    print("Evaluation tamamlandi:")
    print(f"  matched_samples: {summary['matched_samples']}")
    print(f"  exact_accuracy:  {summary['exact_accuracy']:.2%}")
    print(f"  char_accuracy:   {summary['char_accuracy']:.2%}")
    print(f"  avg_conf_correct:{summary['avg_conf_correct']:.3f}")
    print(f"  avg_conf_wrong:  {summary['avg_conf_wrong']:.3f}")
    print(f"  json_report:     {args.report_json}")
    print(f"  md_report:       {args.report_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
