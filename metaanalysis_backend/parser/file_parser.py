"""
文件解析引擎 - 支持Excel(.xlsx/.xls)、CSV、TXT格式
负责文件解析、元数据提取、数据预览
"""

import os
import io
import pandas as pd
import numpy as np
from typing import Optional


# pandas dtype -> 前端友好类型映射
DTYPE_MAP = {
    "int64": "integer",
    "int32": "integer",
    "int16": "integer",
    "int8": "integer",
    "uint64": "integer",
    "uint32": "integer",
    "uint16": "integer",
    "uint8": "integer",
    "float64": "float",
    "float32": "float",
    "object": "string",
    "bool": "boolean",
    "datetime64[ns]": "datetime",
    "datetime64[ns, tz]": "datetime",
    "timedelta64[ns]": "duration",
    "category": "category",
}


def read_file(file_path: str, file_type: str = None) -> pd.DataFrame:
    """
    根据文件类型读取文件为DataFrame
    
    Args:
        file_path: 文件路径
        file_type: 文件类型（xlsx/csv/txt），None则根据扩展名推断
    
    Returns:
        pandas DataFrame
    """
    if file_type is None:
        ext = os.path.splitext(file_path)[1].lower()
        file_type = {"xlsx": "xlsx", ".xls": "xlsx"}.get(ext, ext.lstrip("."))

    if file_type == "xlsx":
        return pd.read_excel(file_path, engine="openpyxl")
    elif file_type in ("csv", "txt"):
        # 自动检测编码和分隔符
        try:
            # 先尝试utf-8
            return _read_csv_smart(file_path)
        except UnicodeDecodeError:
            # 回退到gbk
            return _read_csv_smart(file_path, encoding="gbk")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def read_file_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """
    从字节数组读取文件为DataFrame（用于上传时直接解析）
    
    Args:
        content: 文件二进制内容
        filename: 文件名（用于推断类型）
    
    Returns:
        pandas DataFrame
    """
    ext = os.path.splitext(filename)[1].lower()
    file_type = {".xlsx": "xlsx", ".xls": "xlsx"}.get(ext, ext.lstrip("."))

    if file_type == "xlsx":
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    elif file_type in ("csv", "txt"):
        # 尝试多种编码
        for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
            try:
                return _read_csv_smart_from_bytes(content, encoding=enc)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        raise ValueError(f"Cannot decode file: {filename}")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _read_csv_smart(file_path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """智能读取CSV：自动检测分隔符"""
    with open(file_path, "r", encoding=encoding) as f:
        sample = f.read(4096)

    sep = _detect_separator(sample)
    return pd.read_csv(file_path, sep=sep, encoding=encoding)


def _read_csv_smart_from_bytes(content: bytes, encoding: str = "utf-8") -> pd.DataFrame:
    """智能读取CSV（从字节）：自动检测分隔符"""
    sample = content[:4096].decode(encoding)
    sep = _detect_separator(sample)
    return pd.read_csv(io.BytesIO(content), sep=sep, encoding=encoding)


def _detect_separator(sample: str) -> str:
    """检测CSV分隔符"""
    first_line = sample.split("\n")[0]
    for sep in [",", "\t", ";", "|"]:
        if sep in first_line and first_line.count(sep) >= 1:
            return sep
    return ","


def extract_metadata(df: pd.DataFrame) -> dict:
    """
    从DataFrame提取元数据
    
    Returns:
        {
            "row_count": int,
            "col_count": int,
            "columns": [{"name": str, "type": str, "missing_count": int, "missing_rate": float, "unique_count": int}]
        }
    """
    total_rows = len(df)
    columns_meta = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_rate = round(missing_count / total_rows, 4) if total_rows > 0 else 0.0
        dtype_str = str(series.dtype)
        col_type = DTYPE_MAP.get(dtype_str, "string")

        # 统计唯一值数量（采样以提高性能）
        try:
            unique_count = int(series.nunique())
        except (TypeError, ValueError):
            unique_count = -1

        # 确保缺失率不是NaN
        missing_rate = round(missing_count / total_rows, 4) if total_rows > 0 else 0.0
        if missing_rate != missing_rate:  # NaN check
            missing_rate = 0.0

        columns_meta.append({
            "name": str(col),
            "type": col_type,
            "missing_count": missing_count,
            "missing_rate": missing_rate,
            "unique_count": unique_count,
        })

    return {
        "row_count": total_rows,
        "col_count": len(df.columns),
        "columns": columns_meta,
    }


def get_preview(df: pd.DataFrame, rows: int = 20) -> list:
    """
    获取数据预览（前N行），返回可JSON序列化的列表
    
    Args:
        df: DataFrame
        rows: 预览行数
    
    Returns:
        [{"column1": value, "column2": value, ...}, ...]
    """
    preview_df = df.head(rows).copy()

    # 将不可序列化的值转换为字符串
    for col in preview_df.columns:
        # 处理NaN/NaT
        preview_df[col] = preview_df[col].apply(
            lambda x: None if pd.isna(x) else x
        )
        # 处理numpy类型
        preview_df[col] = preview_df[col].apply(_convert_value)

    # 转为records
    return preview_df.to_dict(orient="records")


def _convert_value(val):
    """将numpy类型转换为Python原生类型"""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        # Handle NaN
        if np.isnan(val):
            return None
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    return val


def _safe_float(val):
    """将值安全转换为float，NaN转None"""
    if val is None:
        return None
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def get_basic_stats(df: pd.DataFrame) -> dict:
    """
    获取基础统计摘要
    
    Returns:
        {
            "numeric_cols": [{"name": str, "mean": float, "std": float, "min": float, "max": float, ...}],
            "categorical_cols": [{"name": str, "top": str, "top_count": int}]
        }
    """
    numeric_stats = []
    categorical_stats = []

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)

        if DTYPE_MAP.get(dtype_str) in ("integer", "float"):
            desc = series.describe()
            numeric_stats.append({
                "name": str(col),
                "mean": _safe_float(desc.get("mean")),
                "std": _safe_float(desc.get("std")),
                "min": _safe_float(desc.get("min")),
                "max": _safe_float(desc.get("max")),
                "q25": _safe_float(desc.get("25%")),
                "q50": _safe_float(desc.get("50%")),
                "q75": _safe_float(desc.get("75%")),
            })
        elif DTYPE_MAP.get(dtype_str) == "string":
            try:
                desc = series.describe()
                categorical_stats.append({
                    "name": str(col),
                    "unique": int(desc.get("unique", 0)),
                    "top": str(desc.get("top", "")),
                    "top_count": int(desc.get("freq", 0)),
                })
            except (TypeError, ValueError):
                pass

    return {
        "numeric_cols": numeric_stats,
        "categorical_cols": categorical_stats,
    }
