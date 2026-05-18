"""
统计分析API
6大模块：描述统计、假设检验、相关分析、回归分析、时序分析、聚类分析
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional

from models import get_db
from models.dataset import Dataset
from services.statistic_service import StatisticEngine
from parser.file_parser import read_file
from utils.response import ApiResponse

router = APIRouter(prefix="/api/statistic", tags=["统计分析"])


def _safe_serialize(data):
    """递归清理numpy类型，确保JSON可序列化"""
    import numpy as np
    if isinstance(data, dict):
        return {str(k): _safe_serialize(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_safe_serialize(v) for v in data]
    if isinstance(data, (np.bool_,)):
        return bool(data)
    if isinstance(data, (np.integer,)):
        return int(data)
    if isinstance(data, (np.floating,)):
        import math
        v = float(data)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(data, np.ndarray):
        return data.tolist()
    return data


# ── Schema ──────────────────────────────────────────────

class StatBase(BaseModel):
    dataset_id: int = Field(..., description="数据集ID")
    columns: Optional[list[str]] = Field(None, description="分析字段列表，None=全部数值列")


class DescriptiveReq(StatBase):
    confidence: float = Field(0.95, description="置信水平")


class HypothesisReq(StatBase):
    method: str = Field("ttest_independent", description="检验方法")
    alpha: float = Field(0.05, description="显著性水平")
    group_col: Optional[str] = None
    value_col: Optional[str] = None
    group_a: Optional[str] = None
    group_b: Optional[str] = None
    col_a: Optional[str] = None
    col_b: Optional[str] = None


class CorrelationReq(StatBase):
    method: str = Field("pearson", description="相关系数类型: pearson/spearman/kendall")


class RegressionReq(BaseModel):
    dataset_id: int
    y_col: str = Field(..., description="因变量")
    x_cols: list[str] = Field(..., description="自变量列表")
    regression_type: str = Field("linear", description="回归类型")


class TimeseriesReq(BaseModel):
    dataset_id: int
    date_col: str = Field(..., description="时间列")
    value_col: str = Field(..., description="值列")
    periods: int = Field(5, description="预测期数")


class ClusteringReq(StatBase):
    k: int = Field(3, description="聚类数", ge=2, le=20)
    standardize: bool = Field(True, description="是否标准化")


# ── 接口 ──────────────────────────────────────────────

async def _get_df(db: AsyncSession, dataset_id: int):
    """获取数据集DataFrame"""
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        return None, "数据集不存在"
    try:
        filepath = ds.cleaned_path if ds.is_cleaned and ds.cleaned_path else ds.file_path
        df = read_file(filepath, ds.file_type)
        return df, None
    except Exception as e:
        return None, f"加载数据失败: {str(e)}"


@router.post("/descriptive")
async def descriptive(req: DescriptiveReq, db: AsyncSession = Depends(get_db)):
    """描述统计"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        result = StatisticEngine.descriptive(df, req.columns, req.confidence)
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"描述统计失败: {str(e)}")


@router.post("/hypothesis")
async def hypothesis(req: HypothesisReq, db: AsyncSession = Depends(get_db)):
    """假设检验"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        params = req.model_dump()
        params.pop("dataset_id", None)
        params.pop("columns", None)
        result = StatisticEngine.hypothesis(df, params)
        if "error" in result:
            return ApiResponse.fail(msg=result["error"])
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"假设检验失败: {str(e)}")


@router.post("/correlation")
async def correlation(req: CorrelationReq, db: AsyncSession = Depends(get_db)):
    """相关性分析"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        result = StatisticEngine.correlation(df, req.columns, req.method)
        if "error" in result:
            return ApiResponse.fail(msg=result["error"])
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"相关分析失败: {str(e)}")


@router.post("/regression")
async def regression(req: RegressionReq, db: AsyncSession = Depends(get_db)):
    """回归分析"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        params = req.model_dump()
        result = StatisticEngine.regression(df, params)
        if "error" in result:
            return ApiResponse.fail(msg=result["error"])
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"回归分析失败: {str(e)}")


@router.post("/timeseries")
async def timeseries(req: TimeseriesReq, db: AsyncSession = Depends(get_db)):
    """时序分析"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        params = req.model_dump()
        result = StatisticEngine.timeseries(df, params)
        if "error" in result:
            return ApiResponse.fail(msg=result["error"])
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"时序分析失败: {str(e)}")


@router.post("/clustering")
async def clustering(req: ClusteringReq, db: AsyncSession = Depends(get_db)):
    """聚类分析"""
    df, err = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        params = req.model_dump()
        result = StatisticEngine.clustering(df, params)
        if "error" in result:
            return ApiResponse.fail(msg=result["error"])
        return ApiResponse.ok(data=_safe_serialize(result))
    except Exception as e:
        return ApiResponse.fail(msg=f"聚类分析失败: {str(e)}")


def _classify_columns(df):
    """智能字段分类：区分数值型、文本型、日期型"""
    import re
    numeric_cols = []
    text_cols = []
    date_cols = []
    total_rows = len(df)

    for col in df.columns:
        dtype = df[col].dtype
        # 日期型
        if dtype == "datetime64[ns]" or dtype == "datetime64[us]" or dtype == "datetime64[ns, UTC]":
            date_cols.append(col)
            continue

        # 名称含日期关键词
        if re.search(r'日期|时间|date|time|datetime', col, re.I):
            date_cols.append(col)
            continue

        # 数值型
        if dtype in ("int64", "int32", "float64", "float32", "Int64", "Float64"):
            # 智能排除标识符字段：列名含 id/uid/编号/编码 且唯一值比例高
            is_id = bool(re.search(r'(id|编号|编码|序号|uid|no|code)$', col, re.I))
            if is_id:
                unique_ratio = df[col].nunique() / total_rows if total_rows > 0 else 0
                if unique_ratio > 0.7:
                    text_cols.append(col)
                    continue
            # 纯整数列且唯一值比例极高也视为标识符
            if dtype in ("int64", "int32", "Int64"):
                unique_ratio = df[col].nunique() / total_rows if total_rows > 0 else 0
                if unique_ratio > 0.95 and total_rows > 20:
                    text_cols.append(col)
                    continue
            numeric_cols.append(col)
            continue

        # 其他归为文本
        text_cols.append(col)

    return numeric_cols, text_cols, date_cols


@router.get("/fields/{dataset_id}")
async def get_fields(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """获取数据集字段列表（数值型/文本型分类）"""
    df, err = await _get_df(db, dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    numeric_cols, text_cols, date_cols = _classify_columns(df)
    all_cols = [{"name": c, "dtype": str(df[c].dtype), "category": "numeric" if c in numeric_cols else "text" if c in text_cols else "date", "non_null": int(df[c].notna().sum())} for c in df.columns]
    return ApiResponse.ok(data={
        "all": all_cols,
        "numeric": numeric_cols,
        "text": text_cols,
        "date": date_cols,
    })
