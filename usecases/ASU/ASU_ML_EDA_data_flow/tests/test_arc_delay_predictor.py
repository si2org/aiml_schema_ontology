import re
import subprocess
import sys
from pathlib import Path

METRIC_TOLERANCE = 0.000001  # acceptable absolute difference for percentage metrics


def _extract_metric(log_text, label):
    """Extract a floating point metric from the log output."""
    pattern = rf"{re.escape(label)}\s*:\s*([-\d\.]+)"
    match = re.search(pattern, log_text)
    if not match:
        raise AssertionError(f"Metric '{label}' not found in log output")
    return float(match.group(1))


def test_arc_delay_predictor_log_matches_golden():
    """Run the arc delay predictor and compare its log to the checked-in golden copy."""
    script_dir = Path(__file__).resolve().parent.parent / "usecases" / "arc_delay_predictor"
    script_path = script_dir / "arc_delay_prediction.py"
    log_path = script_dir / "arc_delay_prediction.log"
    log_ok_path = script_dir / "arc_delay_prediction.log.ok"
    dataframe_path = script_dir / "arc_delay_predictor_dataframe.csv"
    dataframe_ok_path = script_dir / "arc_delay_predictor_dataframe.csv.ok"
    mlcard_path = script_dir / "mlcard_properties.csv"
    mlcard_ok_path = script_dir / "mlcard_properties.csv.ok"

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    log_path.write_text(completed.stdout)

    if completed.stderr:
        # Surface warnings in the failure message while still allowing the comparison check below.
        print(f"arc_delay_prediction.py stderr:\n{completed.stderr}")

    log_expected = log_ok_path.read_text()
    log_actual = log_path.read_text()

    for metric_label in ("Maximum Error %", "Mean Error %"):
        actual_value = _extract_metric(log_actual, metric_label)
        expected_value = _extract_metric(log_expected, metric_label)
        diff = abs(actual_value - expected_value)
        assert (
            diff <= METRIC_TOLERANCE
        ), f"{metric_label} differed by {diff}, exceeding tolerance {METRIC_TOLERANCE}"

    dataframe_expected = dataframe_ok_path.read_text()
    dataframe_actual = dataframe_path.read_text()
    assert (
        dataframe_actual == dataframe_expected
    ), "arc_delay_predictor_dataframe.csv output diverged from arc_delay_predictor_dataframe.csv.ok"

    mlcard_expected = mlcard_ok_path.read_text()
    mlcard_actual = mlcard_path.read_text()
    assert (
        mlcard_actual == mlcard_expected
    ), "mlcard_properties.csv output diverged from mlcard_properties.csv.ok"
    if log_path.exists():
        log_path.unlink()
    if dataframe_path.exists():
        dataframe_path.unlink()
    if mlcard_path.exists():
        mlcard_path.unlink()
