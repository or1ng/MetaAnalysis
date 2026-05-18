"""
报告生成API
MVP阶段：基于pandas分析生成HTML报告
"""
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from models import get_db
from models.dataset import Dataset
from parser.file_parser import read_file
from utils.response import ApiResponse

router = APIRouter(prefix="/api/report", tags=["报告生成"])


def _safe(data):
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
    import re
    numeric_cols, text_cols, date_cols = [], [], []
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


def _generate_html_report(df, ds, template="business", include_charts=True, include_stats=True, include_suggestions=True):
    """生成HTML报告 - 三种模板差异化"""
    import re
    num_cols, text_cols, date_cols = _classify_columns(df)
    total_rows = len(df)
    total_cols = len(df.columns)
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    missing_total = int(df.isnull().sum().sum())
    dup_total = int(df.duplicated().sum())

    # 预计算公共数据
    outlier_info = {}
    for col in num_cols[:8]:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        IQR = Q3 - Q1
        mask = (s < Q1 - 1.5 * IQR) | (s > Q3 + 1.5 * IQR)
        outlier_info[col] = {
            "count": int(mask.sum()),
            "min": float(s.min()),
            "max": float(s.max()),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "std": float(s.std()),
            "skew": float(s.skew()),
            "kurtosis": float(s.kurtosis()),
            "Q1": float(Q1),
            "Q3": float(Q3),
        }

    corr_matrix = None
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr()

    # ── 按模板生成 ──
    if template == "business":
        return _gen_business(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                             missing_total, dup_total, outlier_info, corr_matrix, now,
                             include_charts, include_stats, include_suggestions)
    elif template == "academic":
        return _gen_academic(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                             missing_total, dup_total, outlier_info, corr_matrix, now,
                             include_charts, include_stats, include_suggestions)
    else:
        return _gen_simple(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                           missing_total, dup_total, outlier_info, corr_matrix, now,
                           include_stats, include_suggestions)


