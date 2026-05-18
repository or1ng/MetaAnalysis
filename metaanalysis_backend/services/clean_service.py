"""
数据清洗引擎
支持：缺失值处理、异常值检测/处理、去重、格式标准化、质量评分、快照回滚
"""

import os
import shutil
import copy
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional


# ── 质量评分 ──────────────────────────────────────────────

def quality_score(df: pd.DataFrame) -> dict:
    """
    计算数据质量评分（0-100）
    检查维度：缺失率、异常值、重复行、格式一致性
    """
    total_rows = len(df)
    total_cells = total_rows * len(df.columns)
    if total_cells == 0:
        return {"score": 100, "total_rows": 0, "total_cols": 0,
                "missing_cells": 0, "outlier_count": 0, "dup_rows": 0, "format_issues": 0}

    # 1. 缺失值
    missing_cells = int(df.isna().sum().sum())
    missing_rate = missing_cells / total_cells

    # 2. 异常值检测（数值列用IQR）
    outlier_count = 0
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        Q1 = s.quantile(0.25)
        Q3 = s.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outlier_count += int(((s < lower) | (s > upper)).sum())

    # 3. 重复行
    dup_rows = int(df.duplicated().sum())

    # 4. 格式问题（文本列中含特殊字符/空白字符串）
    format_issues = 0
    for col in df.select_dtypes(include=['object']).columns:
        # 空白字符串
        blank_count = int((df[col].str.strip() == '').sum()) if df[col].dtype == 'object' else 0
        format_issues += blank_count

    # 评分算法
    score = 100
    score -= min(30, missing_rate * 100)  # 缺失率最多扣30分
    dup_rate = dup_rows / total_rows if total_rows > 0 else 0
    score -= min(20, dup_rate * 200)  # 重复率最多扣20分
    outlier_rate = outlier_count / total_cells if total_cells > 0 else 0
    score -= min(25, outlier_rate * 300)  # 异常率最多扣25分
    format_rate = format_issues / total_cells if total_cells > 0 else 0
    score -= min(25, format_rate * 500)  # 格式问题最多扣25分

    score = max(0, min(100, int(score)))

    return {
        "score": score,
        "total_rows": total_rows,
        "total_cols": len(df.columns),
        "missing_cells": missing_cells,
        "outlier_count": outlier_count,
        "dup_rows": dup_rows,
        "format_issues": format_issues,
    }


# ── 缺失值处理 ────────────────────────────────────────────

def fill_missing(df: pd.DataFrame, strategy: str = "mean", custom_value=None) -> tuple:
    """
    处理缺失值
    strategy: mean / median / mode / drop / constant
    返回 (处理后的df, affected_rows, summary)
    """
    df_clean = df.copy()
    affected = 0
    details = []

    for col in df_clean.columns:
        missing_mask = df_clean[col].isna()
        missing_count = int(missing_mask.sum())
        if missing_count == 0:
            continue

        if strategy == "drop":
            pass  # 最后统一drop
        elif strategy == "constant" and custom_value is not None:
            df_clean.loc[missing_mask, col] = custom_value
            affected += missing_count
            details.append(f"{col}: 填充常量 {custom_value} ({missing_count}处)")
        elif pd.api.types.is_numeric_dtype(df_clean[col]):
            if strategy == "mean":
                fill_val = df_clean[col].mean()
            elif strategy == "median":
                fill_val = df_clean[col].median()
            elif strategy == "mode":
                mode_vals = df_clean[col].mode()
                fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else 0
            else:
                fill_val = 0

            if pd.notna(fill_val):
                fill_val = float(fill_val)
                df_clean.loc[missing_mask, col] = fill_val
                affected += missing_count
                details.append(f"{col}: {strategy}填充 {fill_val:.2f} ({missing_count}处)")
        else:
            # 文本列用mode或"未知"
            if strategy == "mode":
                mode_vals = df_clean[col].mode()
                fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else "未知"
            else:
                fill_val = "未知"
            df_clean.loc[missing_mask, col] = fill_val
            affected += missing_count
            details.append(f"{col}: 填充'{fill_val}' ({missing_count}处)")

    if strategy == "drop":
        before = len(df_clean)
        df_clean = df_clean.dropna()
        affected = before - len(df_clean)
        details.append(f"删除含缺失行: {affected}行")

    return df_clean, affected, "; ".join(details)


# ── 异常值处理 ────────────────────────────────────────────

def detect_outliers(df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5) -> dict:
    """
    检测异常值
    method: iqr / zscore
    返回 {col_name: {"count": int, "lower": float, "upper": float, "indices": [int]}}
    """
    result = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) < 4:
            continue

        if method == "iqr":
            Q1 = s.quantile(0.25)
            Q3 = s.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR
        elif method == "zscore":
            mean = s.mean()
            std = s.std()
            if std == 0:
                continue
            lower = mean - threshold * std
            upper = mean + threshold * std
        else:
            continue

        mask = (s < lower) | (s > upper)
        outlier_indices = s[mask].index.tolist()
        if len(outlier_indices) > 0:
            result[col] = {
                "count": len(outlier_indices),
                "lower": float(lower),
                "upper": float(upper),
                "indices": outlier_indices[:50],  # 最多返回50个
            }

    return result


