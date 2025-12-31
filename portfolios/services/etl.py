import pandas as pd
from decimal import Decimal
from portfolios.models import Asset, Price


def load_prices_from_excel(path: str):
    """
    Lee el sheet 'Precios' del Excel y carga Assets y Prices.
    """
    df = pd.read_excel(path, sheet_name="Precios")

    date_column = df.columns[0]
    asset_columns = df.columns[1:]

    assets = {}
    for col in asset_columns:
        asset, _ = Asset.objects.get_or_create(name=col)
        assets[col] = asset

    prices_created = 0

    for _, row in df.iterrows():
        date = row[date_column]

        for col in asset_columns:
            value = row[col]

            if pd.isna(value):
                continue

            Price.objects.update_or_create(
                asset=assets[col],
                date=date,
                defaults={"price": Decimal(value)},
            )
            prices_created += 1

    return prices_created


def _df_from_admin_html(path: str):
    """Parse a saved Django admin HTML page listing Prices into a DataFrame.
    Expects a table with columns like id, asset, date, price.
    Returns a DataFrame with columns (asset, date, price) or None if not found.
    """
    try:
        tables = pd.read_html(path)
    except Exception:
        return None

    def _normalize_columns(df):
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df

    for t in tables:
        df = _normalize_columns(t)
        cols = set(df.columns)
        if {"asset", "date", "price"}.issubset(cols):
            return df[["asset", "date", "price"]]
    return None


def load_prices_from_csv(paths):
    """
    Carga precios desde uno o varios archivos CSV.

    Formatos soportados:
    - Wide: primera columna es la fecha; columnas siguientes son nombres de activos con su precio.
    - Long: columnas con nombres (asset|ticker), (date), (price).

    paths: ruta (str) o lista de rutas.
    """
    if isinstance(paths, str):
        paths = [paths]

    prices_created = 0

    for path in paths:
        # Detect if the file is actually an HTML saved page from admin
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(512)
        except Exception:
            head = ""

        if "<html" in head.lower() or "<!doctype" in head.lower():
            df = _df_from_admin_html(path)
            if df is None:
                # Fallback: try CSV load anyway
                df = pd.read_csv(path)
        else:
            df = pd.read_csv(path)

        # Normalizar encabezados
        cols_lower = [str(c).strip().lower() for c in df.columns]

        # Detectar formato long
        has_asset = any(c in cols_lower for c in ["asset", "ticker", "symbol", "asset_name"])
        has_date = any(c in cols_lower for c in ["date", "fecha"])
        has_price = "price" in cols_lower or "valor" in cols_lower or "precio" in cols_lower

        if has_asset and has_date and has_price:
            # Long format
            # Mapear nombres reales
            def colidx(name_opts):
                for i, c in enumerate(cols_lower):
                    if c in name_opts:
                        return i
                return None

            i_asset = colidx({"asset", "ticker", "symbol", "asset_name"})
            i_date = colidx({"date", "fecha"})
            i_price = colidx({"price", "valor", "precio"})

            for _, row in df.iterrows():
                asset_name = str(row.iloc[i_asset]).strip()
                if not asset_name:
                    continue
                date_val = pd.to_datetime(row.iloc[i_date], errors="coerce").date()
                price_val = row.iloc[i_price]
                if pd.isna(price_val):
                    continue

                asset, _ = Asset.objects.get_or_create(name=asset_name)
                Price.objects.update_or_create(
                    asset=asset,
                    date=date_val,
                    defaults={"price": Decimal(str(price_val))},
                )
                prices_created += 1
        else:
            # Wide format
            date_column = df.columns[0]
            asset_columns = df.columns[1:]

            assets = {}
            for col in asset_columns:
                asset, _ = Asset.objects.get_or_create(name=str(col).strip())
                assets[col] = asset

            for _, row in df.iterrows():
                date = pd.to_datetime(row[date_column], errors="coerce").date()
                for col in asset_columns:
                    value = row[col]
                    if pd.isna(value):
                        continue
                    Price.objects.update_or_create(
                        asset=assets[col],
                        date=date,
                        defaults={"price": Decimal(str(value))},
                    )
                    prices_created += 1

    return prices_created
