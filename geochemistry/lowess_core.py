"""
lowess_core.py — Geo-mean LOWESS 平滑模块（纯计算 + 绘图，不含 Tkinter 界面）

功能：
    lowess_bootstrap()  LOWESS 拟合 + bootstrap 置信带（百分位区间和 ±2σ 都给出）
    suggest_frac()      用 k 折交叉验证给出平滑窗口 frac 的建议值
    plot_lowess()       画成参考图的样式：灰色空心散点 + 红色曲线 + 浅红置信带

依赖：numpy, pandas, matplotlib, statsmodels
兼容旧版本：pandas < 0.24（无 to_numpy）、numpy < 1.17（无 default_rng）、
           statsmodels < 0.12（无 xvals 参数，改用拟合值插值到网格）
方法参考：Cleveland (1979) JASA 74:829–836（稳健局部加权回归）
"""
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess


def _clean(x, y):
    """转数值、去掉 NaN/inf，返回按 x 排序的数组。"""
    x = np.asarray(pd.to_numeric(pd.Series(x), errors="coerce"), dtype=float)
    y = np.asarray(pd.to_numeric(pd.Series(y), errors="coerce"), dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    order = np.argsort(x)
    return x[order], y[order]


def _make_rng(seed):
    """numpy >= 1.17 用 Generator，旧版本退回 RandomState。"""
    if hasattr(np.random, "default_rng"):
        return np.random.default_rng(seed)
    return np.random.RandomState(seed)


def _randint(rng, n):
    """有放回抽取 n 个 0..n-1 的整数，兼容 Generator 和 RandomState。"""
    if hasattr(rng, "integers"):
        return rng.integers(0, n, n)
    return rng.randint(0, n, n)


FAST_DELTA = 0.005   # 快速模式：delta = x 范围的 0.5%


def _interp_sorted_fit(x, y, grid, frac, it, delta):
    """在数据点上拟合（可带 delta 加速），再线性插值到网格。"""
    fit = lowess(y, x, frac=frac, it=it, delta=delta, return_sorted=True)
    xs, ys = fit[:, 0], fit[:, 1]
    ux, inv = np.unique(xs, return_inverse=True)          # 相同 x 取平均
    uy = np.bincount(inv, weights=ys) / np.bincount(inv)
    return np.interp(grid, ux, uy)


def _lowess_at(x, y, grid, frac, it, fast=False):
    if fast:
        # statsmodels 的 delta：相距不到 delta 的点不单独做局部回归，而是线性插值，
        # 数据量大时可快约 10 倍；曲线差异远小于置信带宽度
        return _interp_sorted_fit(x, y, grid, frac, it, FAST_DELTA * (x.max() - x.min()))
    try:
        return np.asarray(lowess(y, x, frac=frac, it=it, xvals=grid), dtype=float)
    except TypeError:
        # statsmodels < 0.12 没有 xvals
        return _interp_sorted_fit(x, y, grid, frac, it, 0.0)


def _fit(x, y, grid, frac, it, fast=False):
    """在 grid 上求 LOWESS 值；超出数据 x 范围的位置设为 NaN（不外推）。"""
    grid = np.asarray(grid, dtype=float)
    yhat = _lowess_at(x, y, grid, frac, it, fast)
    yhat[(grid < x.min()) | (grid > x.max())] = np.nan
    return yhat


def lowess_bootstrap(x, y, frac=0.3, it=3, n_boot=500, ci=95,
                     n_grid=200, seed=None, progress=None, fast=False):
    """
    参数
        frac     平滑窗口：每个局部回归使用的数据点比例（0~1），越大越平滑
        it       稳健迭代次数，3 为 Cleveland 推荐值，能压低离群点影响；0 为普通 LOWESS
        n_boot   bootstrap 次数，置信带一般 500~1000 次足够；0 表示不计算置信带
        ci       置信水平（%）
        progress 可选回调 progress(i, n_boot)，给 GUI 进度条用
        fast     True 时 bootstrap 部分用 delta 近似加速；主曲线始终精确计算
    返回
        DataFrame: x, y_fit, ci_low, ci_high, boot_sd, n_valid
    """
    x, y = _clean(x, y)
    if len(x) < 10:
        raise ValueError(f"Only {len(x)} valid data points; LOWESS needs at least 10.")
    if not 0 < frac <= 1:
        raise ValueError("frac must be in (0, 1].")

    grid = np.linspace(x.min(), x.max(), n_grid)
    y_fit = _fit(x, y, grid, frac, it)

    n_boot = int(n_boot)
    if n_boot <= 0:                            # 不计算置信带，只返回曲线
        nan = np.full(n_grid, np.nan)
        return pd.DataFrame({"x": grid, "y_fit": y_fit, "ci_low": nan,
                             "ci_high": nan, "boot_sd": nan,
                             "n_valid": np.zeros(n_grid, int)})

    rng = _make_rng(seed)
    n = len(x)
    boots = np.full((n_boot, n_grid), np.nan)
    for b in range(n_boot):
        idx = _randint(rng, n)                 # 成对重采样 (x, y)
        xb, yb = x[idx], y[idx]
        order = np.argsort(xb)
        boots[b] = _fit(xb[order], yb[order], grid, frac, it, fast)
        if progress is not None:
            progress(b + 1, n_boot)

    alpha = (100 - ci) / 2
    with np.errstate(all="ignore"):
        ci_low = np.nanpercentile(boots, alpha, axis=0)
        ci_high = np.nanpercentile(boots, 100 - alpha, axis=0)
        boot_sd = np.nanstd(boots, axis=0, ddof=1)

    return pd.DataFrame({
        "x": grid,
        "y_fit": y_fit,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "boot_sd": boot_sd,                    # y_fit ± 2*boot_sd 即参考图 2 的 2σ 带
        "n_valid": np.sum(np.isfinite(boots), axis=0),
    })


def suggest_frac(x, y, candidates=(0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7),
                 it=3, k=5, seed=0, fast=True):
    """
    k 折交叉验证选 frac。误差用中位绝对误差（对地化数据里的离群点更稳健）。
    返回 (最佳 frac, 各候选值误差的 DataFrame)。
    """
    x, y = _clean(x, y)
    rng = _make_rng(seed)
    folds = rng.permutation(len(x)) % k
    rows = []
    for f in candidates:
        errs = []
        for i in range(k):
            tr, te = folds != i, folds == i
            pred = _fit(x[tr], y[tr], x[te], f, it, fast)
            ok = np.isfinite(pred)
            errs.append(np.abs(pred[ok] - y[te][ok]))
        rows.append({"frac": f, "cv_mae": float(np.median(np.concatenate(errs)))})
    table = pd.DataFrame(rows)
    best = float(table.loc[table["cv_mae"].idxmin(), "frac"])
    return best, table


def plot_lowess(ax, x, y, result, band="percentile",
                line_color="#A4262C", band_color="#D9868A",
                label_curve="LOWESS", show_points=True):
    """
    band = "percentile" 用 ci_low/ci_high；band = "2sigma" 用 y_fit ± 2*boot_sd。
    ax 可以是嵌入 Tkinter 的 FigureCanvasTkAgg 里的 Axes。
    """
    x, y = _clean(x, y)
    if show_points:
        ax.scatter(x, y, s=28, facecolors="none", edgecolors="#B5B5B5",
                   linewidths=0.8, zorder=1, label="Data")
    if band == "2sigma":
        lo = result["y_fit"] - 2 * result["boot_sd"]
        hi = result["y_fit"] + 2 * result["boot_sd"]
    else:
        lo, hi = result["ci_low"], result["ci_high"]
    ax.fill_between(result["x"], lo, hi, color=band_color, alpha=0.35,
                    linewidth=0, zorder=2)
    ax.plot(result["x"], result["y_fit"], color=line_color, lw=2.5,
            zorder=3, label=label_curve)
    return ax


if __name__ == "__main__":
    # 自测：模拟一条 4000 Ma 之后下降的趋势，带离群点
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = _make_rng(1)
    age = rng.uniform(3200, 4400, 600)
    true = np.where(age < 4100, 6.2, 6.2 - (age - 4100) / 300)
    d18o = true + rng.normal(0, 0.4, age.size)
    d18o[rng.choice(age.size, 15, replace=False)] += rng.choice([-2, 2], 15)

    best, table = suggest_frac(age, d18o)
    print(table.to_string(index=False))
    print("建议 frac =", best)

    res = lowess_bootstrap(age, d18o, frac=best, n_boot=300, seed=0)
    print(res.iloc[::40].round(3).to_string(index=False))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    plot_lowess(ax, age, d18o, res)
    ax.set_xlabel("Age (Ma)")
    ax.set_ylabel("δ18O (‰)")
    fig.tight_layout()
    fig.savefig("lowess_demo.png", dpi=150)
    print("demo 图已保存 lowess_demo.png")
