# -*- coding: utf-8 -*-
"""
경기도 과천시 카페·베이커리 조건별 검색 웹앱
- pandas 로 데이터 분석/전처리
- streamlit 으로 조건(범주) 버튼 필터링 앱 구현 (추가 패키지 없이 내장 기능만 사용)

실행:  streamlit run app.py

[데이터 근거 안내]
- 프랜차이즈 여부          : 실제 (업체명 브랜드로 판별)
- 커피만/제과만/둘다        : 반실제 (업종 분류 + 업체명 키워드로 도출)
- 주차/발렛/애견/성별선호/넓이 : 샘플 속성 (원본에 없어 업체명 기반으로 고정 생성 → 재실행해도 동일)
"""

import hashlib
import re

import pandas as pd
import streamlit as st

CSV_FILE = "경기도 과천시_카페 및 베이커리 업체 현황_20240331.csv"

# 과천시 카페·베이커리에 실제로 존재하는 프랜차이즈 브랜드 키워드
FRANCHISE_KEYWORDS = [
    "파리바게", "뚜레쥬르", "메가엠지씨커피", "이디야", "컴포즈커피", "빽다방",
    "더벤티", "투썸플레이스", "매머드", "타이거커피", "카페베네", "디저트39",
    "아이작", "나따오비까", "스타벅스", "엔제리너스", "커피빈", "할리스",
    "밀크앤허니",
]

# 업체명에 들어가면 '제과(베이커리) 취급'으로 보는 키워드
BAKERY_KEYWORDS = [
    "베이커리", "제과", "빵", "케익", "케이크", "cake", "디저트", "파이", "와플",
    "카스테라", "꽈배기", "식빵", "케빈", "베이킹", "명과", "리에제",
]
# 업체명에 들어가면 '커피 취급'으로 보는 키워드
COFFEE_KEYWORDS = ["커피", "카페", "coffee", "까페", "브루", "에스프레소", "라운지"]

SIZE_BUCKETS = ["10평 미만", "10~20평", "20~30평", "30평 이상"]


