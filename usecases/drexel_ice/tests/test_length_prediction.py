import os
import pytest
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../usecases/length_prediction')))

from main import run

def test_length_prediction_golden():
    run()
    df_actual = pd.read_csv("usecases/drexel_ice/usecases/length_prediction/results/results.csv")
    df_expected = pd.read_csv("usecases/drexel_ice/usecases/length_prediction/results/results.csv.golden")
    pd.testing.assert_frame_equal(df_actual, df_expected)
