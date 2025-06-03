import pandas as pd
import StringIO


def describe(df: pd.DataFrame):
    """
    Takes a pandas dataframe as input
    Returns a description of the dataset.

    input: pd.DataFrame
    output: dict
    """
    if df is None:
        return "No dataset uploaded."
    return df.describe().to_dict()


def missing_values(df: pd.DataFrame):
    """
    Returns missing value counts

    input: pd.DataFrame
    output: dict
    """
    if df is None:
        return "No dataset uploaded."
    return df.isnull().sum().to_dict()


def get_info(df: pd.DataFrame):
    """
    Returns info about the dataset

    input: pd.DataFrame
    output: dict
    """
    if df is None:
        return "No dataset uploaded."
    buf = StringIO()
    df.info(buf=buf)
    return buf.getvalue()
