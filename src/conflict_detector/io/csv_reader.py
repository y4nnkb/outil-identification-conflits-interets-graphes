from pathlib import Path

import pandas as pd


def read_input_tables(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    path = Path(data_dir)
    return {file.stem: pd.read_csv(file) for file in path.glob("*.csv")}
