from pathlib import Path

import pandas as pd
from pandas import DataFrame

FIRST_FILE = Path(__file__).parent.parent.resolve() / "data" / "temp_data.xlsx"
SECOND_FILE = Path(__file__).parent.parent.resolve() / "data" / "temp_data_2.xlsx"
MERGE_FILE = Path(__file__).parent.parent.resolve() / "data" / "temp_data_merge.xlsx"

MERGE_COLUMNS = [
    "Automatable with current Orbital V2 Features (July 2025)",
    "To Automate",
    "Remarks",
    "Remarks 2",
    "Questions",
]


def merge_df(df_1: DataFrame, df_2: DataFrame) -> None:
    df_1 = df_1.fillna("").astype(str)
    df_2 = df_2.fillna("").astype(str)
    df_1_id = df_1["ID"].tolist()
    for id in range(len(df_1_id)):
        df_2.loc[df_2["ID"] == df_1_id[id], MERGE_COLUMNS] = df_1.loc[
            df_1["ID"] == df_1_id[id], MERGE_COLUMNS
        ]
    df_2.to_excel(MERGE_FILE, index=False)


def main():
    merge_df(pd.read_excel(FIRST_FILE), pd.read_excel(SECOND_FILE))


if __name__ == "__main__":
    main()