# ---------------------------------------------------------------------------
# 데이터 로딩 & 전처리
# ---------------------------------------------------------------------------
def _seed(name: str) -> int:
    """업체명 기반의 고정 시드값 (재실행해도 항상 동일 → 샘플 속성이 안 바뀜)"""
    return int(hashlib.md5(str(name).encode("utf-8")).hexdigest(), 16)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_FILE, encoding="cp949")
    df = df.rename(columns={"위도": "lat", "경도": "lon"})

    # --- 동 추출 -----------------------------------------------------------
    def extract_dong(addr: str) -> str:
        m = re.search(r"과천시\s+(\S+?[동리])", str(addr))
        return m.group(1) if m else "기타"

    df["동"] = df["소재지지번주소"].apply(extract_dong)

    # --- 프랜차이즈 여부 (실제: 업체명 기반) --------------------------------
    def is_franchise(name: str) -> bool:
        return any(k in str(name) for k in FRANCHISE_KEYWORDS)

    df["프랜차이즈"] = df["업체명"].apply(is_franchise)

    # --- 커피/제과 취급 여부 (반실제: 분류 + 이름 키워드) -------------------
    def sells(name: str, kind_class: str):
        name = str(name)
        has_bakery = kind_class == "제과점업" or any(k in name for k in BAKERY_KEYWORDS)
        has_coffee = kind_class == "커피 전문점" or any(k.lower() in name.lower() for k in COFFEE_KEYWORDS)
        return pd.Series([has_coffee, has_bakery])

    df[["커피취급", "제과취급"]] = df.apply(
        lambda r: sells(r["업체명"], r["표준산업분류명"]), axis=1
    )

    def category(r):
        if r["커피취급"] and r["제과취급"]:
            return "커피+제과 둘다"
        if r["커피취급"]:
            return "커피만"
        return "제과만"

    df["업종구분"] = df.apply(category, axis=1)

    # --- 샘플 속성 (원본에 없음 → 업체명 시드로 고정 생성) ------------------
    def build_sample(row):
        s = _seed(row["업체명"] + row["소재지지번주소"])
        parking = (s % 100) < 55
        valet = parking and ((s // 7) % 100) < 15
        dog = ((s // 13) % 100) < 22

        r = (s // 17) % 10          # 분위기: 여성40% / 남성30% / 무난30%
        gender = "여성 선호" if r < 4 else ("남성 선호" if r < 7 else "무난")

        idx = (s // 19) % 4          # 매장 넓이
        if row["프랜차이즈"]:        # 프랜차이즈는 한 단계 넓게 보정
            idx = min(idx + 1, 3)
        size = SIZE_BUCKETS[idx]
        return pd.Series([parking, valet, dog, gender, size])

    df[["주차", "발렛", "애견동반", "분위기", "매장넓이"]] = df.apply(build_sample, axis=1)
    return df


# ---------------------------------------------------------------------------
# 버튼형 필터 헬퍼 (st.pills 없으면 multiselect 로 대체)
# ---------------------------------------------------------------------------
def button_group(label, options, key):
    if hasattr(st, "pills"):
        return st.pills(label, options, selection_mode="multi", key=key) or []
    return st.multiselect(label, options, key=key)


# ---------------------------------------------------------------------------
# 페이지 구성
# ---------------------------------------------------------------------------
st.set_page_config(page_title="과천 카페·베이커리 조건 검색", page_icon="☕", layout="wide")
df = load_data()

st.title("☕ 과천시 카페·베이커리 조건별 검색")
st.caption("데이터 기준일 2024-03-31 · 출처 공공데이터포털 · 원하는 조건 버튼을 눌러 내 상황에 맞는 곳을 찾아보세요")

# ── 필터 영역 (사이드바) ───────────────────────────────────────────────
with st.sidebar:
    st.header("🔎 조건 선택")
    st.caption("여러 개 선택 가능 · 아무것도 안 누르면 전체")

    f_kind = button_group("업종", ["커피만", "제과만", "커피+제과 둘다"], "kind")
    f_fran = button_group("프랜차이즈", ["프랜차이즈", "개인/독립"], "fran")
    f_amen = button_group("편의시설 (모두 충족)", ["주차 가능", "발렛 가능", "애견 동반"], "amen")
    f_mood = button_group("선호 분위기", ["남성 선호", "여성 선호"], "mood")
    f_size = button_group("매장 넓이", SIZE_BUCKETS, "size")

    st.divider()
    st.markdown(
        "🟢 **프랜차이즈·업종**은 실제 데이터 기반\n\n"
        "🟡 **주차·발렛·애견·분위기·넓이**는 데모용 **샘플 속성**입니다 "
        "(원본 데이터에 없어 업체명 기준으로 고정 생성)."
    )

# ── 필터 적용 ──────────────────────────────────────────────────────────
res = df.copy()

if f_kind:
    res = res[res["업종구분"].isin(f_kind)]

if f_fran and len(f_fran) == 1:   # 둘 다 고르면 제한 없음
    want = f_fran[0] == "프랜차이즈"
    res = res[res["프랜차이즈"] == want]

# 편의시설: 선택한 항목을 '모두' 충족 (AND)
if "주차 가능" in f_amen:
    res = res[res["주차"]]
if "발렛 가능" in f_amen:
    res = res[res["발렛"]]
if "애견 동반" in f_amen:
    res = res[res["애견동반"]]

if f_mood:
    res = res[res["분위기"].isin(f_mood)]

if f_size:
    res = res[res["매장넓이"].isin(f_size)]

# ── 결과 출력 ──────────────────────────────────────────────────────────
selected = f_kind + f_fran + f_amen + f_mood + f_size
c1, c2, c3 = st.columns(3)
c1.metric("검색 결과", f"{len(res)} 곳")
c2.metric("전체 대비", f"{len(res) / len(df) * 100:.0f} %")
c3.metric("적용한 조건", f"{len(selected)} 개")

if selected:
    st.markdown("**선택한 조건:** " + " · ".join(f"`{s}`" for s in selected))

st.divider()

if len(res) == 0:
    st.warning("조건에 맞는 업체가 없습니다. 조건을 줄여보세요.")
else:
    view = res[
        ["업체명", "업종구분", "프랜차이즈", "주차", "발렛", "애견동반",
         "분위기", "매장넓이", "동", "소재지도로명주소", "전화번호"]
    ].rename(columns={
        "프랜차이즈": "프랜차이즈여부", "애견동반": "애견", "소재지도로명주소": "주소",
    }).reset_index(drop=True)
    view.index += 1

    st.dataframe(view, width="stretch", height=430)

    st.subheader("📍 결과 위치")
    st.map(res[["lat", "lon"]], size=20)

    with st.expander("💡 결과 요약 통계"):
        a, b = st.columns(2)
        a.write("**업종 분포**")
        a.bar_chart(res["업종구분"].value_counts())
        b.write("**동별 분포**")
        b.bar_chart(res["동"].value_counts())
