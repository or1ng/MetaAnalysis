"""
数据清洗 API
- 质量诊断 / 一键清洗 / 自定义清洗 / 清洗日志 / 回滚 / 还原
"""

import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db
from models.dataset import Dataset
from models.clean_log import CleanLog
from utils.response import ApiResponse
from parser.file_parser import read_file, get_preview, extract_metadata, get_basic_stats
from services import clean_service

router = APIRouter(prefix="/api/clean", tags=["数据清洗"])

# 清洗文件暂存目录
CLEAN_WORK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "clean_work")


# ── Pydantic Schema ───────────────────────────────────────

class CustomCleanRequest(BaseModel):
    """自定义清洗请求"""
    missing_strategy: str = Field("mean", description="缺失值策略: mean/median/mode/drop/constant")
    missing_custom_value: Optional[str] = Field(None, description="自定义填充值(当strategy=constant)")
    outlier_method: str = Field("iqr", description="异常值检测方法: iqr/zscore")
    outlier_handle: str = Field("clip", description="异常值处理方式: clip/mean/drop")
    outlier_threshold: float = Field(1.5, description="IQR倍数/Z-Score倍数")
    remove_duplicates: bool = Field(True, description="是否去重")
    dup_subset: Optional[list] = Field(None, description="去重依据列名列表")
    strip_whitespace: bool = Field(True, description="去除空白")
    date_unify: bool = Field(True, description="日期格式统一")
    case_lower: bool = Field(False, description="文本转小写")


# ── 辅助函数 ──────────────────────────────────────────────

