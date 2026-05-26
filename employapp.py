import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(layout="wide")

st.title("고용률로 읽는 경제활동인구 데이터 분석")
st.write("경제 수학에서 배우는 고용률, 실업률, 경제활동참가율을 실제 데이터로 탐구하는 자료입니다.")

st.divider()

st.header("1. 고용 관련 인구의 분류")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
고용 관련 지표를 이해하려면 먼저 인구가 어떻게 분류되는지 알아야 합니다.

**총인구** 중 경제 지표 계산에 주로 사용되는 인구는 **15세 이상 인구**입니다.

15세 이상 인구는 다시 다음과 같이 나뉩니다.

- **경제활동인구**: 일할 능력과 의사가 있는 사람
- **비경제활동인구**: 일할 능력이나 의사가 없거나 구직 활동을 하지 않는 사람

경제활동인구는 다시 다음과 같이 나뉩니다.

- **취업자**
- **실업자**
""")

with col2:
    st.markdown("""
```text
총인구
 ├─ 15세 미만 인구
 └─ 15세 이상 인구
      ├─ 비경제활동인구
      └─ 경제활동인구
           ├─ 실업자
           └─ 취업자

""")

st.divider()

st.header("2. 고용 관련 주요 지표")

# -----------------------------------
# 경제활동참가율
# -----------------------------------


st.markdown("## 경제활동참가율")

st.latex(r'''
\frac{경제활동인구}{15세이상인구}
\times 100
''')

st.markdown("""
- 경제활동인구 : 일할 능력과 의사가 있는 사람 수  
- 15세이상인구 : 경제활동이 가능한 전체 인구
""")

st.info("15세 이상 인구 중 경제활동인구의 비율")

st.divider()

# -----------------------------------
# 실업률
# -----------------------------------

st.markdown("## 실업률")

st.latex(r'''
\frac{실업자}{경제활동인구}
\times 100
''')

st.markdown("""
- 실업자 : 일자리를 구하고 있지만 일하지 못하는 사람 수  
- 경제활동인구 : 취업자 + 실업자
""")

st.info("경제활동인구 중 실업자의 비율")

st.divider()

# -----------------------------------
# 고용률
# -----------------------------------

st.markdown("## 고용률")

st.latex(r'''
\frac{취업자}{15세이상인구}
\times 100
''')

st.markdown("""
- 취업자 : 실제로 일하고 있는 사람 수  
- 15세이상인구 : 경제활동이 가능한 전체 인구
""")

st.info("15세 이상 인구 중 취업자의 비율")

st.warning("""
실업률과 고용률은 분모가 다릅니다.

실업률이 낮아졌다고 해서 반드시 고용 상황이 좋아진 것은 아닙니다.

구직을 포기한 사람이 늘어나면 실업률은 낮아질 수 있지만 고용률은 높아지지 않을 수 있습니다.
""")

st.divider()

st.header("3. 실제 데이터 분석")

uploaded_file = st.file_uploader(
    "고용 관련 데이터 파일 업로드",
    type=["xls", "xlsx", "csv"]
)

def read_kosis_xls(file):
    import re
    import html

    content = file.read()
    text = content.decode("euc-kr", errors="ignore")

    row_blocks = re.findall(r"<Row[^>]*>(.*?)</Row>", text, flags=re.DOTALL)

    rows = []
    for block in row_blocks:
        values = re.findall(r"<Data[^>]*>(.*?)</Data>", block, flags=re.DOTALL)
        values = [html.unescape(v).strip() for v in values]
        if values:
            rows.append(values)

    header_index = None
    for i, row in enumerate(rows):
        if "성별" in row and "항목" in row and "단위" in row:
            header_index = i
            break

    if header_index is None:
        raise ValueError("성별, 항목, 단위가 있는 표 머리글을 찾지 못했습니다.")

    header = rows[header_index]
    data = rows[header_index + 1:]

    max_len = len(header)
    cleaned_data = []

    for row in data:
        if len(row) < max_len:
            row = row + [""] * (max_len - len(row))
        elif len(row) > max_len:
            row = row[:max_len]
        cleaned_data.append(row)

    df = pd.DataFrame(cleaned_data, columns=header)
    return df

def prepare_data(df):
    id_cols = ["성별", "항목", "단위"]
    id_cols = [col for col in id_cols if col in df.columns]

    time_cols = [col for col in df.columns if col not in id_cols]

    long_df = df.melt(
        id_vars=id_cols,
        value_vars=time_cols,
        var_name="시점",
        value_name="값"
    )

    long_df["시점"] = (
        long_df["시점"]
        .astype(str)
        .str.replace(" 월", "", regex=False)
        .str.strip()
    )

    long_df["값"] = pd.to_numeric(long_df["값"], errors="coerce")
    long_df = long_df.dropna(subset=["값"])

    long_df["연도"] = long_df["시점"].str[:4].astype(int)

    long_df["항목"] = (
        long_df["항목"]
        .astype(str)
        .str.replace("[천명]", "", regex=False)
        .str.replace("[%]", "", regex=False)
        .str.strip()
    )

    return long_df

def draw_line_chart(data, title, color_col="성별"):
    fig = px.line(
        data,
        x="시점",
        y="값",
        color=color_col,
        markers=True,
        title=title
    )

    fig.update_layout(
        xaxis_title="시점",
        yaxis_title="값",
        legend_title_text=color_col
    )

    st.plotly_chart(fig, use_container_width=True)

if uploaded_file is not None:

    try:
        if uploaded_file.name.endswith(".csv"):

           df = pd.read_csv(uploaded_file)

        elif uploaded_file.name.endswith(".xlsx"):

            df = pd.read_excel(uploaded_file)

        else:

            df = read_kosis_xls(uploaded_file)

        long_df = prepare_data(df)

        st.sidebar.header("분석 조건 선택")

        min_year = int(long_df["연도"].min())
        max_year = int(long_df["연도"].max())

        year_range = st.sidebar.slider(
            "분석 기간 선택",
            min_year,
            max_year,
            (min_year, max_year)
        )

        filtered_df = long_df[
            (long_df["연도"] >= year_range[0]) &
            (long_df["연도"] <= year_range[1])
        ]

        filtered_df = long_df[
            (long_df["연도"] >= year_range[0]) &
            (long_df["연도"] <= year_range[1])
        ]

        metric_list = ["경제활동참가율", "실업률", "고용률"]

        selected_metric = st.sidebar.selectbox(
            "분석할 지표 선택",
            metric_list
        )

        analysis_mode = st.sidebar.radio(
            "탐구 질문 선택",
            [
                "전체 추세 보기",
                "남녀 비교",
                "남녀 격차 보기",
                "농가와 비농가 비교",
                "농가와 비농가 격차 보기",
                "한 집단 자세히 보기"
            ]
        )

        st.divider()

        st.subheader("4. 선택한 데이터 분석")

        st.caption("그래프가 복잡해지지 않도록 한 번에 1개의 질문만 분석하도록 구성했습니다.")

        # ------------------------------------------------
        # 전체 추세 보기
        # ------------------------------------------------
        if analysis_mode == "전체 추세 보기":

            st.markdown("### 전체 집단의 고용 지표 변화")

            view_df = filtered_df[
                (filtered_df["항목"] == selected_metric) &
                (filtered_df["성별"] == "계")
            ]

            draw_line_chart(
                view_df,
                f"전체 {selected_metric} 변화"
            )

            st.info("""

해석 포인트

시간이 지나면서 증가하는지, 감소하는지 살펴보세요.
특정 시기에 급격한 변화가 있는지 확인해 보세요.

코로나19 전후 시기의 변화도 함께 생각해 볼 수 있습니다.
""")

        # ------------------------------------------------
        # 남녀 비교
        # ------------------------------------------------
        elif analysis_mode == "남녀 비교":

            st.markdown("### 남자와 여자의 고용 지표 비교")

            view_df = filtered_df[
                (filtered_df["항목"] == selected_metric) &
                (filtered_df["성별"].isin(["남자", "여자"]))
            ]

            draw_line_chart(
                view_df,
                f"남녀 {selected_metric} 비교"
            )

            st.info("""

해석 포인트

남자와 여자 중 어느 집단의 값이 더 높은가요?
두 선의 간격이 시간이 지나면서 줄어드는지 살펴보세요.

여성의 경제활동참가율이나 고용률이 증가하는 추세인지 확인해 보세요.
""")

        # ------------------------------------------------
        # 남녀 격차
        # ------------------------------------------------
        elif analysis_mode == "남녀 격차 보기":

            st.markdown("### 남녀 격차 분석")

            view_df = filtered_df[
                (filtered_df["항목"] == selected_metric) &
                (filtered_df["성별"].isin(["남자", "여자"]))
            ]

            gap_df = view_df.pivot_table(
                index="시점",
                columns="성별",
                values="값",
                aggfunc="first"
            ).reset_index()

            if "남자" in gap_df.columns and "여자" in gap_df.columns:
                gap_df["남녀 격차"] = gap_df["남자"] - gap_df["여자"]

                fig = px.line(
                    gap_df,
                    x="시점",
                    y="남녀 격차",
                    markers=True,
                    title=f"{selected_metric}의 남녀 격차 변화"
                )

                fig.update_layout(
                    xaxis_title="시점",
                    yaxis_title="남자 - 여자"
                )

                st.plotly_chart(fig, use_container_width=True)

                latest_gap = gap_df["남녀 격차"].iloc[-1]
                st.success(f"선택한 기간의 마지막 시점에서 남녀 격차는 약 {latest_gap:.2f}입니다.")

            else:
                st.warning("남자와 여자 데이터가 모두 있어야 격차 분석이 가능합니다.")

            st.info("""

해석 포인트

격차가 0에 가까워질수록 남녀 차이가 줄어든 것입니다.

격차가 커지는 시기와 작아지는 시기를 찾아보세요.
""")

        # ------------------------------------------------
        # 농가와 비농가 비교
        # ------------------------------------------------
        elif analysis_mode == "농가와 비농가 비교":

            st.markdown("### 농가와 비농가의 고용 지표 비교")

            view_df = filtered_df[
                (filtered_df["항목"] == selected_metric) &
                (filtered_df["성별"].isin(["농가", "비농가"]))
            ]

            draw_line_chart(
                view_df,
                f"농가와 비농가 {selected_metric} 비교"
            )

            st.info("""

해석 포인트

농가와 비농가 중 어느 집단의 값이 더 높은가요?
농가는 계절이나 산업 구조의 영향을 더 크게 받을 수 있습니다.

두 집단의 변화 폭이 비슷한지 비교해 보세요.
""")

        # ------------------------------------------------
        # 농가와 비농가 격차
        # ------------------------------------------------
        elif analysis_mode == "농가와 비농가 격차 보기":

            st.markdown("### 농가와 비농가 격차 분석")

            view_df = filtered_df[
                (filtered_df["항목"] == selected_metric) &
                (filtered_df["성별"].isin(["농가", "비농가"]))
            ]

            gap_df = view_df.pivot_table(
                index="시점",
                columns="성별",
                values="값",
                aggfunc="first"
            ).reset_index()

            if "농가" in gap_df.columns and "비농가" in gap_df.columns:
                gap_df["농가-비농가 격차"] = gap_df["농가"] - gap_df["비농가"]

                fig = px.line(
                    gap_df,
                    x="시점",
                    y="농가-비농가 격차",
                    markers=True,
                    title=f"{selected_metric}의 농가-비농가 격차 변화"
                )

                fig.update_layout(
                    xaxis_title="시점",
                    yaxis_title="농가 - 비농가"
                )

                st.plotly_chart(fig, use_container_width=True)

                latest_gap = gap_df["농가-비농가 격차"].iloc[-1]
                st.success(f"선택한 기간의 마지막 시점에서 농가와 비농가의 격차는 약 {latest_gap:.2f}입니다.")

            else:
                st.warning("농가와 비농가 데이터가 모두 있어야 격차 분석이 가능합니다.")

            st.info("""

해석 포인트

격차가 양수이면 농가가 비농가보다 높은 것입니다.
격차가 음수이면 비농가가 농가보다 높은 것입니다.

격차가 크게 변하는 시기를 찾아보세요.
""")

        # ------------------------------------------------
        # 한 집단 자세히 보기
        # ------------------------------------------------
        elif analysis_mode == "한 집단 자세히 보기":

            st.markdown("### 한 집단의 세 지표 함께 보기")

            group_options = [
                "계",
                "남자",
                "여자",
                "농가",
                "농가남자",
                "농가여자",
                "비농가",
                "비농가남자",
                "비농가여자"
            ]

            available_groups = [
                g for g in group_options
                if g in filtered_df["성별"].unique()
            ]

            selected_group = st.selectbox(
                "자세히 볼 집단 선택",
                available_groups
            )

            view_df = filtered_df[
                (filtered_df["성별"] == selected_group) &
                (filtered_df["항목"].isin(metric_list))
            ]

            fig = px.line(
                view_df,
                x="시점",
                y="값",
                color="항목",
                markers=True,
                title=f"{selected_group}의 고용 관련 세 지표 변화"
            )

            fig.update_layout(
                xaxis_title="시점",
                yaxis_title="비율(%)",
                legend_title_text="지표"
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("""

해석 포인트

경제활동참가율과 고용률은 비슷하게 움직이나요?
실업률은 다른 두 지표와 어떻게 다르게 움직이나요?

실업률만으로 고용 상황을 판단하기 어려운 이유를 생각해 보세요.
""")

        st.divider()

        st.subheader("탐구 질문")

        st.info("""
남성과 여성의 고용률 격차는 줄어들고 있는가?
실업률이 낮아졌다고 해서 고용 상황이 반드시 좋아졌다고 볼 수 있을까?
경제활동참가율과 고용률은 어떤 관계가 있을까?
농가와 비농가의 고용 구조는 어떤 차이가 있을까?

특정 시기에 고용률이 크게 변한 이유는 무엇일까?
""")

        with st.expander("원본 데이터 보기"):
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("파일을 읽는 중 오류가 발생했습니다.")
        st.write(e)

else:
    st.info("먼저 고용 관련 데이터 파일을 업로드하세요.")