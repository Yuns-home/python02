# -*- coding: utf-8 -*-
"""
지역 간 제과·카페 데이터 비교 그래프
- 경기도 과천시 (카페·베이커리, 2024-03-31)
- 전북특별자치도 정읍시 (제과점, 2025-07-01)

matplotlib 로 4개 패널 비교 그래프를 그려 화면에 표시하고 PNG 로 저장한다.

실행:  python graph.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 한글 폰트 설정 (Windows 기준: 맑은 고딕)
# ---------------------------------------------------------------------------
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False   # 음수 부호 깨짐 방지

GWACHEON_CSV = "경기도 과천시_카페 및 베이커리 업체 현황_20240331.csv"
JEONGEUP_CSV = "전북특별자치도 정읍시_제과점 현황_20250701.csv"

# 두 지역에 실제로 존재하는 프랜차이즈 브랜드 키워드 (app.py 와 동일 기준)
FRANCHISE_KEYWORDS = [
    "파리바게", "뚜레쥬르", "메가엠지씨커피", "이디야", "컴포즈커피", "빽다방",
    "더벤티", "투썸플레이스", "매머드", "타이거커피", "카페베네", "디저트39",
    "아이작", "나따오비까", "스타벅스", "엔제리너스", "커피빈", "할리스",
    "밀크앤허니",
]

# 업체명에 들어가면 '제과(베이커리)'로 보는 키워드
BAKERY_KEYWORDS = [
    "베이커리", "제과", "빵", "케익", "케이크", "cake", "디저트", "파이", "와플",
    "카스테라", "꽈배기", "식빵", "케빈", "베이킹", "명과", "리에제",
]

# 그래프 색상 (두 지역 구분)
COLOR_GW = "#4C78A8"   # 과천 - 파랑
COLOR_JE = "#F58518"   # 정읍 - 주황


# ---------------------------------------------------------------------------
# 데이터 로딩
# ---------------------------------------------------------------------------
def is_franchise(name: str) -> bool:
    return any(k in str(name) for k in FRANCHISE_KEYWORDS)


def is_bakery(name: str, kind_class: str = "") -> bool:
    """제과(베이커리) 취급 여부: 업종 분류 또는 업체명 키워드로 판별"""
    name = str(name)
    return kind_class == "제과점업" or any(k in name for k in BAKERY_KEYWORDS)


def load_gwacheon() -> pd.DataFrame:
    df = pd.read_csv(GWACHEON_CSV, encoding="cp949")
    df["프랜차이즈"] = df["업체명"].apply(is_franchise)
    df["제과여부"] = df.apply(
        lambda r: is_bakery(r["업체명"], r["표준산업분류명"]), axis=1
    )
    return df


def load_jeongeup() -> pd.DataFrame:
    df = pd.read_csv(JEONGEUP_CSV, encoding="utf-8")
    df["프랜차이즈"] = df["업소명"].apply(is_franchise)
    df["제과여부"] = True   # 정읍 데이터는 모두 제과점
    return df


# ---------------------------------------------------------------------------
# 그래프 그리기
# ---------------------------------------------------------------------------
def draw(gw: pd.DataFrame, je: pd.DataFrame):
    regions = ["과천시", "정읍시"]
    colors = [COLOR_GW, COLOR_JE]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(
        "과천시 vs 정읍시 제과·카페 데이터 비교",
        fontsize=17, fontweight="bold",
    )

    # ── ① 전체 업체 수 비교 ───────────────────────────────────────────────
    ax = axes[0, 0]
    totals = [len(gw), len(je)]
    bars = ax.bar(regions, totals, color=colors)
    ax.set_title("① 전체 등록 업체 수", fontsize=13)
    ax.set_ylabel("업체 수 (곳)")
    ax.bar_label(bars, fmt="%d곳", padding=3)
    ax.set_ylim(0, max(totals) * 1.2)

    # ── ② 제과점 수 비교 (과천은 베이커리만 추출) ─────────────────────────
    ax = axes[0, 1]
    bakery_counts = [int(gw["제과여부"].sum()), int(je["제과여부"].sum())]
    bars = ax.bar(regions, bakery_counts, color=colors)
    ax.set_title("② 제과(베이커리) 업체 수", fontsize=13)
    ax.set_ylabel("업체 수 (곳)")
    ax.bar_label(bars, fmt="%d곳", padding=3)
    ax.set_ylim(0, max(bakery_counts) * 1.2)

    # ── ③ 프랜차이즈 vs 개인 (묶음 막대) ──────────────────────────────────
    ax = axes[1, 0]
    fran = [int(gw["프랜차이즈"].sum()), int(je["프랜차이즈"].sum())]
    indep = [len(gw) - fran[0], len(je) - fran[1]]
    x = np.arange(len(regions))
    w = 0.35
    b1 = ax.bar(x - w / 2, fran, w, label="프랜차이즈", color="#54A24B")
    b2 = ax.bar(x + w / 2, indep, w, label="개인/독립", color="#B0B0B0")
    ax.set_title("③ 프랜차이즈 vs 개인/독립", fontsize=13)
    ax.set_ylabel("업체 수 (곳)")
    ax.set_xticks(x)
    ax.set_xticklabels(regions)
    ax.bar_label(b1, fmt="%d", padding=3)
    ax.bar_label(b2, fmt="%d", padding=3)
    ax.legend()

    # ── ④ 프랜차이즈 비율(%) 비교 ─────────────────────────────────────────
    ax = axes[1, 1]
    fran_ratio = [
        fran[0] / len(gw) * 100,
        fran[1] / len(je) * 100,
    ]
    bars = ax.bar(regions, fran_ratio, color=colors)
    ax.set_title("④ 프랜차이즈 비율", fontsize=13)
    ax.set_ylabel("비율 (%)")
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    ax.set_ylim(0, max(fran_ratio) * 1.3 if max(fran_ratio) > 0 else 10)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig("region_compare.png", dpi=120, bbox_inches="tight")
    print("그래프 저장 완료 → region_compare.png")
    plt.show()


def main():
    gw = load_gwacheon()
    je = load_jeongeup()

    print(f"[과천시] 전체 {len(gw)}곳 · 제과 {int(gw['제과여부'].sum())}곳 · "
          f"프랜차이즈 {int(gw['프랜차이즈'].sum())}곳")
    print(f"[정읍시] 전체 {len(je)}곳 · 제과 {int(je['제과여부'].sum())}곳 · "
          f"프랜차이즈 {int(je['프랜차이즈'].sum())}곳")

    draw(gw, je)


if __name__ == "__main__":
    main()