async def _get_dataset(db: AsyncSession, dataset_id: int) -> Dataset:
    """获取数据集，如不存在抛404"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    ds = result.scalar_one_or_none()
    if not ds:
        from core.exceptions import AppException
        raise AppException(code=404, message="数据集不存在")
    return ds


def _get_working_file(dataset: Dataset) -> str:
    """获取当前工作文件路径（优先cleaned_path，其次原始file_path）"""
    if dataset.cleaned_path and os.path.exists(dataset.cleaned_path):
        return dataset.cleaned_path
    return dataset.file_path


def _save_cleaned_df(df, dataset: Dataset) -> str:
    """保存清洗后的DataFrame，保持与原始文件相同的格式"""
    os.makedirs(CLEAN_WORK_DIR, exist_ok=True)
    file_type = dataset.file_type  # csv / xlsx / xls
    filename = f"cleaned_{dataset.id}_{dataset.version}.{file_type}"
    filepath = os.path.join(CLEAN_WORK_DIR, filename)
    if file_type in ("xlsx", "xls"):
        df.to_excel(filepath, index=False, engine='openpyxl')
    else:
        df.to_csv(filepath, index=False, encoding='utf-8')
    return filepath


# ── 接口 ──────────────────────────────────────────────────

@router.get("/summary/{dataset_id}")
async def clean_summary(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """数据质量诊断报告"""
    ds = await _get_dataset(db, dataset_id)
    filepath = _get_working_file(ds)

    try:
        df = read_file(filepath, ds.file_type)
    except Exception as e:
        return ApiResponse.fail(message=f"文件读取失败: {str(e)}")

    # 质量评分
    qs = clean_service.quality_score(df)

    # 异常值详情
    outliers = clean_service.detect_outliers(df, method="iqr")
    outlier_summary = []
    for col, info in outliers.items():
        outlier_summary.append({
            "column": col,
            "count": info["count"],
            "range": f"[{info['lower']:.2f}, {info['upper']:.2f}]",
        })

    # 缺失值详情
    missing_detail = []
    for col in df.columns:
        mc = int(df[col].isna().sum())
        if mc > 0:
            missing_detail.append({
                "column": col,
                "missing_count": mc,
                "missing_rate": round(mc / len(df) * 100, 1),
            })

    return ApiResponse.ok(data={
        **qs,
        "outlier_detail": outlier_summary,
        "missing_detail": missing_detail,
        "suggestions": _generate_suggestions(qs, outlier_summary, missing_detail),
    })


def _generate_suggestions(qs, outliers, missing) -> list:
    """根据质量诊断生成建议"""
    suggestions = []
    if qs["missing_cells"] > 0:
        suggestions.append(f"发现{qs['missing_cells']}处缺失值，建议均值/中位数填充")
    if qs["outlier_count"] > 0:
        col_names = [o["column"] for o in outliers[:3]]
        suggestions.append(f"{len(outliers)}个数值列存在异常值({', '.join(col_names)}等)，建议IQR截断")
    if qs["dup_rows"] > 0:
        suggestions.append(f"发现{qs['dup_rows']}行重复数据，建议去重")
    if qs["format_issues"] > 0:
        suggestions.append(f"存在{qs['format_issues']}处格式问题，建议标准化")
    if qs["score"] >= 95:
        suggestions.append("数据质量优秀，无需清洗")
    return suggestions


@router.post("/auto/{dataset_id}")
async def auto_clean(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """一键智能清洗"""
    ds = await _get_dataset(db, dataset_id)
    filepath = _get_working_file(ds)

    try:
        df = read_file(filepath, ds.file_type)
    except Exception as e:
        return ApiResponse.fail(message=f"文件读取失败: {str(e)}")

    # 保存快照
    os.makedirs(CLEAN_WORK_DIR, exist_ok=True)
    snapshot_path = clean_service.save_snapshot(df, CLEAN_WORK_DIR, ds.id, ds.version)

    # 执行一键清洗
    cleaned_df, logs = clean_service.auto_clean(df)

    # 保存清洗结果
    cleaned_path = _save_cleaned_df(cleaned_df, ds)

    # 更新数据集
    ds.cleaned_path = cleaned_path
    ds.version += 1
    ds.is_cleaned = 1
    ds.row_count = len(cleaned_df)
    ds.col_count = len(cleaned_df.columns)
    meta = extract_metadata(cleaned_df)
    ds.columns_json = meta["columns"]

    # 写入清洗日志
    for log in logs:
        clean_log = CleanLog(
            dataset_id=ds.id,
            action_type=log["action"],
            params_json={},
            affected_rows=log["affected"],
            result_summary=log["summary"],
            snapshot_path=snapshot_path,
        )
        db.add(clean_log)

    await db.commit()

    # 清洗后质量评分
    new_qs = clean_service.quality_score(cleaned_df)

    return ApiResponse.ok(data={
        "dataset_id": ds.id,
        "cleaned": True,
        "before_rows": len(df),
        "after_rows": len(cleaned_df),
        "before_score": clean_service.quality_score(df)["score"],
        "after_score": new_qs["score"],
        "logs": logs,
        "new_preview": get_preview(cleaned_df, 10),
    })


@router.post("/custom/{dataset_id}")
async def custom_clean(dataset_id: int, req: CustomCleanRequest,
                       db: AsyncSession = Depends(get_db)):
    """自定义清洗规则"""
    ds = await _get_dataset(db, dataset_id)
    filepath = _get_working_file(ds)

    try:
        df = read_file(filepath, ds.file_type)
    except Exception as e:
        return ApiResponse.fail(message=f"文件读取失败: {str(e)}")

    # 保存快照
    os.makedirs(CLEAN_WORK_DIR, exist_ok=True)
    snapshot_path = clean_service.save_snapshot(df, CLEAN_WORK_DIR, ds.id, ds.version)

    logs = []
    current_df = df.copy()
    before_rows = len(current_df)

    # 1. 格式标准化
    if req.strip_whitespace or req.date_unify or req.case_lower:
        current_df, aff, summary = clean_service.normalize_format(
            current_df,
            strip_whitespace=req.strip_whitespace,
            date_unify=req.date_unify,
            case_lower=req.case_lower,
        )
        if aff > 0:
            logs.append({"action": "格式标准化", "affected": aff, "summary": summary})

    # 2. 去重
    if req.remove_duplicates:
        subset = req.dup_subset if req.dup_subset else None
        current_df, aff, summary = clean_service.remove_duplicates(current_df, subset=subset)
        if aff > 0:
            logs.append({"action": "去重", "affected": aff, "summary": summary})

    # 3. 缺失值处理
    custom_val = req.missing_custom_value
    current_df, aff, summary = clean_service.fill_missing(
        current_df,
        strategy=req.missing_strategy,
        custom_value=custom_val,
    )
    if aff > 0:
        logs.append({"action": f"缺失值处理({req.missing_strategy})", "affected": aff, "summary": summary})

    # 4. 异常值处理
    current_df, aff, summary = clean_service.handle_outliers(
        current_df,
        method=req.outlier_method,
        handle=req.outlier_handle,
        threshold=req.outlier_threshold,
    )
    if aff > 0:
        logs.append({"action": f"异常值处理({req.outlier_handle})", "affected": aff, "summary": summary})

    # 保存结果
    cleaned_path = _save_cleaned_df(current_df, ds)

    ds.cleaned_path = cleaned_path
    ds.version += 1
    ds.is_cleaned = 1
    ds.row_count = len(current_df)
    ds.col_count = len(current_df.columns)
    meta = extract_metadata(current_df)
    ds.columns_json = meta["columns"]

    # 写入日志
    for log in logs:
        clean_log = CleanLog(
            dataset_id=ds.id,
            action_type=log["action"],
            params_json=req.model_dump(),
            affected_rows=log["affected"],
            result_summary=log["summary"],
            snapshot_path=snapshot_path,
        )
        db.add(clean_log)

    await db.commit()

    new_qs = clean_service.quality_score(current_df)

    return ApiResponse.ok(data={
        "dataset_id": ds.id,
        "cleaned": len(logs) > 0,
        "before_rows": before_rows,
        "after_rows": len(current_df),
        "before_score": clean_service.quality_score(df)["score"],
        "after_score": new_qs["score"],
        "logs": logs,
        "new_preview": get_preview(current_df, 10),
    })


@router.get("/logs/{dataset_id}")
async def clean_logs(dataset_id: int, page: int = Query(1, ge=1),
                     page_size: int = Query(20, ge=1, le=100),
                     db: AsyncSession = Depends(get_db)):
    """清洗日志列表"""
    # 确认数据集存在
    await _get_dataset(db, dataset_id)

    query = select(CleanLog).where(CleanLog.dataset_id == dataset_id).order_by(desc(CleanLog.created_at))
    # 计算总数
    from sqlalchemy import func as sa_func
    count_q = select(sa_func.count()).select_from(CleanLog).where(CleanLog.dataset_id == dataset_id)
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "action_type": log.action_type,
            "params": log.params_json or {},
            "affected_rows": log.affected_rows,
            "result_summary": log.result_summary,
            "has_snapshot": bool(log.snapshot_path and os.path.exists(log.snapshot_path)),
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
        })

    return ApiResponse.ok(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.post("/rollback/{log_id}")
async def rollback(log_id: int, db: AsyncSession = Depends(get_db)):
    """回滚到指定操作前的快照"""
    result = await db.execute(select(CleanLog).where(CleanLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        from core.exceptions import AppException
        raise AppException(code=404, message="清洗日志不存在")

    if not log.snapshot_path or not os.path.exists(log.snapshot_path):
        return ApiResponse.fail(message="快照文件不存在，无法回滚")

    # 加载快照
    df = clean_service.load_snapshot(log.snapshot_path)

    # 更新数据集
    ds_result = await db.execute(select(Dataset).where(Dataset.id == log.dataset_id))
    ds = ds_result.scalar_one()
    cleaned_path = _save_cleaned_df(df, ds)

    ds.cleaned_path = cleaned_path
    ds.row_count = len(df)
    ds.col_count = len(df.columns)
    meta = extract_metadata(df)
    ds.columns_json = meta["columns"]

    await db.commit()

    return ApiResponse.ok(data={
        "message": f"已回滚到操作 [{log.action_type}] 之前的状态",
        "rows": len(df),
        "preview": get_preview(df, 5),
    })


@router.post("/restore/{dataset_id}")
async def restore(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """还原到原始数据（清除所有清洗结果）"""
    ds = await _get_dataset(db, dataset_id)

    if not os.path.exists(ds.file_path):
        return ApiResponse.fail(message="原始文件不存在")

    df = read_file(ds.file_path, ds.file_type)
    ds.cleaned_path = ""
    ds.is_cleaned = 0
    ds.version = 1
    ds.row_count = len(df)
    ds.col_count = len(df.columns)
    meta = extract_metadata(df)
    ds.columns_json = meta["columns"]

    await db.commit()

    return ApiResponse.ok(data={
        "message": "已还原到原始数据",
        "rows": len(df),
        "preview": get_preview(df, 5),
    })


@router.get("/preview/{dataset_id}")
async def clean_preview(dataset_id: int, rows: int = Query(50, ge=1, le=200),
                        db: AsyncSession = Depends(get_db)):
    """清洗后数据预览（含异常标记）"""
    ds = await _get_dataset(db, dataset_id)
    filepath = _get_working_file(ds)

    try:
        df = read_file(filepath, ds.file_type)
    except Exception as e:
        return ApiResponse.fail(message=f"文件读取失败: {str(e)}")

    # 检测异常值标记
    outliers = clean_service.detect_outliers(df, method="iqr")
    outlier_cells = set()
    for col, info in outliers.items():
        for idx in info["indices"]:
            outlier_cells.add((idx, col))

    # 检测重复行
    dup_mask = df.duplicated(keep=False)
    dup_indices = set(df[dup_mask].index.tolist())

    # 检测缺失
    missing_cells = set()
    for col in df.columns:
        for idx in df[df[col].isna()].index:
            missing_cells.add((idx, col))

    # 预览数据
    preview_df = df.head(rows).copy()
    preview_data = []
    for i, (idx, row) in enumerate(preview_df.iterrows()):
        row_data = {"_row_num": i + 1, "_is_dup": idx in dup_indices}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                row_data[col] = None
            elif hasattr(val, 'item'):
                row_data[col] = val.item()
            else:
                row_data[col] = val
            row_data[f"_cell_{col}"] = "outlier" if (idx, col) in outlier_cells else \
                ("missing" if (idx, col) in missing_cells else "normal")
        preview_data.append(row_data)

    return ApiResponse.ok(data={
        "rows": preview_data,
        "columns": list(df.columns),
        "outlier_count": sum(info["count"] for info in outliers.values()),
        "missing_count": int(df.isna().sum().sum()),
        "dup_count": int(dup_mask.sum()),
    })


# pandas import for type checking
import pandas as pd