def handle_outliers(df: pd.DataFrame, method: str = "iqr", handle: str = "clip",
                    threshold: float = 1.5) -> tuple:
    """
    处理异常值
    method: iqr / zscore
    handle: clip / mean / drop
    threshold: IQR倍数或Z-Score倍数
    返回 (df, affected, summary)
    """
    df_clean = df.copy()
    total_affected = 0
    details = []

    outliers = detect_outliers(df, method=method, threshold=threshold)

    for col, info in outliers.items():
        count = info["count"]
        lower, upper = info["lower"], info["upper"]
        s = df_clean[col]
        mask = (s < lower) | (s > upper)

        if handle == "clip":
            df_clean[col] = s.clip(lower=lower, upper=upper)
            details.append(f"{col}: 截断至[{lower:.1f}, {upper:.1f}] ({count}处)")
        elif handle == "mean":
            mean_val = s.mean()
            df_clean.loc[mask, col] = mean_val
            details.append(f"{col}: 替换为均值{mean_val:.2f} ({count}处)")
        elif handle == "drop":
            df_clean = df_clean[~mask]
            details.append(f"{col}: 删除异常行 ({count}行)")

        total_affected += count

    return df_clean, total_affected, "; ".join(details) if details else "未检测到异常值"


# ── 去重 ──────────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame, subset: list = None, keep: str = "first") -> tuple:
    """
    去重
    subset: 指定列去重，None则全部列
    keep: first / last / False(删除所有重复)
    返回 (df, affected, summary)
    """
    before = len(df)
    if subset:
        df_clean = df.drop_duplicates(subset=subset, keep=keep)
        label = f"按 {','.join(subset)} 去重"
    else:
        df_clean = df.drop_duplicates(keep=keep)
        label = "完全去重"

    affected = before - len(df_clean)
    summary = f"{label}: 删除{affected}行" if affected > 0 else "无重复行"

    return df_clean, affected, summary


# ── 格式标准化 ────────────────────────────────────────────

def normalize_format(df: pd.DataFrame, strip_whitespace: bool = True,
                     date_unify: bool = True, case_lower: bool = False) -> tuple:
    """
    格式标准化
    - 去除首尾空白
    - 日期格式统一
    - 文本大小写
    返回 (df, affected, summary)
    """
    df_clean = df.copy()
    affected = 0
    details = []

    for col in df_clean.columns:
        # 去空白
        if strip_whitespace and df_clean[col].dtype == 'object':
            before = df_clean[col].copy()
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # 还原NaN（strip会变成字符串"nan"）
            df_clean[col] = df_clean[col].replace('nan', np.nan).replace('None', np.nan)
            changed = int((before != df_clean[col]).sum())
            if changed > 0:
                affected += changed
                details.append(f"{col}: 去除首尾空白 ({changed}处)")

        # 日期统一
        if date_unify and df_clean[col].dtype == 'object':
            try:
                parsed = pd.to_datetime(df_clean[col], errors='coerce')
                if parsed.notna().sum() > len(df_clean) * 0.5:
                    df_clean[col] = parsed
                    changed = int(parsed.notna().sum())
                    affected += changed
                    details.append(f"{col}: 日期格式统一 ({changed}处)")
            except Exception:
                pass

        # 大小写
        if case_lower and df_clean[col].dtype == 'object':
            before = df_clean[col].copy()
            df_clean[col] = df_clean[col].astype(str).str.lower()
            df_clean[col] = df_clean[col].replace('nan', np.nan).replace('none', np.nan)
            changed = int((before.astype(str) != df_clean[col].astype(str)).sum())
            if changed > 0:
                affected += changed
                details.append(f"{col}: 转为小写 ({changed}处)")

    return df_clean, affected, "; ".join(details) if details else "无需标准化"


# ── 一键智能清洗 ──────────────────────────────────────────

def auto_clean(df: pd.DataFrame) -> tuple:
    """
    一键智能清洗：自动检测并处理所有数据质量问题
    流程：格式标准化 → 去重 → 缺失值填充 → 异常值截断
    返回 (cleaned_df, logs)
    """
    logs = []
    current_df = df.copy()

    # Step 1: 格式标准化
    current_df, aff, summary = normalize_format(current_df, strip_whitespace=True, date_unify=True)
    if aff > 0:
        logs.append({"action": "格式标准化", "affected": aff, "summary": summary})

    # Step 2: 去重
    current_df, aff, summary = remove_duplicates(current_df)
    if aff > 0:
        logs.append({"action": "去重", "affected": aff, "summary": summary})

    # Step 3: 缺失值填充
    current_df, aff, summary = fill_missing(current_df, strategy="mean")
    if aff > 0:
        logs.append({"action": "缺失值填充", "affected": aff, "summary": summary})

    # Step 4: 异常值处理（IQR截断）
    current_df, aff, summary = handle_outliers(current_df, method="iqr", handle="clip")
    if aff > 0:
        logs.append({"action": "异常值截断", "affected": aff, "summary": summary})

    return current_df, logs


# ── 快照管理 ──────────────────────────────────────────────

def save_snapshot(df: pd.DataFrame, snapshot_dir: str, dataset_id: int, version: int) -> str:
    """保存数据快照为CSV"""
    os.makedirs(snapshot_dir, exist_ok=True)
    filename = f"dataset_{dataset_id}_v{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(snapshot_dir, filename)
    df.to_csv(filepath, index=False, encoding='utf-8')
    return filepath


def load_snapshot(filepath: str) -> pd.DataFrame:
    """从快照加载数据"""
    return pd.read_csv(filepath)
