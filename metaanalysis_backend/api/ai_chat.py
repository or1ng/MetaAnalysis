"""
AI智能问答API
MVP阶段：基于pandas统计分析的本地推理引擎（不依赖外部LLM）
"""
import re
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional

from models import get_db
from models.dataset import Dataset
from parser.file_parser import read_file
from utils.response import ApiResponse

router = APIRouter(prefix="/api/ai", tags=["AI智能问答"])


# ── 工具函数 ──────────────────────────────────────────────

def _safe_serialize(data):
    """递归清理numpy类型"""
    if isinstance(data, dict):
        return {str(k): _safe_serialize(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_safe_serialize(v) for v in data]
    if isinstance(data, (np.bool_,)):
        return bool(data)
    if isinstance(data, (np.integer,)):
        return int(data)
    if isinstance(data, (np.floating,)):
        v = float(data)
        return None if (np.isnan(v) or np.isinf(v)) else v
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, pd.Timestamp):
        return str(data)
    return data


async def _get_df(db: AsyncSession, dataset_id: int):
    """获取数据集DataFrame"""
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        return None, "数据集不存在", None
    try:
        filepath = ds.cleaned_path if ds.is_cleaned and ds.cleaned_path else ds.file_path
        df = read_file(filepath, ds.file_type)
        return df, None, ds
    except Exception as e:
        return None, f"加载数据失败: {str(e)}", None


def _numeric_cols(df):
    return df.select_dtypes(include=["number"]).columns.tolist()


def _detect_intent(question: str, df: pd.DataFrame) -> str:
    """检测用户问题意图"""
    q = question.lower()
    num_cols = _numeric_cols(df)
    all_cols = list(df.columns)

    # 数据概览
    if any(k in q for k in ["概览", "概况", "总览", "整体", "介绍一下", "什么数据", "有哪些列", "字段"]):
        return "overview"
    # 缺失值
    if any(k in q for k in ["缺失", "空值", "null", "na", "nan"]):
        return "missing"
    # 重复值
    if any(k in q for k in ["重复", "去重", "dup"]):
        return "duplicates"
    # 分布
    if any(k in q for k in ["分布", "频次", "频率", "占比", "比例"]):
        return "distribution"
    # 相关性
    if any(k in q for k in ["相关", "关联", "correlation", "corr"]):
        return "correlation"
    # 趋势
    if any(k in q for k in ["趋势", "变化", "增长", "下降", "同比", "环比"]):
        return "trend"
    # 对比
    if any(k in q for k in ["对比", "比较", "差异", "vs"]):
        return "comparison"
    # 异常值
    if any(k in q for k in ["异常值", "离群", "outlier"]):
        return "outlier"
    # 排名/Top
    if any(k in q for k in ["排名", "top", "前几", "最多", "最少", "最大", "最小", "最高", "最低"]):
        return "ranking"
    # 汇总/均值/求和
    if any(k in q for k in ["均值", "平均", "求和", "总计", "合计", "mean", "sum", "总量", "中位数", "标准差"]):
        return "aggregation"
    # 分组
    if any(k in q for k in ["分组", "按", "每个", "各个", "group"]):
        return "groupby"

    # 检查是否提到具体列名
    mentioned_cols = [c for c in all_cols if c.lower() in q]
    if mentioned_cols and num_cols:
        return "column_analysis"
    if mentioned_cols:
        return "column_info"

    # 通用统计
    if num_cols:
        return "descriptive"

    return "overview"


