import subprocess
import sys
from pathlib import Path


def test_preroute_delay_predictor_log_matches_golden():
    """Ensure preroute_delay_prediction.py emits the expected log output."""
    script_dir = Path(__file__).resolve().parent.parent / "usecases" / "preroute_delay_prediction"
    script_path = script_dir / "preroute_delay_prediction.py"
    log_path = script_dir / "preroute_delay_prediction.log"
    log_ok_path = script_dir / "preroute_delay_prediction.log.ok"
    features_path = script_dir / "preroute_delay_predictor_features.csv"
    plot_path = script_dir / "preroute_delay_prediction_plot.png"

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
        print(f"preroute_delay_prediction.py stderr:\n{completed.stderr}")

    actual_log = log_path.read_text()
    expected_log = log_ok_path.read_text()
    assert actual_log == expected_log, "preroute_delay_prediction.py output diverged from preroute_delay_prediction.log.ok"

    for artifact in (log_path, features_path, plot_path):
        if artifact.exists():
            artifact.unlink()