# ═══════════════════════════════════════════════════════════
# 商务汇报模板：侧重业务洞察、排名、占比、行动建议
# ═══════════════════════════════════════════════════════════
_CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _gen_business(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                  missing_total, dup_total, outlier_info, corr_matrix, now,
                  include_charts, include_stats, include_suggestions):

    style = """
    <style>
        body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 40px 60px; color: #2c3e50; line-height: 1.8; }
        .cover { text-align: center; padding: 60px 0 30px; border-bottom: 3px solid #2980b9; margin-bottom: 36px; }
        .cover h1 { font-size: 30px; color: #2c3e50; margin-bottom: 8px; }
        .cover .subtitle { color: #7f8c8d; font-size: 14px; margin: 4px 0; }
        h2 { color: #2980b9; border-left: 4px solid #2980b9; padding-left: 12px; margin: 36px 0 16px; font-size: 20px; }
        h3 { color: #34495e; margin: 20px 0 10px; font-size: 16px; }
        .kpi-row { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0; }
        .kpi-card { background: linear-gradient(135deg, #2980b9, #3498db); color: #fff; padding: 16px 24px; border-radius: 8px; min-width: 120px; text-align: center; }
        .kpi-card .kpi-value { font-size: 28px; font-weight: 700; }
        .kpi-card .kpi-label { font-size: 12px; opacity: 0.85; }
        .kpi-card.green { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .kpi-card.orange { background: linear-gradient(135deg, #e67e22, #f39c12); }
        .kpi-card.red { background: linear-gradient(135deg, #c0392b, #e74c3c); }
        table { width: 100%; border-collapse: collapse; margin: 14px 0; }
        th { background: #3498db; color: #fff; padding: 10px 12px; text-align: left; font-weight: 500; }
        td { padding: 8px 12px; border: 1px solid #ecf0f1; }
        tr:nth-child(even) { background: #f8f9fa; }
        .insight { background: #eaf2f8; border-left: 3px solid #2980b9; padding: 12px 16px; margin: 10px 0; border-radius: 0 6px 6px 0; }
        .warning { background: #fdedec; border-left: 3px solid #e74c3c; padding: 12px 16px; margin: 10px 0; border-radius: 0 6px 6px 0; }
        .success { background: #eafaf1; border-left: 3px solid #27ae60; padding: 12px 16px; margin: 10px 0; border-radius: 0 6px 6px 0; }
        .rank-bar { height: 18px; background: linear-gradient(90deg, #3498db, #2980b9); border-radius: 9px; margin: 2px 0; transition: width 0.3s; }
        .action-item { background: #fef9e7; border-left: 3px solid #f39c12; padding: 10px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; }
        ul { padding-left: 20px; }
        li { margin: 6px 0; }
    </style>
    """
    h = [f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>商务汇报分析报告</title>{style}</head><body>']

    # 封面
    h.append(f'<div class="cover"><h1>商务汇报分析报告</h1>')
    h.append(f'<p class="subtitle">数据集：{ds.name}</p>')
    h.append(f'<p class="subtitle">报告周期：{now}</p>')
    h.append(f'<p class="subtitle">MetaAnalysis元析智能</p></div>')

    # 动态章节编号
    sec = [0]

    def section(title):
        sec[0] += 1
        num = _CN_NUM[sec[0] - 1] if sec[0] <= len(_CN_NUM) else str(sec[0])
        h.append(f'<h2>{num}、{title}</h2>')

    # 核心KPI
    section("核心指标概览")
    h.append('<div class="kpi-row">')
    h.append(f'<div class="kpi-card"><div class="kpi-value">{total_rows:,}</div><div class="kpi-label">总记录数</div></div>')
    h.append(f'<div class="kpi-card green"><div class="kpi-value">{total_cols}</div><div class="kpi-label">分析维度</div></div>')
    if num_cols:
        h.append(f'<div class="kpi-card orange"><div class="kpi-value">{outlier_info.get(num_cols[0], {}).get("count", 0)}</div><div class="kpi-label">{num_cols[0]}异常</div></div>')
    h.append(f'<div class="kpi-card {("red" if missing_total > 0 else "green")}"><div class="kpi-value">{missing_total:,}</div><div class="kpi-label">缺失值</div></div>')
    h.append('</div>')

    # 维度排名分析
    if text_cols and num_cols:
        section("维度排名分析")
        metric_col = num_cols[0]
        for g_col in text_cols[:3]:
            grouped = df.groupby(g_col)[metric_col].agg(["sum", "mean", "count"]).sort_values("sum", ascending=False)
            if len(grouped) <= 1:
                continue
            total_val = grouped["sum"].sum()
            h.append(f'<h3>按「{g_col}」维度 - {metric_col}汇总排名</h3>')
            h.append('<table><tr><th>排名</th><th>维度</th><th>汇总值</th><th>均值</th><th>记录数</th><th>占比</th><th>分布</th></tr>')
            for rank, (name, row) in enumerate(grouped.head(10).iterrows(), 1):
                pct = row["sum"] / total_val * 100 if total_val else 0
                h.append(f'<tr><td>{rank}</td><td><b>{name}</b></td><td>{row["sum"]:,.2f}</td><td>{row["mean"]:,.2f}</td><td>{row["count"]:,}</td><td>{pct:.1f}%</td><td><div class="rank-bar" style="width:{min(pct, 100)}%"></div></td></tr>')
            h.append('</table>')
            top3_pct = grouped.head(3)["sum"].sum() / total_val * 100 if total_val else 0
            h.append(f'<div class="insight">Top 3 占比 {top3_pct:.1f}%，{"集中度较高" if top3_pct > 60 else "分布相对均匀"}。</div>')

    # 数据质量评估
    section("数据质量评估")
    quality_score = 100
    if missing_total > 0:
        quality_score -= min(30, missing_total / total_rows * 100) if total_rows else 30
    if dup_total > 0:
        quality_score -= min(20, dup_total / total_rows * 100) if total_rows else 20
    outlier_total = sum(v["count"] for v in outlier_info.values())
    if outlier_total > 0:
        quality_score -= min(15, outlier_total / total_rows * 100) if total_rows else 15
    quality_score = max(0, quality_score)
    score_color = "#27ae60" if quality_score >= 80 else "#f39c12" if quality_score >= 60 else "#e74c3c"
    h.append(f'<div style="font-size:18px;margin:12px 0;">数据质量评分：<b style="color:{score_color};font-size:24px;">{quality_score:.0f}</b>/100</div>')

    if missing_total > 0:
        missing_cols = df.isnull().sum()[df.isnull().sum() > 0]
        h.append(f'<div class="warning">缺失值：共 {missing_total:,} 处，涉及 {", ".join(missing_cols.index[:5].tolist())}</div>')
    if dup_total > 0:
        h.append(f'<div class="warning">重复记录：共 {dup_total} 条</div>')
    if outlier_total > 0:
        outlier_names = [k for k, v in outlier_info.items() if v["count"] > 0]
        h.append(f'<div class="warning">异常值：{", ".join(outlier_names[:5])} 共 {outlier_total} 个数据点超出IQR范围</div>')
    if missing_total == 0 and dup_total == 0 and outlier_total == 0:
        h.append('<div class="success">数据质量优秀，无缺失值、无重复记录、无显著异常值。</div>')

    # 关键指标分布（受 include_charts 控制）
    if include_charts and num_cols:
        section("关键指标分布")
        h.append('<table><tr><th>指标</th><th>均值</th><th>中位数</th><th>标准差</th><th>最小值</th><th>最大值</th><th>变异系数</th></tr>')
        for col in num_cols[:8]:
            info = outlier_info.get(col, {})
            if not info:
                continue
            cv = info["std"] / info["mean"] * 100 if info["mean"] != 0 else 0
            cv_tag = "高波动" if cv > 50 else "中等" if cv > 25 else "稳定"
            h.append(f'<tr><td><b>{col}</b></td><td>{info["mean"]:,.2f}</td><td>{info["median"]:,.2f}</td><td>{info["std"]:,.2f}</td><td>{info["min"]:,.2f}</td><td>{info["max"]:,.2f}</td><td>{cv:.1f}% ({cv_tag})</td></tr>')
        h.append('</table>')

    # 业务关联分析（受 include_stats 控制，需要相关矩阵）
    if include_stats and corr_matrix is not None:
        strong = []
        n = len(num_cols)
        for i in range(min(n, 8)):
            for j in range(i + 1, min(n, 8)):
                r = corr_matrix.iloc[i, j]
                if abs(r) > 0.5:
                    strength = "强" if abs(r) > 0.8 else "中等"
                    direction = "正" if r > 0 else "负"
                    strong.append(f"<b>{num_cols[i]}</b> 与 <b>{num_cols[j]}</b> {direction}相关（r={r:.3f}，{strength}相关）")
        if strong:
            section("业务关联分析")
            for s in strong[:6]:
                h.append(f'<div class="insight">{s}</div>')

    # 行动建议（受 include_suggestions 控制）
    if include_suggestions:
        section("行动建议")
        actions = []
        if missing_total > 0:
            actions.append(f"对缺失值字段进行填充处理（均值/中位数/插值），预计可提升分析覆盖率 {(missing_total / (total_rows * total_cols) * 100):.1f}%")
        if dup_total > 0:
            actions.append("排查并清理重复记录，避免统计口径偏差")
        outlier_cols = [k for k, v in outlier_info.items() if v["count"] > 0]
        if outlier_cols:
            actions.append(f"对 {', '.join(outlier_cols[:3])} 的异常值进行业务核实，区分真实异常与数据录入错误")
        if text_cols and num_cols:
            g = text_cols[0]
            m = num_cols[0]
            grp = df.groupby(g)[m].sum().sort_values(ascending=False)
            if len(grp) > 1:
                actions.append(f"关注「{grp.index[-1]}」维度表现（{m}仅为头部「{grp.index[0]}」的 {grp.iloc[-1] / grp.iloc[0] * 100:.1f}%），建议分析原因并制定提升策略")
        if corr_matrix is not None and len(num_cols) > 1:
            for i in range(min(len(num_cols) - 1, 3)):
                r = corr_matrix.iloc[i, i + 1]
                if abs(r) > 0.7:
                    actions.append(f"利用 {num_cols[i]} 与 {num_cols[i + 1]} 的高度关联性，可考虑合并指标或构建综合评分")
                    break
        if not actions:
            actions.append("数据质量良好，建议进入深度分析阶段，使用统计分析模块进行假设检验")
        for a in actions:
            h.append(f'<div class="action-item">• {a}</div>')

    h.append('</body></html>')
    return '\n'.join(h)


# ═══════════════════════════════════════════════════════════
# 学术论文模板：侧重统计方法、分布检验、严谨表述
# ═══════════════════════════════════════════════════════════
def _gen_academic(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                  missing_total, dup_total, outlier_info, corr_matrix, now,
                  include_charts, include_stats, include_suggestions):

    style = """
    <style>
        body { font-family: 'Times New Roman', 'SimSun', serif; margin: 50px 70px; color: #333; line-height: 2; }
        .cover { text-align: center; padding: 60px 0 30px; border-bottom: 1px solid #333; margin-bottom: 40px; }
        .cover h1 { font-size: 26px; color: #1a1a1a; margin-bottom: 6px; }
        .cover .subtitle { color: #666; font-size: 13px; margin: 3px 0; }
        h2 { color: #333; border-bottom: 1px solid #ccc; padding-bottom: 6px; margin: 36px 0 14px; font-size: 18px; }
        h3 { color: #444; margin: 20px 0 10px; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 13px; }
        th { background: #e8e8e8; border: 1px solid #999; padding: 8px 10px; font-weight: 600; }
        td { border: 1px solid #ccc; padding: 6px 10px; }
        .note { background: #f5f5f5; border: 1px solid #ddd; padding: 10px 14px; margin: 10px 0; font-size: 13px; border-radius: 2px; }
        .finding { background: #fafafa; border-left: 3px solid #666; padding: 10px 14px; margin: 10px 0; font-size: 13px; }
        .sig-high { color: #c0392b; font-weight: 600; }
        .sig-mid { color: #e67e22; font-weight: 600; }
        ul, ol { padding-left: 24px; }
        li { margin: 5px 0; }
        .formula { font-family: 'Courier New', monospace; background: #f9f9f9; padding: 2px 6px; border-radius: 2px; }
    </style>
    """
    h = [f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>学术研究报告</title>{style}</head><body>']

    # 封面
    h.append('<div class="cover">')
    h.append('<h1>数据分析研究报告</h1>')
    h.append(f'<p class="subtitle">数据来源：{ds.name}</p>')
    h.append(f'<p class="subtitle">分析日期：{now}</p>')
    h.append(f'<p class="subtitle">工具：MetaAnalysis元析智能</p></div>')

    # 动态章节编号
    sec = [0]
    sub = [0]

    def section(title):
        sec[0] += 1
        sub[0] = 0
        h.append(f'<h2>{sec[0]}. {title}</h2>')

    def subsection(title):
        sub[0] += 1
        h.append(f'<h3>{sec[0]}.{sub[0]} {title}</h3>')

    # 1. 研究数据描述
    section("研究数据描述")
    h.append(f'<p>本研究基于「{ds.name}」数据集进行分析，该数据集共包含 <b>{total_rows:,}</b> 条观测记录和 <b>{total_cols}</b> 个变量。')
    h.append(f'其中数值型变量 {len(num_cols)} 个，分类型变量 {len(text_cols)} 个，日期型变量 {len(date_cols)} 个。</p>')
    h.append('<div class="note">')
    h.append(f'数据完整性：缺失值 {missing_total:,} 处（占比 {missing_total / (total_rows * total_cols) * 100:.2f}%），重复记录 {dup_total} 条。')
    if missing_total > 0:
        h.append(f'缺失值涉及变量：{", ".join(df.isnull().sum()[df.isnull().sum() > 0].index.tolist())}。')
    h.append('</div>')

    # 变量清单
    subsection("变量定义")
    h.append('<table><tr><th>变量名</th><th>类型</th><th>非空计数</th><th>唯一值数</th><th>样本值</th></tr>')
    for col in df.columns:
        dtype = "数值型(连续)" if col in num_cols else "日期型" if col in date_cols else "分类型"
        sample = str(df[col].dropna().iloc[0]) if len(df) > 0 else "-"
        h.append(f'<tr><td><i>{col}</i></td><td>{dtype}</td><td>{df[col].notna().sum()}</td><td>{df[col].nunique()}</td><td>{sample[:30]}</td></tr>')
    h.append('</table>')

    # 2. 描述性统计
    if include_stats and num_cols:
        section("描述性统计分析")
        subsection("集中趋势与离散程度")
        h.append('<table><tr><th>变量</th><th>均值</th><th>标准误</th><th>中位数</th><th>标准差</th><th>最小值</th><th>最大值</th><th>偏度</th><th>峰度</th></tr>')
        for col in num_cols[:10]:
            info = outlier_info.get(col, {})
            if not info:
                continue
            se = info["std"] / (total_rows ** 0.5) if total_rows > 0 else 0
            skew_note = "右偏" if info["skew"] > 1 else "左偏" if info["skew"] < -1 else "近似对称"
            kurt_note = "尖峰" if info["kurtosis"] > 3 else "平坦" if info["kurtosis"] < -1 else "近似正态"
            h.append(f'<tr><td><i>{col}</i></td><td>{info["mean"]:.4f}</td><td>{se:.4f}</td><td>{info["median"]:.4f}</td><td>{info["std"]:.4f}</td><td>{info["min"]:.4f}</td><td>{info["max"]:.4f}</td><td>{info["skew"]:.3f}({skew_note})</td><td>{info["kurtosis"]:.3f}({kurt_note})</td></tr>')
        h.append('</table>')
        h.append('<div class="note">注：偏度 > 0 表示右偏分布；峰度 > 3 表示尖峰分布（相较于正态分布）。</div>')

        # 正态性检验
        subsection("分布正态性评估")
        h.append('<table><tr><th>变量</th><th>偏度</th><th>峰度</th><th>IQR范围</th><th>异常值数</th><th>正态性判断</th></tr>')
        for col in num_cols[:10]:
            info = outlier_info.get(col, {})
            if not info:
                continue
            skew = info["skew"]
            kurt = info["kurtosis"]
            oc = info["count"]
            normal = (abs(skew) < 2 and abs(kurt) < 7)
            judge = "近似正态" if normal else "非正态分布"
            judge_cls = "" if normal else " class=\"sig-mid\""
            h.append(f'<tr><td><i>{col}</i></td><td>{skew:.3f}</td><td>{kurt:.3f}</td><td>[{info["Q1"]:.2f}, {info["Q3"]:.2f}]</td><td>{oc}</td><td{judge_cls}>{judge}</td></tr>')
        h.append('</table>')

    # 3. 相关性分析
    if include_stats and corr_matrix is not None:
        section("相关性分析")
        subsection("Pearson相关系数矩阵")
        n = min(len(num_cols), 8)
        h.append('<table><tr><th></th>')
        for col in num_cols[:n]:
            h.append(f'<th>{col}</th>')
        h.append('</tr>')
        for i in range(n):
            h.append(f'<tr><td><i>{num_cols[i]}</i></td>')
            for j in range(n):
                r = corr_matrix.iloc[i, j]
                if abs(r) > 0.8:
                    cls = ' class="sig-high"'
                elif abs(r) > 0.6:
                    cls = ' class="sig-mid"'
                else:
                    cls = ''
                h.append(f'<td{cls}>{r:.4f}</td>')
            h.append('</tr>')
        h.append('</table>')

        # 显著相关对
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                r = corr_matrix.iloc[i, j]
                if abs(r) > 0.5:
                    pairs.append((num_cols[i], num_cols[j], r))
        if pairs:
            subsection("显著相关关系（|r| > 0.5）")
            h.append('<table><tr><th>变量对</th><th>相关系数(r)</th><th>决定系数(R²)</th><th>相关强度</th></tr>')
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            for c1, c2, r in pairs[:8]:
                r2 = r ** 2
                strength = "强相关" if abs(r) > 0.8 else "中等相关" if abs(r) > 0.6 else "弱相关"
                h.append(f'<tr><td><i>{c1}</i> ↔ <i>{c2}</i></td><td>{r:.4f}</td><td>{r2:.4f}</td><td>{strength}</td></tr>')
            h.append('</table>')

    # 4. 异常值分析
    if outlier_info:
        section("异常值检测")
        h.append('<p>采用四分位距法（IQR）进行异常值检测，定义异常值为小于 <span class="formula">Q1 - 1.5×IQR</span> 或大于 <span class="formula">Q3 + 1.5×IQR</span> 的观测值。</p>')
        h.append('<table><tr><th>变量</th><th>Q1</th><th>Q3</th><th>IQR</th><th>下界</th><th>上界</th><th>异常值数</th><th>异常率</th></tr>')
        for col, info in outlier_info.items():
            iqr = info["Q3"] - info["Q1"]
            lower = info["Q1"] - 1.5 * iqr
            upper = info["Q3"] + 1.5 * iqr
            rate = info["count"] / total_rows * 100 if total_rows else 0
            h.append(f'<tr><td><i>{col}</i></td><td>{info["Q1"]:.2f}</td><td>{info["Q3"]:.2f}</td><td>{iqr:.2f}</td><td>{lower:.2f}</td><td>{upper:.2f}</td><td>{info["count"]}</td><td>{rate:.2f}%</td></tr>')
        h.append('</table>')

    # 5. 研究结论与建议
    if include_suggestions:
        section("研究结论与建议")
        h.append('<ol>')
        non_normal = [c for c, info in outlier_info.items() if abs(info["skew"]) >= 2 or abs(info["kurtosis"]) >= 7]
        if non_normal:
            h.append(f'<li>变量 {", ".join(non_normal[:5])} 的分布偏离正态，后续参数检验（如t检验、ANOVA）需谨慎，建议采用非参数方法（Mann-Whitney U、Kruskal-Wallis）或进行适当变换。</li>')
        if missing_total > 0:
            h.append(f'<li>数据集存在 {missing_total:,} 处缺失值，建议报告缺失机制（MCAR/MAR/MNAR），并根据机制选择合适处理方法（列表删除、多重插补等）。</li>')
        if dup_total > 0:
            h.append(f'<li>检测到 {dup_total} 条完全重复记录，建议在分析前进行去重处理，避免对统计推断产生偏差。</li>')
        if corr_matrix is not None:
            high_corr = []
            for i in range(min(len(num_cols), 6)):
                for j in range(i + 1, min(len(num_cols), 6)):
                    if abs(corr_matrix.iloc[i, j]) > 0.8:
                        high_corr.append((num_cols[i], num_cols[j]))
            if high_corr:
                h.append(f'<li>变量对 {", ".join([f"({a}, {b})" for a, b in high_corr[:3]])} 存在高度共线性（|r|>0.8），在回归分析中可能导致多重共线性问题，建议考虑方差膨胀因子（VIF）诊断或变量选择。</li>')
        h.append('<li>建议进一步使用统计检验（正态性检验Shapiro-Wilk、方差齐性检验Levene）和回归建模进行深入分析。</li>')
        h.append('</ol>')

    h.append('</body></html>')
    return '\n'.join(h)


# ═══════════════════════════════════════════════════════════
# 简约分析模板：精简、一页看懂
# ═══════════════════════════════════════════════════════════
def _gen_simple(df, ds, num_cols, text_cols, date_cols, total_rows, total_cols,
                missing_total, dup_total, outlier_info, corr_matrix, now,
                include_stats, include_suggestions):

    style = """
    <style>
        body { font-family: -apple-system, 'PingFang SC', sans-serif; margin: 30px; color: #444; line-height: 1.7; max-width: 800px; }
        .header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #2ecc71; padding-bottom: 12px; margin-bottom: 20px; }
        .header h1 { font-size: 22px; color: #2c3e50; margin: 0; }
        .header .meta { font-size: 12px; color: #999; }
        .section { margin: 20px 0; }
        .section-title { font-size: 15px; font-weight: 700; color: #2ecc71; margin-bottom: 10px; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin: 10px 0; }
        .stat-item { background: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; }
        .stat-item .val { font-size: 20px; font-weight: 700; color: #2c3e50; }
        .stat-item .lbl { font-size: 11px; color: #999; }
        .bullet { padding: 6px 0; padding-left: 16px; position: relative; }
        .bullet::before { content: ""; position: absolute; left: 0; top: 12px; width: 6px; height: 6px; background: #2ecc71; border-radius: 50%; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }
        th { background: #2ecc71; color: #fff; padding: 8px 10px; text-align: left; }
        td { padding: 6px 10px; border-bottom: 1px solid #eee; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
        .tag-green { background: #d5f5e3; color: #27ae60; }
        .tag-red { background: #fadbd8; color: #e74c3c; }
        .tag-yellow { background: #fef9e7; color: #f39c12; }
    </style>
    """
    h = [f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>数据简报</title>{style}</head><body>']

    # 头部
    h.append(f'<div class="header"><h1>📊 {ds.name} - 数据简报</h1><span class="meta">{now}</span></div>')

    # 核心指标
    h.append('<div class="section"><div class="section-title">核心指标</div>')
    h.append('<div class="stat-grid">')
    h.append(f'<div class="stat-item"><div class="val">{total_rows:,}</div><div class="lbl">总记录</div></div>')
    h.append(f'<div class="stat-item"><div class="val">{total_cols}</div><div class="lbl">字段数</div></div>')
    quality = "优秀" if (missing_total == 0 and dup_total == 0) else "需关注"
    q_cls = "tag-green" if quality == "优秀" else "tag-red"
    h.append(f'<div class="stat-item"><div class="val"><span class="tag {q_cls}">{quality}</span></div><div class="lbl">数据质量</div></div>')
    if num_cols:
        h.append(f'<div class="stat-item"><div class="val">{len(num_cols)}</div><div class="lbl">数值字段</div></div>')
    if text_cols:
        h.append(f'<div class="stat-item"><div class="val">{len(text_cols)}</div><div class="lbl">分类字段</div></div>')
    h.append('</div></div>')

    # 关键发现（精简）
    h.append('<div class="section"><div class="section-title">关键发现</div>')
    if missing_total > 0:
        h.append(f'<div class="bullet">缺失值 {missing_total:,} 处，需处理</div>')
    if dup_total > 0:
        h.append(f'<div class="bullet">重复记录 {dup_total} 条</div>')
    outlier_total = sum(v["count"] for v in outlier_info.values())
    if outlier_total > 0:
        outlier_names = [k for k, v in outlier_info.items() if v["count"] > 0]
        h.append(f'<div class="bullet">{", ".join(outlier_names[:3])} 存在异常值（共 {outlier_total} 个）</div>')
    if missing_total == 0 and dup_total == 0 and outlier_total == 0:
        h.append('<div class="bullet">数据质量优秀，无缺失/重复/异常</div>')

    # Top 洞察
    if text_cols and num_cols:
        grp = df.groupby(text_cols[0])[num_cols[0]].sum().sort_values(ascending=False)
        if len(grp) > 0:
            top = grp.index[0]
            top_pct = grp.iloc[0] / grp.sum() * 100 if grp.sum() else 0
            h.append(f'<div class="bullet">「{text_cols[0]}」维度中，「{top}」的{num_cols[0]}占比最高（{top_pct:.1f}%）</div>')
    h.append('</div>')

    # 指标速览
    if include_stats and num_cols:
        h.append('<div class="section"><div class="section-title">指标速览</div>')
        h.append('<table><tr><th>指标</th><th>均值</th><th>中位数</th><th>标准差</th><th>范围</th></tr>')
        for col in num_cols[:6]:
            info = outlier_info.get(col, {})
            if not info:
                continue
            h.append(f'<tr><td><b>{col}</b></td><td>{info["mean"]:,.2f}</td><td>{info["median"]:,.2f}</td><td>{info["std"]:,.2f}</td><td>{info["min"]:,.2f} ~ {info["max"]:,.2f}</td></tr>')
        h.append('</table></div>')

    # 相关性速览
    if corr_matrix is not None and len(num_cols) >= 2:
        strong = []
        n = min(len(num_cols), 6)
        for i in range(n):
            for j in range(i + 1, n):
                r = corr_matrix.iloc[i, j]
                if abs(r) > 0.6:
                    strong.append(f"{num_cols[i]} ↔ {num_cols[j]} (r={r:.2f})")
        if strong:
            h.append('<div class="section"><div class="section-title">显著关联</div>')
            for s in strong[:4]:
                h.append(f'<div class="bullet">{s}</div>')
            h.append('</div>')

    # 建议
    if include_suggestions:
        h.append('<div class="section"><div class="section-title">下一步建议</div>')
        if missing_total > 0:
            h.append('<div class="bullet">处理缺失值后重新分析</div>')
        outlier_cols = [k for k, v in outlier_info.items() if v["count"] > 0]
        if outlier_cols:
            h.append(f'<div class="bullet">核实 {", ".join(outlier_cols[:3])} 异常值</div>')
        h.append('<div class="bullet">使用统计分析模块深入检验</div>')
        h.append('<div class="bullet">使用AI问答模块探索更多问题</div>')
        h.append('</div>')

    h.append('</body></html>')
    return '\n'.join(h)


# ── Schema ──────────────────────────────────────────────

class ReportGenerateReq(BaseModel):
    dataset_id: int = Field(..., description="数据集ID")
    template: str = Field("business", description="报告模板: business/academic/simple")
    include_charts: bool = Field(True, description="包含图表")
    include_stats: bool = Field(True, description="包含统计结论")
    include_suggestions: bool = Field(True, description="包含建议")


# ── 路由 ──────────────────────────────────────────────

# 内存存储报告
_reports = {}
_report_counter = [0]


@router.post("/generate")
async def generate_report(req: ReportGenerateReq, db: AsyncSession = Depends(get_db)):
    """生成报告"""
    df, err, ds = await _get_df(db, req.dataset_id)
    if err:
        return ApiResponse.fail(msg=err)
    try:
        html_content = _generate_html_report(df, ds, req.template, req.include_charts, req.include_stats, req.include_suggestions)
        _report_counter[0] += 1
        report_id = _report_counter[0]
        _reports[report_id] = {
            "id": report_id,
            "dataset_id": req.dataset_id,
            "dataset_name": ds.name,
            "template": req.template,
            "html": html_content,
            "created_at": pd.Timestamp.now().isoformat(),
        }
        return ApiResponse.ok(data={
            "report_id": report_id,
            "status": "done",
            "message": "报告生成成功",
        })
    except Exception as e:
        return ApiResponse.fail(msg=f"报告生成失败: {str(e)}")


@router.get("/list")
async def list_reports(db: AsyncSession = Depends(get_db)):
    """报告列表"""
    items = []
    for rid, rpt in _reports.items():
        items.append({
            "id": rpt["id"],
            "dataset_name": rpt["dataset_name"],
            "template": rpt["template"],
            "created_at": rpt["created_at"],
        })
    items.sort(key=lambda x: x["id"], reverse=True)
    return ApiResponse.ok(data={"total": len(items), "items": items[:20]})


@router.get("/{report_id}")
async def get_report(report_id: int):
    """报告详情"""
    rpt = _reports.get(report_id)
    if not rpt:
        return ApiResponse.fail(msg="报告不存在")
    return ApiResponse.ok(data={"id": rpt["id"], "dataset_name": rpt["dataset_name"], "template": rpt["template"], "created_at": rpt["created_at"]})


@router.get("/{report_id}/preview")
async def preview_report(report_id: int):
    """报告预览（返回HTML）"""
    rpt = _reports.get(report_id)
    if not rpt:
        return ApiResponse.fail(msg="报告不存在")
    return ApiResponse.ok(data={"content_html": rpt["html"]})


@router.get("/{report_id}/download")
async def download_report(report_id: int):
    """下载报告HTML"""
    from fastapi.responses import Response
    rpt = _reports.get(report_id)
    if not rpt:
        return ApiResponse.fail(msg="报告不存在")
    return Response(
        content=rpt["html"],
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.html"}
    )


@router.delete("/{report_id}")
async def delete_report(report_id: int):
    """删除报告"""
    if report_id in _reports:
        del _reports[report_id]
    return ApiResponse.ok(message="删除成功")
