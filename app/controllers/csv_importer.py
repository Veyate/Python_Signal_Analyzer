"""
Contrôleur d'importation CSV.
"""
import pandas as pd
import numpy as np

class CSVImporter:
    @staticmethod
    def preview_csv(file_path, sep=";", decimal=".", nrows=10):
        try:
            if isinstance(file_path, (tuple, list)):
                file_path = file_path[0]
            df = pd.read_csv(file_path, sep=sep, decimal=decimal, nrows=nrows, engine="python")
            return True, df, list(df.columns)
        except Exception as e:
            return False, str(e), []

    @staticmethod
    def load_csv(file_path, x_col, y_col, sep=";", decimal="."):
        try:
            if isinstance(file_path, (tuple, list)):
                file_path = file_path[0]
            df = pd.read_csv(file_path, sep=sep, decimal=decimal, engine="python")
            if x_col not in df.columns or y_col not in df.columns:
                return False, "Colonnes introuvables", None
            df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
            df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
            df_clean = df.dropna(subset=[x_col, y_col]).reset_index(drop=True)
            return True, "Import réussi", df_clean
        except Exception as e:
            return False, str(e), None
