import os
import pytest
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../usecases/timing_prediction')))

from main import run

def test_arrival_time_prediction_golden():
    run("arrivalTime")
    df_actual = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/requiredTime.csv")
    df_expected = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/requiredTime.csv.golden")
    pd.testing.assert_frame_equal(df_actual, df_expected)

def test_required_time_prediction_golden():
    run("requiredTime")
    df_actual = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/requiredTime.csv")
    df_expected = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/requiredTime.csv.golden")
    pd.testing.assert_frame_equal(df_actual, df_expected)

def test_slack_prediction_golden():
    run("slack")
    df_actual = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/slack.csv")
    df_expected = pd.read_csv("usecases/drexel_ice/usecases/timing_prediction/results/slack.csv.golden")
    pd.testing.assert_frame_equal(df_actual, df_expected)
