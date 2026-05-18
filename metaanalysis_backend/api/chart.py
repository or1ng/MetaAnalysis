"""
可视化图表API
基于pandas + ECharts，生成图表配置
"""
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from models import get_db
from models.dataset import Dataset
from parser.file_parser import read_file
from utils.response import ApiResponse

router = APIRouter(prefix="/api/chart", tags=["可视化图表"])


def _safe(data):
    """JSON安全序列化"""
    if isinstance(data, dict):
        return {str(k): _safe(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_safe(v) for v in data]
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
    if isinstance(data, pd.Timestamp):
        return str(data)
    return data


async def _get_df(db: AsyncSession, dataset_id: int):
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        return None, "数据集不存在", None
    try:
        filepath = ds.cleaned_path if ds.is_cleaned and ds.cleaned_path else ds.file_path
        df = read_file(filepath, ds.file_type)
        return df, None, ds
    except Exception as e:
        return None, f"加载数据失败: {str(e)}", None


def _classify_columns(df):
    """智能字段分类"""
    import re
    numeric_cols = []
    text_cols = []
    date_cols = []
    for col in df.columns:
        dtype = df[col].dtype
        if "datetime" in str(dtype):
            date_cols.append(col)
            continue
        if dtype in ("int64", "int32", "float64", "float32", "Int64", "Float64"):
            is_id = bool(re.search(r'(id|编号|编码|序号|uid|no|code)$', col, re.I))
            if is_id and df[col].nunique() / len(df) > 0.7:
                text_cols.append(col)
                continue
            numeric_cols.append(col)
            continue
        text_cols.append(col)
    return numeric_cols, text_cols, date_cols


# 配色方案
COLOR_SCHEMES = {
    "default": ["#409EFF", "#67C23A", "#E6A23C", "#F56C6C", "#909399", "#00d2ff", "#ff6b6b", "#ffd93d"],
    "green": ["#2d8a4e", "#27ae60", "#52c41a", "#95de64", "#b7eb8f", "#d9f7be", "#6dd5ed", "#2193b0"],
    "purple": ["#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe", "#667eea", "#764ba2"],
}

# ECharts模板
CHART_TEMPLATES = [
    {"type": "bar", "name": "柱状图", "icon": "chart-bar"},
    {"type": "line", "name": "折线图", "icon": "chart-line"},
    {"type": "pie", "name": "饼图", "icon": "chart-pie"},
    {"type": "scatter", "name": "散点图", "icon": "dot-chart"},
    {"type": "boxplot", "name": "箱线图", "icon": "box-plot"},
    {"type": "histogram", "name": "直方图", "icon": "histogram"},
]


def _generate_bar_option(df, x_field, y_fields, title, color_scheme, show_legend):
    """柱状图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    series = []
    for i, y_field in enumerate(y_fields):
        # 按x_field分组求和
        grouped = df.groupby(x_field)[y_field].sum().sort_values(ascending=False).head(20)
        series.append({
            "name": y_field,
            "type": "bar",
            "data": _safe(grouped.values.tolist()),
            "itemStyle": {"color": colors[i % len(colors)]},
        })
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "legend": {"show": show_legend, "bottom": 0},
        "xAxis": {"type": "category", "data": _safe(grouped.index.tolist()), "axisLabel": {"rotate": 30}},
        "yAxis": {"type": "value"},
        "series": series,
        "grid": {"bottom": 60 if (show_legend and len(y_fields) > 1) else 40},
    }


def _generate_line_option(df, x_field, y_fields, title, color_scheme, show_legend):
    """折线图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    series = []
    x_data = None
    for i, y_field in enumerate(y_fields):
        grouped = df.groupby(x_field)[y_field].sum()
        if x_data is None:
            x_data = _safe(grouped.index.tolist())
        series.append({
            "name": y_field,
            "type": "line",
            "data": _safe(grouped.values.tolist()),
            "smooth": True,
            "lineStyle": {"color": colors[i % len(colors)]},
            "itemStyle": {"color": colors[i % len(colors)]},
            "areaStyle": {"opacity": 0.1},
        })
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "legend": {"show": show_legend, "bottom": 0},
        "xAxis": {"type": "category", "data": x_data, "axisLabel": {"rotate": 30}},
        "yAxis": {"type": "value"},
        "series": series,
    }


