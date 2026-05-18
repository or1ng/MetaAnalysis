"""
MetaAnalysis 统计算法引擎
支持：描述统计、假设检验（t检验/卡方/ANOVA/正态性）、相关分析、回归分析、时序分析、聚类分析
"""
import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Any


class StatisticEngine:
    """统计算法引擎核心"""

    # ── 描述统计 ──────────────────────────────────────────────
    @staticmethod
    def descriptive(df: pd.DataFrame, columns: list | None = None,
                    confidence: float = 0.95) -> dict:
        """
        描述统计分析
        columns: 要分析的字段列表（None=全部数值列）
        confidence: 置信水平
        返回: summary_table, normality_test, interpretation
        """
        if columns:
            cols = [c for c in columns if c in df.columns]
        else:
            cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not cols:
            return {"summary_table": [], "normality_test": [], "interpretation": ""}

        alpha = 1 - confidence
        summary_rows = []
        normality_rows = []
        interpretations = []

        for col in cols:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) < 3:
                continue

            n = len(series)
            mean = float(series.mean())
            median = float(series.median())
            std = float(series.std(ddof=1)) if n > 1 else 0.0
            var = float(series.var(ddof=1)) if n > 1 else 0.0
            min_v = float(series.min())
            max_v = float(series.max())
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            skew = float(series.skew())
            kurt = float(series.kurtosis())
            se = std / np.sqrt(n)
            cv = (std / mean * 100) if mean != 0 else 0.0
            ci_low = float(mean - sp_stats.t.ppf(1 - alpha / 2, n - 1) * se)
            ci_high = float(mean + sp_stats.t.ppf(1 - alpha / 2, n - 1) * se)

            summary_rows.append({
                "field": col, "n": n,
                "mean": _r(mean), "median": _r(median), "std": _r(std), "var": _r(var),
                "min": _r(min_v), "max": _r(max_v),
                "q1": _r(q1), "q3": _r(q3), "iqr": _r(iqr),
                "skew": _r(skew), "kurtosis": _r(kurt),
                "cv_percent": _r(cv), "se": _r(se),
                "ci_low": _r(ci_low), "ci_high": _r(ci_high),
            })

            # 正态性检验 (Shapiro-Wilk, 样本<=5000)
            if 3 <= n <= 5000:
                if n > 50:
                    _, p_norm = sp_stats.kstest(series, "norm", args=(mean, std))
                    test_name = "Kolmogorov-Smirnov"
                    w_stat = None
                else:
                    stat_sw, p_norm = sp_stats.shapiro(series)
                    test_name = "Shapiro-Wilk"
                    w_stat = _r(stat_sw)
            else:
                test_name = " skipped (>5000)"
                p_norm = None
                w_stat = None

            is_normal = p_norm is not None and p_norm > alpha
            normality_rows.append({
                "field": col, "test": test_name,
                "statistic": w_stat, "p_value": _r(p_norm) if p_norm is not None else None,
                "is_normal": is_normal,
            })

            # 自动解读
            interp_parts = [f"**{col}**：均值{_r(mean)}，标准差{_r(std)}，样本量{n}。"]
            if abs(skew) > 1:
                direction = "右偏" if skew > 0 else "左偏"
                interp_parts.append(f"分布明显{direction}（偏度={_r(skew)}），不服从正态分布。")
            elif abs(skew) > 0.5:
                direction = "右偏" if skew > 0 else "左偏"
                interp_parts.append(f"分布轻微{direction}（偏度={_r(skew)}）。")
            if kurt > 3:
                interp_parts.append(f"峰度={_r(kurt)}（>3），存在尖峰厚尾特征。")
            if cv > 100:
                interp_parts.append(f"变异系数={_r(cv)}%，数据离散程度极高。")
            elif cv > 50:
                interp_parts.append(f"变异系数={_r(cv)}%，数据离散程度较高。")
            interpretations.append(" ".join(interp_parts))

        return {
            "summary_table": summary_rows,
            "normality_test": normality_rows,
            "interpretation": "\n".join(interpretations),
        }

    # ── 假设检验 ──────────────────────────────────────────────
    @staticmethod
    def hypothesis(df: pd.DataFrame, params: dict) -> dict:
        """
        假设检验统一入口
        params: {method, group_col, value_col, group_a, group_b, expected_freq, alpha}
        """
        method = params.get("method", "ttest_independent")
        alpha = params.get("alpha", 0.05)
        result = {"method": method, "alpha": alpha, "results": []}

        if method == "ttest_independent":
            result = StatisticEngine._ttest_independent(df, params, alpha)
        elif method == "ttest_paired":
            result = StatisticEngine._ttest_paired(df, params, alpha)
        elif method == "chi2_test":
            result = StatisticEngine._chi2_test(df, params, alpha)
        elif method == "anova":
            result = StatisticEngine._anova(df, params, alpha)
        elif method == "normality":
            result = StatisticEngine._normality_test(df, params, alpha)
        else:
            result["error"] = f"不支持的检验方法: {method}"

        return result

    @staticmethod
    def _ttest_independent(df, params, alpha):
        """独立样本t检验"""
        group_col = params.get("group_col", "")
        value_col = params.get("value_col", "")
        group_a = params.get("group_a", "")
        group_b = params.get("group_b", "")

        grp_a = pd.to_numeric(df[df[group_col] == group_a][value_col], errors="coerce").dropna()
        grp_b = pd.to_numeric(df[df[group_col] == group_b][value_col], errors="coerce").dropna()

        t_stat, p_val = sp_stats.ttest_ind(grp_a, grp_b, equal_var=False)
        u_stat, p_mwu = sp_stats.mannwhitneyu(grp_a, grp_b, alternative="two-sided")

        sig = p_val < alpha
        return {
            "method": "独立样本t检验 (Welch)",
            "alpha": alpha,
            "results": [{
                "group_a": group_a, "group_b": group_b,
                "n_a": len(grp_a), "n_b": len(grp_b),
                "mean_a": _r(grp_a.mean()), "mean_b": _r(grp_b.mean()),
                "std_a": _r(grp_a.std(ddof=1)), "std_b": _r(grp_b.std(ddof=1)),
                "t_statistic": _r(t_stat), "p_value": _r(p_val),
                "significant": sig,
                "effect_cohens_d": _r(_cohens_d(grp_a, grp_b)),
                "mwu_u": _r(u_stat), "mwu_p": _r(p_mwu),
                "conclusion": f"{'拒绝' if sig else '不能拒绝'}H0（p={_r(p_val)}{'' if not sig else ' < α=' + str(alpha)}），两组均值{'存在' if sig else '无'}显著差异。",
            }],
            "interpretation": (
                f"独立样本t检验结果：{group_a}(n={len(grp_a)}, M={_r(grp_a.mean())}) vs "
                f"{group_b}(n={len(grp_b)}, M={_r(grp_b.mean())})，"
                f"t={_r(t_stat)}，p={_r(p_val)}。{'差异显著' if sig else '差异不显著'}。"
                f"效应量Cohen's d={_r(_cohens_d(grp_a, grp_b))}（{'大' if abs(_cohens_d(grp_a, grp_b)) > 0.8 else '中' if abs(_cohens_d(grp_a, grp_b)) > 0.5 else '小'}效应）。"
            ),
        }

    @staticmethod
    def _ttest_paired(df, params, alpha):
        """配对样本t检验"""
        col_a = params.get("col_a", "")
        col_b = params.get("col_b", "")
        s1 = pd.to_numeric(df[col_a], errors="coerce").dropna()
        s2 = pd.to_numeric(df[col_b], errors="coerce").dropna()
        common = s1.index.intersection(s2.index)
        s1, s2 = s1.loc[common], s2.loc[common]

        t_stat, p_val = sp_stats.ttest_rel(s1, s2)
        sig = p_val < alpha
        diff = s1 - s2
        return {
            "method": "配对样本t检验",
            "alpha": alpha,
            "results": [{
                "col_a": col_a, "col_b": col_b, "n": len(s1),
                "mean_diff": _r(diff.mean()), "std_diff": _r(diff.std(ddof=1)),
                "t_statistic": _r(t_stat), "p_value": _r(p_val), "significant": sig,
                "effect_cohens_d": _r(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else None,
                "conclusion": f"{'拒绝' if sig else '不能拒绝'}H0，配对差值均值={_r(diff.mean())}，{'差异显著' if sig else '差异不显著'}。",
            }],
        }

    @staticmethod
    def _chi2_test(df, params, alpha):
        """卡方检验"""
        col_a = params.get("col_a", "")
        col_b = params.get("col_b", "")
        contingency = pd.crosstab(df[col_a], df[col_b])
        chi2, p_val, dof, expected = sp_stats.chi2_contingency(contingency)
        n = contingency.sum().sum()
        cramers_v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1))) if min(contingency.shape) > 1 else 0

        sig = p_val < alpha
        return {
            "method": "卡方独立性检验",
            "alpha": alpha,
            "results": [{
                "col_a": col_a, "col_b": col_b,
                "chi2_statistic": _r(chi2), "p_value": _r(p_val), "dof": int(dof),
                "significant": sig, "n": int(n),
                "cramers_v": _r(cramers_v),
                "conclusion": f"{'拒绝' if sig else '不能拒绝'}H0，两变量{'存在' if sig else '无'}显著关联（χ²={_r(chi2)}，p={_r(p_val)}）。",
            }],
            "interpretation": f"卡方检验：{col_a}与{col_b}的交叉分析显示{'显著关联' if sig else '无显著关联'}（χ²={_r(chi2)}，df={dof}，p={_r(p_val)}），Cramer's V={_r(cramers_v)}。",
        }

    @staticmethod
    def _anova(df, params, alpha):
        """单因素方差分析"""
        group_col = params.get("group_col", "")
        value_col = params.get("value_col", "")
        groups = []
        group_names = []
        for name, grp in df.groupby(group_col):
            vals = pd.to_numeric(grp[value_col], errors="coerce").dropna()
            if len(vals) >= 2:
                groups.append(vals.values)
                group_names.append(str(name))

        if len(groups) < 2:
            return {"method": "ANOVA", "error": "有效分组不足2组"}

        f_stat, p_val = sp_stats.f_oneway(*groups)

        # 事后 Tukey HSD
        all_vals = np.concatenate(groups)
        all_labels = np.concatenate([np.full(len(g), i) for i, g in enumerate(groups)])
        try:
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
            tukey = pairwise_tukeyhsd(all_vals, all_labels)
            posthoc = []
            for i in range(len(group_names)):
                for j in range(i + 1, len(group_names)):
                    idx = 0
                    for ii in range(i):
                        idx += len(group_names) - ii - 1
                    idx_ij = idx + (j - i - 1)
                    if idx_ij < len(tukey.reject):
                        posthoc.append({
                            "group_a": group_names[i], "group_b": group_names[j],
                            "meandiff": _r(tukey.meandiffs[idx_ij]),
                            "p_adj": _r(tukey.pvalues[idx_ij]),
                            "reject": bool(tukey.reject[idx_ij]),
                        })
        except Exception:
            posthoc = []

        sig = p_val < alpha
        group_stats = [{"name": n, "n": len(g), "mean": _r(np.mean(g)), "std": _r(np.std(g, ddof=1))}
                       for n, g in zip(group_names, groups)]

        return {
            "method": "单因素方差分析 (One-Way ANOVA)",
            "alpha": alpha,
            "results": [{
                "f_statistic": _r(f_stat), "p_value": _r(p_val),
                "significant": sig,
                "group_count": len(groups), "total_n": len(all_vals),
                "group_stats": group_stats,
                "posthoc": posthoc,
                "conclusion": f"{'拒绝' if sig else '不能拒绝'}H0，组间{'存在' if sig else '无'}显著差异（F={_r(f_stat)}，p={_r(p_val)}）。",
            }],
            "interpretation": (
                f"ANOVA结果：{group_col}对{value_col}的影响{'显著' if sig else '不显著'}"
                f"（F={_r(f_stat)}，p={_r(p_val)}）。"
                f"共{len(groups)}组，总样本量{len(all_vals)}。"
            ),
        }

    @staticmethod
    def _normality_test(df, params, alpha):
        """正态性检验"""
        columns = params.get("columns", [])
        if not columns:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        results = []
        for col in columns:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            n = len(series)
            if n < 3:
                continue
            if n <= 5000:
                stat_v, p_val = sp_stats.shapiro(series)
                test_name = "Shapiro-Wilk"
            else:
                stat_v, p_val = sp_stats.kstest(series, "norm", args=(series.mean(), series.std()))
                test_name = "Kolmogorov-Smirnov"

            results.append({
                "field": col, "test": test_name,
                "statistic": _r(stat_v), "p_value": _r(p_val),
                "is_normal": p_val > alpha, "n": n,
            })

        return {
            "method": "正态性检验",
            "alpha": alpha,
            "results": results,
        }

    # ── 相关分析 ──────────────────────────────────────────────
    @staticmethod
    def correlation(df: pd.DataFrame, columns: list | None = None,
                    method: str = "pearson") -> dict:
        """
        相关分析
        method: pearson / spearman / kendall
        返回: correlation_matrix, p_value_matrix, interpretation
        """
        if columns:
            cols = [c for c in columns if c in df.columns]
        else:
            cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(cols) < 2:
            return {"error": "至少需要2个数值字段", "matrix": [], "interpretation": ""}

        sub_df = df[cols].apply(pd.to_numeric, errors="coerce")
        corr_matrix = sub_df.corr(method=method)
        p_matrix = pd.DataFrame(np.ones((len(cols), len(cols))), index=cols, columns=cols)

        for i, c1 in enumerate(cols):
            for j, c2 in enumerate(cols):
                if i < j:
                    s1 = sub_df[c1].dropna()
                    s2 = sub_df[c2].dropna()
                    common = s1.index.intersection(s2.index)
                    s1, s2 = s1.loc[common], s2.loc[common]
                    if method == "pearson":
                        _, p = sp_stats.pearsonr(s1, s2)
                    elif method == "spearman":
                        _, p = sp_stats.spearmanr(s1, s2)
                    else:
                        _, p = sp_stats.kendalltau(s1, s2)
                    p_matrix.loc[c1, c2] = p
                    p_matrix.loc[c2, c1] = p

        # 构建矩阵数据
        matrix_data = []
        for c1 in cols:
            row = []
            for c2 in cols:
                row.append({
                    "col": c2,
                    "r": _r(corr_matrix.loc[c1, c2]),
                    "p": _r(p_matrix.loc[c1, c2]),
                    "sig": abs(corr_matrix.loc[c1, c2]) > 0 and p_matrix.loc[c1, c2] < 0.05,
                })
            matrix_data.append({"col": c1, "values": row})

        # 找强相关对
        strong_pairs = []
        for i, c1 in enumerate(cols):
            for j, c2 in enumerate(cols):
                if i < j:
                    r = corr_matrix.loc[c1, c2]
                    p = p_matrix.loc[c1, c2]
                    if not np.isnan(r) and not np.isnan(p) and abs(r) >= 0.5 and p < 0.05:
                        strength = "强" if abs(r) >= 0.8 else "中"
                        direction = "正" if r > 0 else "负"
                        strong_pairs.append(f"{c1}与{c2}呈{strength}{direction}相关（r={_r(r)}）")

        method_name = {"pearson": "Pearson", "spearman": "Spearman", "kendall": "Kendall"}[method]
        interpretation = f"{method_name}相关分析完成，共{len(cols)}个变量。"
        if strong_pairs:
            interpretation += "显著相关对：" + "；".join(strong_pairs) + "。"
        else:
            interpretation += "未发现|r|≥0.5的显著相关对。"

        return {
            "method": method_name,
            "columns": cols,
            "matrix": matrix_data,
            "strong_pairs": strong_pairs,
            "interpretation": interpretation,
        }

    # ── 回归分析 ──────────────────────────────────────────────
    @staticmethod
    def regression(df: pd.DataFrame, params: dict) -> dict:
        """
        回归分析
        params: {y_col, x_cols, regression_type: "linear"}
        """
        y_col = params.get("y_col", "")
        x_cols = params.get("x_cols", [])
        reg_type = params.get("regression_type", "linear")

        if reg_type != "linear":
            return {"error": f"MVP阶段仅支持线性回归，暂不支持: {reg_type}"}

        if not y_col or not x_cols:
            return {"error": "请指定因变量(y_col)和自变量(x_cols)"}

        valid_x = [c for c in x_cols if c in df.columns]
        if not valid_x:
            return {"error": "自变量列名无效"}

        # 清洗数据
        cols_needed = [y_col] + valid_x
        sub_df = df[cols_needed].apply(pd.to_numeric, errors="coerce").dropna()

        if len(sub_df) < len(valid_x) + 2:
            return {"error": f"有效样本量不足（需>{len(valid_x)+1}，实际{len(sub_df)}）"}

        y = sub_df[y_col].values
        X = sub_df[valid_x].values
        X_with_const = np.column_stack([np.ones(len(X)), X])

        # OLS求解
        try:
            beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
            y_pred = X_with_const @ beta
            residuals = y - y_pred
        except Exception as e:
            return {"error": f"回归计算失败: {str(e)}"}

        n = len(y)
        k = len(valid_x)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1) if n > k + 1 else 0
        mse = ss_res / (n - k - 1) if n > k + 1 else 0
        rmse = np.sqrt(mse)
        f_stat = (r_squared / k) / ((1 - r_squared) / (n - k - 1)) if n > k + 1 and (1 - r_squared) > 0 else 0

        # 系数详情
        coef_list = []
        se_y = np.sqrt(mse)
        for i, name in enumerate(["截距(Intercept)"] + valid_x):
            coef = beta[i]
            se_coef = se_y / np.sqrt(np.sum(X_with_const[:, i] ** 2)) if np.sum(X_with_const[:, i] ** 2) > 0 else 0
            t_val = coef / se_coef if se_coef > 0 else 0
            p_val = 2 * (1 - sp_stats.t.cdf(abs(t_val), n - k - 1))
            coef_list.append({
                "variable": name, "coefficient": _r(coef), "std_error": _r(se_coef),
                "t_value": _r(t_val), "p_value": _r(p_val),
                "significant": p_val < 0.05,
                "beta_std": None,  # 标准化系数后续补充
            })

        # 标准化系数
        try:
            X_std = (sub_df[valid_x].values - sub_df[valid_x].mean().values) / sub_df[valid_x].std().values
            y_std = (y - np.mean(y)) / np.std(y)
            X_std_const = np.column_stack([np.ones(n), X_std])
            beta_std = np.linalg.lstsq(X_std_const, y_std, rcond=None)[0]
            for i in range(len(coef_list)):
                coef_list[i]["beta_std"] = _r(beta_std[i])
        except Exception:
            pass

        # 残差正态性
        _, p_sw = sp_stats.shapiro(residuals) if n <= 5000 else (None, None)
        # DW统计量
        dw = _durbin_watson(residuals)

        # 方程字符串
        eq_parts = [f"{_r(beta[0])}"]
        for i, c in enumerate(valid_x):
            sign = "+" if beta[i + 1] >= 0 else "-"
            eq_parts.append(f"{sign} {_r(abs(beta[i+1]))}*{c}")
        equation = f"{y_col} = " + " ".join(eq_parts)

        sig_vars = [c["variable"] for c in coef_list[1:] if c["significant"]]
        interpretation = (
            f"线性回归方程：{equation}\n"
            f"R²={_r(r_squared)}，调整R²={_r(adj_r_squared)}，RMSE={_r(rmse)}，F={_r(f_stat)}。\n"
            f"显著变量（p<0.05）：{', '.join(sig_vars) if sig_vars else '无'}。\n"
            f"残差正态性：{'通过' if p_sw and p_sw > 0.05 else '未通过'}"
            f"（Shapiro p={_r(p_sw)}），DW={_r(dw)}（{'无自相关' if 1.5 < dw < 2.5 else '可能存在自相关'}）。"
        )

        return {
            "method": "多元线性回归 (OLS)",
            "equation": equation,
            "n": n, "k": k,
            "r_squared": _r(r_squared), "adj_r_squared": _r(adj_r_squared),
            "rmse": _r(rmse), "mse": _r(mse),
            "f_statistic": _r(f_stat),
            "coefficients": coef_list,
            "residual_stats": {
                "mean": _r(float(np.mean(residuals))),
                "std": _r(float(np.std(residuals))),
                "shapiro_p": _r(p_sw),
                "durbin_watson": _r(dw),
            },
            "interpretation": interpretation,
        }

    # ── 时序分析 ──────────────────────────────────────────────
    @staticmethod
    def timeseries(df: pd.DataFrame, params: dict) -> dict:
        """
        时序分析
        params: {date_col, value_col, periods: int (预测期数)}
        """
        date_col = params.get("date_col", "")
        value_col = params.get("value_col", "")
        periods = params.get("periods", 5)

        if not date_col or not value_col:
            return {"error": "请指定时间列(date_col)和值列(value_col)"}

        sub_df = df[[date_col, value_col]].copy()
        sub_df[date_col] = pd.to_datetime(sub_df[date_col], errors="coerce")
        sub_df[value_col] = pd.to_numeric(sub_df[value_col], errors="coerce")
        sub_df = sub_df.dropna().sort_values(date_col).reset_index(drop=True)

        if len(sub_df) < 10:
            return {"error": f"时序数据不足（需≥10，实际{len(sub_df)}）"}

        y = sub_df[value_col].values
        dates = sub_df[date_col].values
        n = len(y)

        # 移动平均
        ma_window = min(7, n // 3)
        if ma_window >= 2:
            ma = pd.Series(y).rolling(ma_window, center=True).mean().values
        else:
            ma = y

        # 趋势（线性拟合）
        x_trend = np.arange(n)
        slope, intercept, r_trend, _, _ = sp_stats.linregress(x_trend, y)
        trend_line = intercept + slope * x_trend

        # 季节性检测（简单方法：检查周期性自相关）
        seasonality = "未检测到"
        max_lag = min(n // 2, 24)
        if max_lag >= 4:
            acf_vals = _acf(y, max_lag)
            for lag in range(2, max_lag + 1):
                if acf_vals[lag] > 0.5 and acf_vals[lag] > acf_vals[lag - 1]:
                    seasonality = f"检测到周期≈{lag}期"
                    break

        # 简单预测（线性外推 + 预测区间）
        future_x = np.arange(n, n + periods)
        pred_values = intercept + slope * future_x
        pred_dates = pd.date_range(start=pd.Timestamp(dates[-1]) + pd.Timedelta(days=1), periods=periods, freq="D")

        # 统计摘要
        stats_summary = {
            "n": n, "start_date": str(dates[0])[:10], "end_date": str(dates[-1])[:10],
            "mean": _r(float(np.mean(y))), "std": _r(float(np.std(y))),
            "min": _r(float(np.min(y))), "max": _r(float(np.max(y))),
            "trend_slope": _r(slope), "trend_r2": _r(r_trend ** 2),
            "seasonality": seasonality,
            "ma_window": ma_window,
        }

        # 构建时间序列数据
        ts_data = []
        for i in range(n):
            ts_data.append({
                "date": str(dates[i])[:10],
                "value": _r(y[i]),
                "ma": _r(ma[i]) if not np.isnan(ma[i]) else None,
                "trend": _r(trend_line[i]),
            })

        pred_data = []
        for i in range(periods):
            pred_data.append({
                "date": str(pred_dates[i])[:10],
                "predicted": _r(pred_values[i]),
            })

        interpretation = (
            f"时序分析：{value_col}在{str(dates[0])[:10]}至{str(dates[-1])[:10]}期间，"
            f"共{n}个观测值。均值={_r(np.mean(y))}，标准差={_r(np.std(y))}。"
            f"趋势斜率={_r(slope)}（{'上升' if slope > 0 else '下降'}趋势，R²={_r(r_trend**2)}）。"
            f"{seasonality}。"
            f"未来{periods}期预测：{', '.join([_r(v) for v in pred_values])}。"
        )

        return {
            "method": "时序分析（趋势+移动平均+预测）",
            "stats": stats_summary,
            "series_data": ts_data,
            "predictions": pred_data,
            "interpretation": interpretation,
        }

    # ── 聚类分析 ──────────────────────────────────────────────
    @staticmethod
    def clustering(df: pd.DataFrame, params: dict) -> dict:
        """
        K-Means聚类分析
        params: {columns, k: int, standardize: bool}
        """
        columns = params.get("columns", [])
        k = params.get("k", 3)
        standardize = params.get("standardize", True)

        if not columns:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        valid_cols = [c for c in columns if c in df.columns]
        if len(valid_cols) < 2:
            return {"error": "聚类至少需要2个数值字段"}

        sub_df = df[valid_cols].apply(pd.to_numeric, errors="coerce").dropna()

        if len(sub_df) < k + 1:
            return {"error": f"有效样本量不足（需>{k}，实际{len(sub_df)}）"}

        X = sub_df.values
        feature_names = valid_cols

        # 标准化
        if standardize:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X

        # K-Means
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        centers = kmeans.cluster_centers_

        # 如果标准化了，反标准化中心
        if standardize:
            centers_orig = scaler.inverse_transform(centers)
        else:
            centers_orig = centers

        # 轮廓系数
        if len(sub_df) > k and len(sub_df) > 2:
            from sklearn.metrics import silhouette_score
            sil_score = silhouette_score(X_scaled, labels)
        else:
            sil_score = 0.0

        # SSE和肘部信息
        sse = float(kmeans.inertia_)

        # 每个簇的统计
        cluster_stats = []
        sub_df_copy = sub_df.copy()
        sub_df_copy["cluster"] = labels
        for c in range(k):
            cluster_data = sub_df_copy[sub_df_copy["cluster"] == c]
            stat = {
                "cluster": int(c), "n": int(len(cluster_data)),
                "percentage": _r(len(cluster_data) / len(sub_df) * 100),
            }
            for col in valid_cols:
                stat[f"{col}_mean"] = _r(cluster_data[col].mean())
                stat[f"{col}_std"] = _r(cluster_data[col].std(ddof=1))
            cluster_stats.append(stat)

        centers_list = []
        for c in range(k):
            center = {"cluster": int(c)}
            for i, col in enumerate(valid_cols):
                center[col] = _r(centers_orig[c][i])
            centers_list.append(center)

        interpretation = (
            f"K-Means聚类（k={k}）完成，{len(sub_df)}个样本分为{k}簇。"
            f"轮廓系数={_r(sil_score)}（{'较好' if sil_score > 0.5 else '一般' if sil_score > 0.25 else '较差'}），"
            f"SSE={_r(sse)}。"
        )
        for cs in cluster_stats:
            interpretation += f"\n- 簇{cs['cluster']}：{cs['n']}个样本（{cs['percentage']}%）"

        return {
            "method": f"K-Means聚类 (k={k})",
            "k": k,
            "n": len(sub_df),
            "features": valid_cols,
            "silhouette_score": _r(sil_score),
            "sse": _r(sse),
            "cluster_stats": cluster_stats,
            "centers": centers_list,
            "labels": labels.tolist(),
            "interpretation": interpretation,
        }


# ── 工具函数 ──────────────────────────────────────────────

def _r(val, decimals=4):
    """Round value for JSON serialization"""
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        val = float(val)
        if np.isnan(val) or np.isinf(val):
            return None
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, float):
        return round(val, decimals)
    return val


def _cohens_d(g1, g2):
    """Cohen's d效应量"""
    n1, n2 = len(g1), len(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(g1) - np.mean(g2)) / pooled_std)


def _acf(series, max_lag):
    """简单自相关函数"""
    series = series - np.mean(series)
    var = np.sum(series ** 2)
    if var == 0:
        return np.zeros(max_lag + 1)
    result = []
    for lag in range(max_lag + 1):
        result.append(float(np.sum(series[:len(series)-lag] * series[lag:]) / var))
    return result


def _durbin_watson(residuals):
    """Durbin-Watson统计量"""
    diff = np.diff(residuals)
    dw = np.sum(diff ** 2) / np.sum(residuals ** 2) if np.sum(residuals ** 2) > 0 else 2.0
    return float(dw)