def _generate_reply(question: str, df: pd.DataFrame, ds) -> dict:
    """生成本地分析回复"""
    intent = _detect_intent(question, df)
    num_cols = _numeric_cols(df)
    total_rows = len(df)
    total_cols = len(df.columns)
    reply_parts = []
    charts = []

    # ── 数据概览 ──
    if intent == "overview":
        reply_parts.append(f"📊 **{ds.name}** 数据概览：")
        reply_parts.append(f"- 共 **{total_rows}** 行 × **{total_cols}** 列")
        reply_parts.append(f"- 数值型字段 {len(num_cols)} 个：{', '.join(num_cols[:8])}{'...' if len(num_cols) > 8 else ''}")
        text_cols = [c for c in df.columns if c not in num_cols]
        if text_cols:
            reply_parts.append(f"- 文本型字段 {len(text_cols)} 个：{', '.join(text_cols[:8])}{'...' if len(text_cols) > 8 else ''}")
        missing = df.isnull().sum()
        total_missing = missing.sum()
        if total_missing > 0:
            reply_parts.append(f"- 缺失值共 **{total_missing}** 处（涉及 {missing[missing > 0].count()} 个字段）")
        else:
            reply_parts.append("- 无缺失值 ✅")
        dup = df.duplicated().sum()
        if dup > 0:
            reply_parts.append(f"- 重复行 **{dup}** 行")
        else:
            reply_parts.append("- 无重复行 ✅")

        # 为概览生成一个快速分布图
        if num_cols:
            chart_data = {}
            for col in num_cols[:6]:
                chart_data[col] = _safe_serialize(df[col].describe().to_dict())
            charts.append({
                "type": "bar",
                "title": "数值字段统计摘要",
                "data": chart_data
            })

    # ── 缺失值分析 ──
    elif intent == "missing":
        missing = df.isnull().sum()
        missing_cols = missing[missing > 0].sort_values(ascending=False)
        if len(missing_cols) == 0:
            reply_parts.append("✅ 当前数据集 **无缺失值**，数据完整性良好。")
        else:
            reply_parts.append(f"🔍 缺失值分析（共 {missing.sum()} 处）：")
            for col, cnt in missing_cols.items():
                pct = cnt / total_rows * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                reply_parts.append(f"- **{col}**: {cnt} 处 ({pct:.1f}%) {bar}")
            charts.append({
                "type": "bar",
                "title": "各字段缺失值数量",
                "data": _safe_serialize(missing_cols.to_dict())
            })

    # ── 重复值 ──
    elif intent == "duplicates":
        dup = df.duplicated().sum()
        reply_parts.append(f"🔍 重复值分析：")
        reply_parts.append(f"- 完全重复行：**{dup}** 行 ({dup/total_rows*100:.1f}%)")
        for col in df.columns:
            dup_count = df[col].duplicated().sum()
            unique_count = df[col].nunique()
            if dup_count > total_rows * 0.5:
                reply_parts.append(f"- **{col}**: {unique_count} 个唯一值（{dup_count} 行重复）")

    # ── 分布分析 ──
    elif intent == "distribution":
        reply_parts.append("📊 数据分布分析：")
        # 找到问题中提到的列
        mentioned = [c for c in df.columns if c in question]
        target_cols = mentioned if mentioned else num_cols[:4]

        for col in target_cols[:4]:
            if col in num_cols:
                desc = df[col].describe()
                reply_parts.append(f"\n**{col}**（数值型）：")
                reply_parts.append(f"- 均值: {desc['mean']:.2f}, 中位数: {desc['50%']:.2f}, 标准差: {desc['std']:.2f}")
                reply_parts.append(f"- 范围: [{desc['min']:.2f}, {desc['max']:.2f}]")
                # 四分位
                iqr = desc['75%'] - desc['25%']
                reply_parts.append(f"- IQR: {iqr:.2f} (Q1={desc['25%']:.2f}, Q3={desc['75%']:.2f})")
            else:
                vc = df[col].value_counts().head(5)
                reply_parts.append(f"\n**{col}**（文本型）Top5：")
                for val, cnt in vc.items():
                    reply_parts.append(f"- {val}: {cnt} ({cnt/total_rows*100:.1f}%)")

        # 生成分布图数据
        if num_cols:
            col = target_cols[0] if target_cols[0] in num_cols else num_cols[0]
            if col in num_cols:
                hist_data = df[col].dropna().tolist()
                charts.append({
                    "type": "histogram",
                    "title": f"{col} 分布直方图",
                    "data": _safe_serialize({"values": hist_data[:5000], "column": col})
                })

    # ── 相关性分析 ──
    elif intent == "correlation":
        if len(num_cols) < 2:
            reply_parts.append("⚠️ 数值型字段不足2个，无法进行相关性分析。")
        else:
            corr_matrix = df[num_cols].corr()
            reply_parts.append("🔗 相关性分析（Pearson系数）：")
            # 找强相关对
            strong_pairs = []
            for i in range(len(num_cols)):
                for j in range(i+1, len(num_cols)):
                    c1, c2 = num_cols[i], num_cols[j]
                    r = corr_matrix.loc[c1, c2]
                    if abs(r) > 0.5:
                        strong_pairs.append((c1, c2, r))
            if strong_pairs:
                strong_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                for c1, c2, r in strong_pairs[:6]:
                    strength = "强" if abs(r) > 0.8 else "中"
                    direction = "正" if r > 0 else "负"
                    reply_parts.append(f"- **{c1}** ↔ **{c2}**: r={r:.3f}（{direction}相关，{strength}）")
            else:
                reply_parts.append("- 未发现显著相关关系（|r| > 0.5）")
            charts.append({
                "type": "heatmap",
                "title": "相关性热力图",
                "data": _safe_serialize(corr_matrix.to_dict())
            })

    # ── 排名分析 ──
    elif intent == "ranking":
        reply_parts.append("🏆 排名分析：")
        mentioned = [c for c in df.columns if c in question]
        # 尝试找到分组列和指标列
        group_col = None
        metric_col = None
        for c in mentioned:
            if c not in num_cols:
                group_col = c
            elif c in num_cols:
                metric_col = c

        if group_col and metric_col:
            result = df.groupby(group_col)[metric_col].agg(["sum", "mean", "count"]).sort_values("sum", ascending=False).head(10)
            reply_parts.append(f"\n按 **{group_col}** 分组的 **{metric_col}** 排名（Top 10）：")
            for idx, (name, row) in enumerate(result.iterrows(), 1):
                reply_parts.append(f"{idx}. {name}: 总计={row['sum']:.2f}, 均值={row['mean']:.2f}, 次数={int(row['count'])}")
            charts.append({
                "type": "bar",
                "title": f"{metric_col} Top10（按{group_col}）",
                "data": _safe_serialize(result["sum"].to_dict())
            })
        elif num_cols:
            for col in num_cols[:2]:
                top5 = df.nlargest(5, col)
                reply_parts.append(f"\n**{col}** Top 5：")
                for _, row in top5.iterrows():
                    vals = [f"{c}={row[c]}" for c in df.columns[:3] if c != col]
                    reply_parts.append(f"- {row[col]:.2f} ({', '.join(vals)})")

    # ── 分组分析 ──
    elif intent == "groupby":
        mentioned = [c for c in df.columns if c in question]
        text_mentioned = [c for c in mentioned if c not in num_cols]
        num_mentioned = [c for c in mentioned if c in num_cols]
        group_col = text_mentioned[0] if text_mentioned else None
        metric_cols = num_mentioned if num_mentioned else num_cols[:3]

        if group_col:
            reply_parts.append(f"📋 按 **{group_col}** 分组统计：")
            grouped = df.groupby(group_col)[metric_cols].agg(["sum", "mean", "count"])
            for col in metric_cols[:4]:
                top = grouped[col]["sum"].sort_values(ascending=False).head(8)
                reply_parts.append(f"\n**{col}**：")
                for name, val in top.items():
                    reply_parts.append(f"- {name}: {val:.2f}")
            charts.append({
                "type": "bar",
                "title": f"按{group_col}分组 - {metric_cols[0]}汇总",
                "data": _safe_serialize(df.groupby(group_col)[metric_cols[0]].sum().sort_values(ascending=False).head(10).to_dict())
            })
        else:
            reply_parts.append("⚠️ 请指定分组字段，例如：\"按地区统计订单金额\"")

    # ── 汇总统计 ──
    elif intent == "aggregation":
        mentioned = [c for c in num_cols if c in question]
        target_cols = mentioned if mentioned else num_cols[:5]
        reply_parts.append("📈 汇总统计：")
        for col in target_cols:
            s = df[col].describe()
            reply_parts.append(f"\n**{col}**：均值={s['mean']:.2f}, 中位数={s['50%']:.2f}, 标准差={s['std']:.2f}, 总和={s['sum']:.2f}")

    # ── 异常值分析 ──
    elif intent == "outlier":
        reply_parts.append("🔍 异常值检测（IQR方法）：")
        for col in num_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower) | (df[col] > upper)]
            if len(outliers) > 0:
                reply_parts.append(f"- **{col}**: {len(outliers)} 个异常值（范围: [{lower:.2f}, {upper:.2f}]，实际: [{df[col].min():.2f}, {df[col].max():.2f}]）")
            else:
                reply_parts.append(f"- **{col}**: 无异常值 ✅")

    # ── 趋势分析 ──
    elif intent == "trend":
        # 寻找日期列
        date_cols = [c for c in df.columns if df[c].dtype == "datetime64[ns]" or "date" in c.lower() or "时间" in c]
        if date_cols:
            date_col = date_cols[0]
            reply_parts.append(f"📈 基于 **{date_col}** 的趋势分析：")
            for col in num_cols[:3]:
                ts = df.groupby(date_col)[col].sum()
                if len(ts) > 1:
                    first_val = ts.iloc[0]
                    last_val = ts.iloc[-1]
                    change = (last_val - first_val) / abs(first_val) * 100 if first_val != 0 else 0
                    direction = "📈 增长" if change > 0 else "📉 下降" if change < 0 else "➡️ 持平"
                    reply_parts.append(f"- **{col}**: {direction} {abs(change):.1f}%（{first_val:.2f} → {last_val:.2f}）")
            charts.append({
                "type": "line",
                "title": "趋势变化",
                "data": _safe_serialize({col: df.groupby(date_col)[col].sum().to_dict() for col in num_cols[:2]})
            })
        else:
            reply_parts.append("⚠️ 未检测到日期/时间字段，无法进行趋势分析。")

    # ── 对比分析 ──
    elif intent == "comparison":
        mentioned = [c for c in df.columns if c in question]
        text_mentioned = [c for c in mentioned if c not in num_cols]
        if text_mentioned:
            group_col = text_mentioned[0]
            num_target = [c for c in num_cols if c in question] or num_cols[:3]
            reply_parts.append(f"📊 **{group_col}** 对比分析：")
            grouped = df.groupby(group_col)[num_target].mean()
            for col in num_target:
                reply_parts.append(f"\n**{col}** 各类别均值：")
                for name, val in grouped[col].sort_values(ascending=False).items():
                    reply_parts.append(f"- {name}: {val:.2f}")
            charts.append({
                "type": "bar",
                "title": f"{group_col} 对比 - {num_target[0]}均值",
                "data": _safe_serialize(grouped[num_target[0]].sort_values(ascending=False).to_dict())
            })
        else:
            reply_parts.append("⚠️ 请指定对比维度，例如：\"各地区销售额对比\"")

    # ── 列分析 ──
    elif intent == "column_analysis":
        mentioned = [c for c in df.columns if c in question]
        for col in mentioned:
            if col in num_cols:
                s = df[col].describe()
                reply_parts.append(f"📊 **{col}** 统计分析：")
                reply_parts.append(f"- 非空值: {int(s['count'])} / {total_rows}")
                reply_parts.append(f"- 均值: {s['mean']:.4f}")
                reply_parts.append(f"- 标准差: {s['std']:.4f}")
                reply_parts.append(f"- 最小值: {s['min']:.4f}")
                reply_parts.append(f"- 25%分位: {s['25%']:.4f}")
                reply_parts.append(f"- 中位数: {s['50%']:.4f}")
                reply_parts.append(f"- 75%分位: {s['75%']:.4f}")
                reply_parts.append(f"- 最大值: {s['max']:.4f}")
            else:
                vc = df[col].value_counts()
                reply_parts.append(f"📊 **{col}** 分析：")
                reply_parts.append(f"- 非空值: {df[col].notna().sum()} / {total_rows}")
                reply_parts.append(f"- 唯一值: {df[col].nunique()}")
                reply_parts.append(f"- 最常见值 Top5：")
                for val, cnt in vc.head(5).items():
                    reply_parts.append(f"  - {val}: {cnt} ({cnt/total_rows*100:.1f}%)")

    # ── 列信息 ──
    elif intent == "column_info":
        mentioned = [c for c in df.columns if c in question]
        for col in mentioned:
            reply_parts.append(f"📋 **{col}**：{df[col].dtype}，非空 {df[col].notna().sum()} 行，唯一值 {df[col].nunique()} 个")

    # ── 描述统计 ──
    elif intent == "descriptive":
        reply_parts.append("📊 描述统计：")
        for col in num_cols[:5]:
            s = df[col].describe()
            reply_parts.append(f"\n**{col}**: 均值={s['mean']:.2f}, 标准差={s['std']:.2f}, 范围=[{s['min']:.2f}, {s['max']:.2f}]")

    # ── 兜底 ──
    else:
        reply_parts.append(f"📋 数据集 **{ds.name}**（{total_rows}行 × {total_cols}列）")
        reply_parts.append(f"\n可用的分析指令：")
        reply_parts.append("- \"数据概览\" - 查看整体情况")
        reply_parts.append("- \"分析XX字段的分布\" - 分布分析")
        reply_parts.append('- "各字段间的相关性" - 相关性分析')
        reply_parts.append('- "按XX统计YY" - 分组统计')
        reply_parts.append('- "XX排名/Top10" - 排名分析')
        reply_parts.append('- "缺失值分析" - 缺失值检测')
        reply_parts.append('- "异常值检测" - 异常值分析')

    reply = "\n".join(reply_parts)

    # 生成reasoning链
    reasoning = [
        f"1. 识别意图: {intent}",
        f"2. 数据集: {ds.name} ({total_rows}×{total_cols})",
        f"3. 分析字段: {', '.join(mentioned if intent in ['column_analysis', 'column_info'] and (mentioned := [c for c in df.columns if c in question]) else num_cols[:4])}",
        f"4. 生成分析结果"
    ]

    return {
        "reply": reply,
        "charts": charts if charts else None,
        "reasoning": reasoning,
        "intent": intent,
    }


