from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import get_db
from models.dataset import Dataset
from schemas.dataset import DatasetRename
from utils.response import ApiResponse
from services.dataset_service import (
    parse_uploaded_file,
    get_dataset_preview,
    get_dataset_stats,
    delete_dataset_files,
)

router = APIRouter(prefix="/api/datasets", tags=["数据管理"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """上传文件并自动解析元数据"""
    import os

    # 校验文件类型
    allowed_types = {".xlsx", ".xls", ".csv", ".txt"}
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_types:
        return ApiResponse.fail(message=f"Unsupported file type: {ext}")

    # 读取文件内容
    content = await file.read()

    # 校验文件大小 (50MB)
    if len(content) > 52_428_800:
        return ApiResponse.fail(message="File too large, max 50MB")

    # 解析文件并保存
    try:
        parse_result = await parse_uploaded_file(content, filename, user_id=1)
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
    except Exception as e:
        return ApiResponse.fail(message=f"Parse error: {str(e)}")

    # 创建数据集记录
    dataset = Dataset(
        user_id=1,  # MVP阶段默认用户
        name=filename,
        file_type=ext.lstrip("."),
        file_path=parse_result["file_path"],
        file_size=parse_result["file_size"],
        row_count=parse_result["row_count"],
        col_count=parse_result["col_count"],
        columns_json=parse_result["columns_json"],
        status="ready",
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    return ApiResponse.ok(data={
        "id": dataset.id,
        "name": dataset.name,
        "file_type": dataset.file_type,
        "file_size": dataset.file_size,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "status": dataset.status,
        "created_at": str(dataset.created_at) if dataset.created_at else "",
    })


@router.get("/")
async def list_datasets(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """数据集列表"""
    offset = (page - 1) * size
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()).offset(offset).limit(size))
    datasets = result.scalars().all()

    total_result = await db.execute(select(func.count(Dataset.id)))
    total = total_result.scalar() or 0

    items = []
    for ds in datasets:
        items.append({
            "id": ds.id,
            "name": ds.name,
            "file_type": ds.file_type,
            "file_size": ds.file_size,
            "row_count": ds.row_count,
            "col_count": ds.col_count,
            "is_cleaned": ds.is_cleaned,
            "status": ds.status,
            "created_at": str(ds.created_at) if ds.created_at else "",
        })

    return ApiResponse.ok(data={"total": total, "items": items, "page": page, "size": size})


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """数据集详情"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        return ApiResponse.not_found("Dataset not found")
    return ApiResponse.ok(data={
        "id": dataset.id,
        "name": dataset.name,
        "file_type": dataset.file_type,
        "file_size": dataset.file_size,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "columns_json": dataset.columns_json,
        "is_cleaned": dataset.is_cleaned,
        "version": dataset.version,
        "status": dataset.status,
        "created_at": str(dataset.created_at) if dataset.created_at else "",
    })


@router.get("/{dataset_id}/preview")
async def preview_dataset(dataset_id: int, rows: int = Query(20, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    """数据预览 - 返回前N行数据"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        return ApiResponse.not_found("Dataset not found")

    try:
        preview_data = get_dataset_preview(dataset_id, dataset.file_path, rows)
    except FileNotFoundError:
        return ApiResponse.fail(message="File not found on disk")
    except Exception as e:
        return ApiResponse.fail(message=f"Preview error: {str(e)}")

    return ApiResponse.ok(data=preview_data)


@router.get("/{dataset_id}/stats")
async def dataset_stats(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """数据集统计摘要"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        return ApiResponse.not_found("Dataset not found")

    try:
        stats_data = get_dataset_stats(dataset.file_path)
    except FileNotFoundError:
        return ApiResponse.fail(message="File not found on disk")
    except Exception as e:
        return ApiResponse.fail(message=f"Stats error: {str(e)}")

    return ApiResponse.ok(data=stats_data)


@router.put("/{dataset_id}")
async def rename_dataset(dataset_id: int, req: DatasetRename, db: AsyncSession = Depends(get_db)):
    """重命名数据集"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        return ApiResponse.not_found("Dataset not found")
    dataset.name = req.name
    await db.flush()
    return ApiResponse.ok(data={"id": dataset.id, "name": dataset.name})


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """删除数据集及其物理文件"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        return ApiResponse.not_found("Dataset not found")

    # 删除物理文件
    delete_dataset_files(dataset.file_path, dataset.cleaned_path)

    # 删除数据库记录
    await db.delete(dataset)
    return ApiResponse.ok(message="Deleted")
