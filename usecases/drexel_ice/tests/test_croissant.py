import os
import pytest
import pandas as pd
from mlcroissant import Dataset

# Path to your metadata file
METADATA_PATH = "combined_croissant_metadata.json"

def load_data(record_set_name: str) -> pd.DataFrame:
    dataset = Dataset(METADATA_PATH)
    return pd.DataFrame(dataset.records(record_set_name))

@pytest.mark.parametrize("record_set_name", [
    "wire_records",
    "area_analysis_records",
    "pin_records",
    "instance_records",
    "netlist_records",
    "clock_tree_records",
    "stage_records",
    "timing_analysis_records",
    "timing_path_records",
    "net_records",
    "standard_cell_records",
    "timing_path_pin_records",
    "port_records",
    "power_analysis_records",
    "netlist_graph_records",
    "clock_tree_graph_records",
    "net_graph_records",
    "timing_graph_graph_records",
    "timing_path_graph_records",
])
def test_record_set_loads(record_set_name):
    df = load_data(record_set_name)
    assert not df.empty, f"{record_set_name} is empty"
    assert isinstance(df, pd.DataFrame), f"{record_set_name} did not return a DataFrame"