# ── Schema ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    dataset_id: int = Field(..., description="数据集ID")
    conversation_id: Optional[int] = Field(None, description="对话ID")


# ── 路由 ──────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """发送AI问答"""
    df, err, ds = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        result = _generate_reply(req.question, df, ds)
        return ApiResponse.ok(data=result)
    except Exception as e:
        return ApiResponse.fail(msg=f"分析失败: {str(e)}")


@router.get("/fields/{dataset_id}")
async def get_fields(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """获取数据集字段列表（供前端侧栏展示）"""
    df, err, ds = await _get_df(db, dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    fields = []
    for col in df.columns:
        fields.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "non_null": int(df[col].notna().sum()),
            "unique": int(df[col].nunique()),
            "sample": str(df[col].dropna().iloc[0]) if len(df) > 0 else None,
        })
    return ApiResponse.ok(data={
        "fields": fields,
        "dataset_name": ds.name,
        "row_count": len(df),
        "col_count": len(df.columns),
    })


@router.post("/auto-explore/{dataset_id}")
async def auto_explore(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """全自动数据探索"""
    df, err, ds = await _get_df(db, dataset_id)
    if err:
        return ApiResponse.fail(msg=err)

    num_cols = _numeric_cols(df)
    total_rows = len(df)
    insights = []
    charts = []

    # 1. 基础信息
    insights.append(f"数据集 {ds.name}：{total_rows}行 × {len(df.columns)}列")

    # 2. 缺失值
    missing = df.isnull().sum()
    total_missing = missing.sum()
    if total_missing > 0:
        missing_cols = missing[missing > 0]
        insights.append(f"发现 {total_missing} 处缺失值，涉及 {len(missing_cols)} 个字段：{', '.join(missing_cols.index.tolist())}")
    else:
        insights.append("数据完整性良好，无缺失值")

    # 3. 重复行
    dup = df.duplicated().sum()
    if dup > 0:
        insights.append(f"存在 {dup} 行重复数据（占比 {dup/total_rows*100:.1f}%）")

    # 4. 数值字段统计
    for col in num_cols[:5]:
        s = df[col].describe()
        skew = df[col].skew()
        kurt = df[col].kurtosis()
        insights.append(f"字段 [{col}]：均值={s['mean']:.2f}, 标准差={s['std']:.2f}, 偏度={skew:.2f}, 峰度={kurt:.2f}")
        if abs(skew) > 2:
            insights.append(f"  ⚠️ {col} 偏度较高（{skew:.2f}），分布可能不对称")

    # 5. 相关性
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        strong = []
        for i in range(len(num_cols)):
            for j in range(i+1, len(num_cols)):
                r = corr.iloc[i, j]
                if abs(r) > 0.6:
                    strong.append(f"{num_cols[i]}↔{num_cols[i+1 if j==i+1 else j]}: r={r:.3f}")
        if strong:
            insights.append(f"强相关关系：{'; '.join(strong)}")

    # 6. 生成图表
    if num_cols:
        charts.append({
            "type": "histogram",
            "title": f"{num_cols[0]} 分布",
            "data": _safe_serialize({"values": df[num_cols[0]].dropna().tolist()[:3000]})
        })
    if len(num_cols) >= 2:
        charts.append({
            "type": "heatmap",
            "title": "相关性矩阵",
            "data": _safe_serialize(corr.to_dict())
        })

    summary = f"已完成对 {ds.name} 的自动探索。共发现 {len(insights)} 项洞察，生成 {len(charts)} 张图表。"

    return ApiResponse.ok(data={
        "insights": insights,
        "charts": charts,
        "summary": summary,
    })


# 对话记录接口（MVP阶段内存存储）
_conversations = {}
_conv_id_counter = [0]


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """对话记录列表"""
    items = []
    for cid, conv in _conversations.items():
        items.append({
            "id": cid,
            "title": conv.get("title", "新对话"),
            "created_at": conv.get("created_at", ""),
            "message_count": len(conv.get("messages", [])),
        })
    items.sort(key=lambda x: x["id"], reverse=True)
    return ApiResponse.ok(data={"total": len(items), "items": items[:20]})


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """对话详情"""
    conv = _conversations.get(conversation_id)
    if not conv:
        return ApiResponse.fail(msg="对话不存在")
    return ApiResponse.ok(data={"messages": conv.get("messages", [])})


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """删除对话"""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
    return ApiResponse.ok(message="删除成功")
