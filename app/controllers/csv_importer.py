import pandas as pd

class CSVImporter:
    @staticmethod
    def preview_csv(file_path, sep=";", decimal=".", nrows=8):
        try:
            df = pd.read_csv(file_path, sep=sep, decimal=decimal, nrows=nrows)
            cols = list(df.columns)
            return True, df, cols
        except Exception as e:
            return False, str(e), []

    @staticmethod
    def load_csv(file_path, x_col, y_col, sep=";", decimal="."):
        try:
            df = pd.read_csv(file_path, sep=sep, decimal=decimal)
            if x_col not in df.columns or y_col not in df.columns:
                return False, f"Colonnes {x_col} ou {y_col} non trouvées.", None

            df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
            df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
            df = df.dropna(subset=[x_col, y_col])

            return True, "Succès", df[[x_col, y_col]]
        except Exception as e:
            return False, f"Erreur de chargement: {str(e)}", None
