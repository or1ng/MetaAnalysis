"""
数据集服务层 - 封装数据集的业务逻辑
"""

import os
import json
import pandas as pd
from parser.file_parser import read_file, read_file_from_bytes, extract_metadata, get_preview, get_basic_stats
from utils.file_utils import generate_filepath


async def parse_uploaded_file(content: bytes, filename: str, user_id: int = 1) -> dict:
    """
    解析上传的文件，返回元数据和保存路径
    
    Args:
        content: 文件二进制内容
        filename: 原始文件名
        user_id: 用户ID
    
    Returns:
        {
            "file_path": str,        # 保存的文件路径
            "row_count": int,        # 行数
            "col_count": int,        # 列数
            "columns_json": list,    # 列元数据
            "file_size": int,        # 文件大小
        }
    """
    # 生成唯一路径并保存
    file_path = generate_filepath(user_id, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # 解析文件
    try:
        df = read_file_from_bytes(content, filename)
    except Exception as e:
        # 如果解析失败，删除已保存的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise ValueError(f"File parse error: {str(e)}")

    # 提取元数据
    meta = extract_metadata(df)

    return {
        "file_path": file_path,
        "row_count": meta["row_count"],
        "col_count": meta["col_count"],
        "columns_json": meta["columns"],
        "file_size": len(content),
    }


def get_dataset_preview(dataset_id: int, file_path: str, rows: int = 20) -> dict:
    """
    获取数据集预览数据
    
    Args:
        dataset_id: 数据集ID
        file_path: 文件路径
        rows: 预览行数
    
    Returns:
        {
            "dataset_id": int,
            "preview": list,       # 前N行数据
            "columns": list,       # 列信息
            "row_count": int,      # 总行数
            "col_count": int,      # 总列数
        }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = read_file(file_path)
    meta = extract_metadata(df)
    preview = get_preview(df, rows)

    return {
        "dataset_id": dataset_id,
        "preview": preview,
        "columns": meta["columns"],
        "row_count": meta["row_count"],
        "col_count": meta["col_count"],
    }


def get_dataset_stats(file_path: str) -> dict:
    """
    获取数据集统计摘要
    
    Args:
        file_path: 文件路径
    
    Returns:
        {
            "columns": list,          # 列元数据
            "numeric_stats": list,    # 数值列统计
            "categorical_stats": list, # 分类列统计
            "row_count": int,
            "col_count": int,
        }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = read_file(file_path)
    meta = extract_metadata(df)
    stats = get_basic_stats(df)

    return {
        "columns": meta["columns"],
        "numeric_stats": stats["numeric_cols"],
        "categorical_stats": stats["categorical_cols"],
        "row_count": meta["row_count"],
        "col_count": meta["col_count"],
    }


def delete_dataset_files(file_path: str, cleaned_path: str = "") -> None:
    """删除数据集关联的物理文件"""
    for path in [file_path, cleaned_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