def _generate_pie_option(df, name_field, value_field, title, color_scheme):
    """饼图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    grouped = df.groupby(name_field)[value_field].sum().sort_values(ascending=False).head(10)
    pie_data = [{"name": str(k), "value": _safe(v)} for k, v in grouped.items()]
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"orient": "vertical", "left": "left", "top": "middle"},
        "series": [{
            "type": "pie",
            "radius": ["30%", "60%"],
            "center": ["55%", "55%"],
            "data": pie_data,
            "label": {"formatter": "{b}\n{d}%"},
            "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}},
        }],
        "color": colors,
    }


def _generate_scatter_option(df, x_field, y_field, title, color_scheme):
    """散点图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    data = df[[x_field, y_field]].dropna()
    scatter_data = _safe(data.values.tolist())
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"formatter": f"{x_field}: {{p[0]}}<br/>{y_field}: {{p[1]}}"},
        "xAxis": {"type": "value", "name": x_field},
        "yAxis": {"type": "value", "name": y_field},
        "series": [{
            "type": "scatter",
            "data": scatter_data[:2000],
            "symbolSize": 6,
            "itemStyle": {"color": colors[0], "opacity": 0.6},
        }],
    }


def _generate_boxplot_option(df, columns, title, color_scheme):
    """箱线图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    box_data = []
    categories = []
    for i, col in enumerate(columns[:8]):
        s = df[col].dropna()
        if len(s) == 0:
            continue
        q1, q2, q3 = s.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        lower = max(s.min(), q1 - 1.5 * iqr)
        upper = min(s.max(), q3 + 1.5 * iqr)
        box_data.append([lower, q1, q2, q3, upper])
        categories.append(col)

    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "category", "data": categories},
        "yAxis": {"type": "value"},
        "series": [{
            "type": "boxplot",
            "data": _safe(box_data),
            "itemStyle": {"color": colors[0], "borderColor": colors[0]},
        }],
    }


def _generate_histogram_option(df, column, title, color_scheme):
    """直方图配置"""
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    s = df[column].dropna()
    # 计算直方图bins
    counts, bin_edges = np.histogram(s, bins=min(30, max(5, s.nunique())))
    bin_labels = [f"{bin_edges[i]:.1f}" for i in range(len(counts))]
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": _safe(bin_labels), "axisLabel": {"rotate": 30}},
        "yAxis": {"type": "value", "name": "频次"},
        "series": [{
            "type": "bar",
            "data": _safe(counts.tolist()),
            "itemStyle": {"color": colors[0]},
            "barWidth": "90%",
        }],
    }


# ── Schema ──────────────────────────────────────────────

class ChartGenerateReq(BaseModel):
    dataset_id: int = Field(..., description="数据集ID")
    chart_type: str = Field(..., description="图表类型: bar/line/pie/scatter/boxplot/histogram")
    x_field: Optional[str] = Field(None, description="X轴/维度字段")
    y_fields: Optional[list[str]] = Field(None, description="Y轴/指标字段")
    title: Optional[str] = Field("", description="图表标题")
    color_scheme: str = Field("default", description="配色方案")
    show_legend: bool = Field(True, description="显示图例")


class BatchChartReq(BaseModel):
    dataset_id: int = Field(..., description="数据集ID")
    chart_type: str = Field("bar", description="图表类型")
    columns: Optional[list[str]] = Field(None, description="指定字段，None=自动选择")


class SaveChartReq(BaseModel):
    dataset_id: int
    chart_type: str
    echarts_option: dict
    title: str = ""


# ── 路由 ──────────────────────────────────────────────

@router.post("/generate")
async def generate_chart(req: ChartGenerateReq, db: AsyncSession = Depends(get_db)):
    """生成ECharts配置"""
    df, err, ds = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)

    num_cols, text_cols, date_cols = _classify_columns(df)

    # 自动选择字段
    x_field = req.x_field
    y_fields = req.y_fields
    title = req.title or f"{ds.name} - {req.chart_type}"

    if req.chart_type in ("bar", "line"):
        if not x_field:
            x_field = text_cols[0] if text_cols else date_cols[0] if date_cols else None
        if not y_fields:
            y_fields = num_cols[:2] if num_cols else []
        if not x_field or not y_fields:
            return ApiResponse.fail(msg="无法自动选择字段，请手动指定X轴和Y轴字段")

        if req.chart_type == "bar":
            option = _generate_bar_option(df, x_field, y_fields, title, req.color_scheme, req.show_legend)
        else:
            option = _generate_line_option(df, x_field, y_fields, title, req.color_scheme, req.show_legend)

    elif req.chart_type == "pie":
        if not x_field:
            x_field = text_cols[0] if text_cols else None
        if not y_fields:
            y_fields = num_cols[:1] if num_cols else []
        if not x_field or not y_fields:
            return ApiResponse.fail(msg="饼图需要指定分类字段和数值字段")
        option = _generate_pie_option(df, x_field, y_fields[0], title, req.color_scheme)

    elif req.chart_type == "scatter":
        if not x_field:
            x_field = num_cols[0] if len(num_cols) >= 2 else None
        if not y_fields:
            y_fields = num_cols[1:2] if len(num_cols) >= 2 else []
        if not x_field or not y_fields:
            return ApiResponse.fail(msg="散点图需要至少2个数值字段")
        option = _generate_scatter_option(df, x_field, y_fields[0], title, req.color_scheme)

    elif req.chart_type == "boxplot":
        cols = req.y_fields or num_cols[:5]
        if not cols:
            return ApiResponse.fail(msg="箱线图需要至少1个数值字段")
        option = _generate_boxplot_option(df, cols, title, req.color_scheme)

    elif req.chart_type == "histogram":
        col = req.y_fields[0] if req.y_fields else (num_cols[0] if num_cols else None)
        if not col:
            return ApiResponse.fail(msg="直方图需要指定1个数值字段")
        option = _generate_histogram_option(df, col, title, req.color_scheme)
    else:
        return ApiResponse.fail(msg=f"不支持的图表类型: {req.chart_type}")

    return ApiResponse.ok(data={
        "echarts_option": _safe(option),
        "chart_type": req.chart_type,
        "title": title,
    })


@router.get("/templates")
async def chart_templates():
    """图表模板列表"""
    return ApiResponse.ok(data={
        "templates": CHART_TEMPLATES,
        "color_schemes": list(COLOR_SCHEMES.keys()),
    })


@router.get("/fields/{dataset_id}")
async def get_dataset_fields(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """获取数据集字段分类（供前端字段面板）"""
    df, err, ds = await _get_df(db, dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    num_cols, text_cols, date_cols = _classify_columns(df)
    return ApiResponse.ok(data={
        "numeric": num_cols,
        "text": text_cols,
        "date": date_cols,
        "dataset_name": ds.name,
    })


@router.post("/batch")
async def batch_charts(req: BatchChartReq, db: AsyncSession = Depends(get_db)):
    """批量自动出图"""
    df, err, ds = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    num_cols, text_cols, date_cols = _classify_columns(df)
    charts = []

    # 1. 数值字段分布直方图
    for col in num_cols[:4]:
        option = _generate_histogram_option(df, col, f"{col} 分布", "default")
        charts.append({"type": "histogram", "title": f"{col} 分布", "echarts_option": _safe(option)})

    # 2. 第一个文本字段的柱状图
    if text_cols and num_cols:
        for num_col in num_cols[:2]:
            option = _generate_bar_option(df, text_cols[0], [num_col], f"按{text_cols[0]}的{num_col}", "default", True)
            charts.append({"type": "bar", "title": f"按{text_cols[0]}的{num_col}", "echarts_option": _safe(option)})

    # 3. 饼图
    if text_cols and num_cols:
        option = _generate_pie_option(df, text_cols[0], num_cols[0], f"{num_cols[0]}占比", "default")
        charts.append({"type": "pie", "title": f"{num_cols[0]}占比", "echarts_option": _safe(option)})

    # 4. 箱线图
    if len(num_cols) >= 2:
        option = _generate_boxplot_option(df, num_cols[:5], "数值字段箱线图", "default")
        charts.append({"type": "boxplot", "title": "数值字段箱线图", "echarts_option": _safe(option)})

    return ApiResponse.ok(data={"charts": charts, "total": len(charts)})


# 保存的图表（MVP内存存储）
_saved_charts = {}


@router.post("/save")
async def save_chart(req: SaveChartReq):
    """保存图表"""
    import uuid
    chart_id = str(uuid.uuid4())[:8]
    _saved_charts[chart_id] = {
        "id": chart_id,
        "dataset_id": req.dataset_id,
        "chart_type": req.chart_type,
        "title": req.title,
        "echarts_option": req.echarts_option,
        "created_at": pd.Timestamp.now().isoformat(),
    }
    return ApiResponse.ok(data={"chart_id": chart_id})


@router.get("/saved/{dataset_id}")
async def saved_charts(dataset_id: int):
    """已保存图表列表"""
    items = [c for c in _saved_charts.values() if c["dataset_id"] == dataset_id]
    return ApiResponse.ok(data={"charts": items, "total": len(items)})
