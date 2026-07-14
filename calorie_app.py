import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
import os
import io
import uuid
from datetime import datetime, date, timedelta
import pandas as pd
import altair as alt
import warnings
warnings.filterwarnings("ignore")

# ================================================================
# ページ設定
# ================================================================
st.set_page_config(
    page_title="🥣 もぐレコ",
    page_icon="🥣",
    layout="wide",
)

# ================================================================
# カスタムCSS（ポップ＆カラフルデザイン）
# ================================================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --coral: #FF6B6B;
        --coral-dark: #E8534F;
        --turquoise: #3DCCC7;
        --turquoise-dark: #29ABA6;
        --sunny: #FFC93C;
        --sunny-dark: #E8AC10;
        --purple: #9B7EDE;
        --purple-dark: #7C5BC4;
        --green: #6BCB77;
        --green-dark: #4EA85C;
        --cream: #FFF7ED;
        --ink: #2D2A32;
    }

    html, body, [class*="css"] {
        font-family: 'M PLUS Rounded 1c', sans-serif !important;
    }

    .stApp {
        background: var(--cream);
    }

    /* ---------- タイトル（丸文字＋縁取り） ---------- */
    .main-title {
        text-align: center;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .main-title .logo-icon {
        width: 44px;
        height: 44px;
        flex-shrink: 0;
    }
    .main-title .accent {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        color: var(--sunny);
        -webkit-text-stroke: 2.5px var(--ink);
        paint-order: stroke fill;
    }
    .sub-title {
        text-align: center;
        color: #8A8494;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 1.8rem;
    }

    /* ---------- ポップカード共通 ---------- */
    .pop-card {
        border-radius: 22px;
        padding: 16px 18px;
        margin-bottom: 12px;
        border: 3px solid var(--ink);
        box-shadow: 5px 5px 0px rgba(45,42,50,0.15);
        color: var(--ink);
    }
    .dish-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border: 3px solid var(--coral);
        box-shadow: 4px 4px 0px var(--coral);
        color: var(--ink);
    }
    .advice-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 18px 20px;
        margin-top: 16px;
        border: 3px solid var(--purple);
        box-shadow: 4px 4px 0px var(--purple);
        color: var(--ink);
        line-height: 1.8;
    }
    .record-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        background: #FFFFFF;
        border-radius: 999px;
        margin-bottom: 8px;
        border: 2.5px solid #EFE6DA;
        color: var(--ink);
        font-weight: 500;
    }

    /* ---------- 見出しバッジ ---------- */
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        color: white;
    }

    /* ---------- サイドバー ---------- */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 3px dashed #EFE6DA;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        font-weight: 800 !important;
        color: var(--ink) !important;
    }

    /* ---------- ボタン（ピル型・ポップ） ---------- */
    .stButton > button {
        border-radius: 999px !important;
        font-weight: 700 !important;
        border: 3px solid var(--ink) !important;
        padding: 0.5em 1.4em !important;
        box-shadow: 3px 3px 0px rgba(45,42,50,0.25) !important;
        transition: all 0.12s ease !important;
        background: var(--sunny) !important;
        color: var(--ink) !important;
    }
    .stButton > button:hover {
        transform: translate(-2px, -2px) !important;
        box-shadow: 5px 5px 0px rgba(45,42,50,0.3) !important;
        background: var(--sunny) !important;
    }
    .stButton > button:active {
        transform: translate(1px, 1px) !important;
        box-shadow: 1px 1px 0px rgba(45,42,50,0.3) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--coral) !important;
        color: white !important;
    }
    .stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        color: var(--coral-dark) !important;
        border-color: var(--coral) !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
        padding: 0.25em 1em !important;
        font-size: 12px !important;
        min-height: 30px !important;
        background: #FFFFFF !important;
        color: var(--coral-dark) !important;
        border-color: var(--coral) !important;
        box-shadow: 2px 2px 0px rgba(45,42,50,0.2) !important;
    }

    /* ---------- タブ ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px !important;
        background: #FFFFFF !important;
        border: 2.5px solid #EFE6DA !important;
        padding: 8px 20px !important;
        font-weight: 700 !important;
        color: #8A8494 !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--turquoise) !important;
        border-color: var(--turquoise-dark) !important;
        color: white !important;
        box-shadow: 3px 3px 0px var(--turquoise-dark) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ---------- ファイルアップローダー / セレクト / 入力 ---------- */
    section[data-testid="stFileUploaderDropzone"] {
        border-radius: 22px !important;
        border: 3px dashed var(--turquoise) !important;
        background: #FFFFFF !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input, .stTextInput input {
        border-radius: 16px !important;
        border: 2.5px solid #EFE6DA !important;
    }
    div[role="radiogroup"] label {
        font-weight: 500 !important;
    }

    /* ---------- メトリクス ---------- */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 14px 16px 10px 16px;
        border: 2.5px solid #EFE6DA;
    }
    div[data-testid="stMetricValue"] {
        color: var(--ink) !important;
        font-weight: 800 !important;
    }

    /* ---------- プログレスバー ---------- */
    div[data-testid="stProgress"] > div > div {
        background: var(--coral) !important;
        border-radius: 999px !important;
    }
    div[data-testid="stProgress"] > div {
        background: #CDEFEF !important;
        border: 2px solid var(--turquoise) !important;
        border-radius: 999px !important;
    }

    /* ---------- アラート系 ---------- */
    div[data-testid="stAlert"] {
        border-radius: 18px !important;
        border: 2.5px solid transparent !important;
        font-weight: 500 !important;
    }

    hr { border-top: 3px dashed #EFE6DA !important; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# 日本時間設定
# ================================================================
os.environ['TZ'] = 'Asia/Tokyo'
try:
    import time
    time.tzset()
except:
    pass

# ================================================================
# Gemini API設定（Secretsから読み込み）
# ================================================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    gemini_ready = True
except Exception:
    gemini_ready = False
    st.error("APIキーが設定されていません。Streamlit Cloudの Settings → Secrets に GEMINI_API_KEY を設定してください。")

# ================================================================
# セッション状態の初期化
# ================================================================
if "meal_log" not in st.session_state:
    st.session_state.meal_log = []

# ================================================================
# 運動データベース
# ================================================================
EXERCISE_DATABASE = {
    "ウォーキング（30分）": 1.6,
    "ジョギング（30分）": 3.5,
    "ランニング（30分）": 4.9,
    "自転車（30分）": 3.0,
    "水泳（30分）": 4.2,
    "筋トレ（30分）": 2.5,
    "ヨガ（30分）": 1.3,
    "階段昇降（30分）": 3.0,
    "テニス（30分）": 3.4,
    "サッカー（30分）": 3.7,
}

# ================================================================
# 関数定義
# ================================================================
def calc_required_calories(height, weight, age, gender, activity):
    if gender == "男性":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    activity_map = {
        "ほぼ運動しない": 1.2,
        "軽い運動（週1-3日）": 1.375,
        "普通の運動（週3-5日）": 1.55,
        "激しい運動（週6-7日）": 1.725,
    }
    return int(bmr * activity_map.get(activity, 1.2))

def calc_ideal_nutrients(required_cal):
    return {
        "carb": int(required_cal * 0.60 / 4),
        "protein": int(required_cal * 0.15 / 4),
        "fat": int(required_cal * 0.25 / 9),
    }

def get_today_records():
    today = date.today().strftime("%Y-%m-%d")
    return [r for r in st.session_state.meal_log if r["date"] == today]

def estimate_calories_gemini(image):
    prompt = """この写真に写っている料理をすべて認識してください。
カロリーや栄養素は、写真に写っている実際の量に基づいて推定してください。

重要：
- 寿司は1貫あたり約40〜60kcalです。写真の貫数を数えて計算してください。
- 小鉢や副菜は量が少ないので、カロリーも低く見積もってください。
- 大盛りや普通盛りなど、見た目の量を考慮してください。
- 写真に写っている実際の量を正確に反映した数値にしてください。

1つだけの場合も、複数ある場合も、以下のJSON形式で返してください。他のテキストは不要です。

{"dishes": [
  {
    "name": "料理名（日本語。寿司なら種類と貫数も書く）",
    "calories": カロリー（写真の実際の量に基づく数値のみ）,
    "carb": 炭水化物グラム数（数値のみ）,
    "protein": タンパク質グラム数（数値のみ）,
    "fat": 脂質グラム数（数値のみ）,
    "confidence": 確信度0.0〜1.0,
    "comment": "この料理についての栄養アドバイス（30文字以内）"
  }
]}

複数の料理が写っている場合はすべて含めてください。"""

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        response = model.generate_content([prompt, image])
        result = response.text.strip()
        result = re.sub(r'^```json|```$', '', result, flags=re.MULTILINE).strip()
        data = json.loads(result)
        dishes = []
        for d in data.get("dishes", []):
            dishes.append({
                "name": d.get("name", "不明な料理"),
                "calories": int(d.get("calories", 0)),
                "nutrients": {
                    "carb": int(d.get("carb", 0)),
                    "protein": int(d.get("protein", 0)),
                    "fat": int(d.get("fat", 0)),
                },
                "confidence": float(d.get("confidence", 0.5)),
                "comment": d.get("comment", ""),
            })
        if not dishes:
            raise ValueError("認識できませんでした")
        return dishes
    except Exception as e:
        st.error(f"Gemini認識エラー: {e}")
        return [{
            "name": "認識できませんでした",
            "calories": 0,
            "nutrients": {"carb": 0, "protein": 0, "fat": 0},
            "confidence": 0,
            "comment": "別の角度から撮影してみてください",
        }]

def generate_ai_advice(consumed, required, consumed_nutrients, ideal_nutrients, today_records):
    meals = [r["name"] for r in today_records if r["type"] == "meal"]
    exercises = [r["name"] for r in today_records if r["type"] == "exercise"]
    remaining = required - consumed

    prompt = f"""あなたは栄養管理の専門家です。以下の情報をもとに、100文字程度で食事アドバイスを日本語で書いてください。

1日の必要カロリー: {required} kcal
現在の摂取カロリー: {consumed} kcal（残り {remaining} kcal）
今日食べたもの: {', '.join(meals) if meals else 'まだなし'}
今日の運動: {', '.join(exercises) if exercises else 'なし'}
炭水化物: {consumed_nutrients['carb']}g / 理想 {ideal_nutrients['carb']}g
タンパク質: {consumed_nutrients['protein']}g / 理想 {ideal_nutrients['protein']}g
脂質: {consumed_nutrients['fat']}g / 理想 {ideal_nutrients['fat']}g

具体的な食材名を挙げて、次に何を食べるべきかアドバイスしてください。"""

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "アドバイスを生成できませんでした。"

# ================================================================
# サイドバー：プロフィール（決断疲れを減らすため必須項目のみ最初に表示）
# ================================================================
with st.sidebar:
    st.header("👤 あなたの情報")
    st.caption("身長・体重だけでもすぐ使えます")
    height = st.number_input("身長 (cm)", value=165.0, step=0.1)
    weight = st.number_input("体重 (kg)", value=60.0, step=0.1)

    with st.expander("詳細設定（年齢・性別・活動量）", expanded=False):
        age = st.number_input("年齢", value=20, step=1)
        gender = st.radio("性別", ["男性", "女性"])
        activity = st.selectbox("ふだんの運動量", [
            "ほぼ運動しない",
            "軽い運動（週1-3日）",
            "普通の運動（週3-5日）",
            "激しい運動（週6-7日）",
        ], index=0)

    required = calc_required_calories(height, weight, age, gender, activity)
    ideal = calc_ideal_nutrients(required)
    st.metric("1日の目安カロリー", f"{required} kcal")

    if gemini_ready:
        st.success("✅ AIが使える状態です")
    else:
        st.error("❌ APIキー未設定")

# ================================================================
# メインコンテンツ
# ================================================================
st.markdown("""
<div class="main-title">
    <svg class="logo-icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M8 22C8 22 8 34 24 34C40 34 40 22 40 22" stroke="#2D2A32" stroke-width="3" stroke-linecap="round"/>
        <path d="M6 22H42" stroke="#2D2A32" stroke-width="3" stroke-linecap="round"/>
        <path d="M8 22C8 14 15 9 24 9C33 9 40 14 40 22" fill="#FF6B6B" stroke="#2D2A32" stroke-width="3" stroke-linejoin="round"/>
        <path d="M20 5C19 6.5 19 8 20.5 9" stroke="#2D2A32" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M27 4C26 5.8 26 7.5 27.7 9" stroke="#2D2A32" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
    <span class="accent">もぐレコ</span>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="sub-title">もぐもぐレコード｜AIが料理をパシャッと認識！記録も分析もぜんぶおまかせ ✨</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🍽️ 食事を記録", "🏃 運動を記録", "📊 今日のまとめ", "📈 履歴グラフ"])

# ================================================================
# タブ1：食事を記録
# ================================================================
with tab1:
    # ---- よく記録する食事（再認記憶：写真なしでワンタップ再記録） ----
    meal_seen = {}
    for r in st.session_state.meal_log:
        if r["type"] == "meal" and r["name"] != "認識できませんでした":
            key = r["name"]
            if key not in meal_seen:
                meal_seen[key] = {"count": 0, "calories": r["calories"], "nutrients": r["nutrients"]}
            meal_seen[key]["count"] += 1
    frequent_meals = sorted(meal_seen.items(), key=lambda x: x[1]["count"], reverse=True)[:3]

    if frequent_meals:
        st.markdown("**よく記録する食事（タップで即記録・写真不要）**")
        cols = st.columns(len(frequent_meals))
        for i, (name, info) in enumerate(frequent_meals):
            with cols[i]:
                if st.button(f"⚡ {name}\n{info['calories']} kcal", key=f"quick_meal_{name}", use_container_width=True):
                    st.session_state.meal_log.append({
                        "id": str(uuid.uuid4()),
                        "date": date.today().strftime("%Y-%m-%d"),
                        "time": datetime.now().strftime("%H:%M"),
                        "type": "meal",
                        "name": name,
                        "calories": info["calories"],
                        "nutrients": info["nutrients"],
                    })
                    st.toast(f"「{name}」を記録しました", icon="✅")
                    st.rerun()
        st.divider()

    st.subheader("料理写真をアップロードして記録")
    uploaded_file = st.file_uploader("写真を選ぶ", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file and st.button("🔍 料理を分析して記録", type="primary"):
        if not gemini_ready:
            st.error("APIキーが設定されていません")
        else:
            image = Image.open(uploaded_file).convert("RGB")
            col_img, col_result = st.columns([1, 1])

            with col_img:
                st.image(image, caption="アップロードした写真", use_container_width=True)

            with st.spinner("🤖 Gemini AIが料理を認識中..."):
                dishes = estimate_calories_gemini(image)

            now_time = datetime.now().strftime("%H:%M")
            today_str = date.today().strftime("%Y-%m-%d")
            for d in dishes:
                st.session_state.meal_log.append({
                    "id": str(uuid.uuid4()),
                    "date": today_str,
                    "time": now_time,
                    "type": "meal",
                    "name": d["name"],
                    "calories": d["calories"],
                    "nutrients": d["nutrients"],
                })

            with col_result:
                total_cal = sum(d["calories"] for d in dishes)
                st.success(f"✅ {len(dishes)}品を認識しました！（合計 {total_cal} kcal）")

                for d in dishes:
                    nut = d["nutrients"]
                    st.markdown(f"""
                    <div class="dish-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; font-size:16px;">🍴 {d['name']}</span>
                            <span class="badge" style="background:var(--coral);">{d['calories']} kcal</span>
                        </div>
                        <div style="font-size:12px; color:#8A8494; margin-top:6px; font-weight:500;">
                            炭水化物 {nut['carb']}g・タンパク質 {nut['protein']}g・脂質 {nut['fat']}g
                        </div>
                        <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                            <span class="badge" style="background:var(--turquoise);">
                                確信度 {d['confidence']*100:.0f}%
                            </span>
                            <span style="color:#8A8494; font-size:12px; font-weight:500;">{d['comment']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ================================================================
# タブ2：運動を記録
# ================================================================
with tab2:
    st.subheader("今日行った運動を記録")

    def log_exercise(name):
        burned = int(EXERCISE_DATABASE[name] * weight)
        st.session_state.meal_log.append({
            "id": str(uuid.uuid4()),
            "date": date.today().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "type": "exercise",
            "name": name,
            "calories": burned,
        })
        st.toast(f"「{name}」を記録しました（消費 {burned} kcal）", icon="✅")

    # ---- よく使う運動（再認記憶：選び直さず一目で選べる） ----
    exercise_counts = {}
    for r in st.session_state.meal_log:
        if r["type"] == "exercise":
            exercise_counts[r["name"]] = exercise_counts.get(r["name"], 0) + 1
    frequent_exercises = sorted(exercise_counts, key=exercise_counts.get, reverse=True)[:3]

    if frequent_exercises:
        st.markdown("**よく記録する運動（タップで即記録）**")
        cols = st.columns(len(frequent_exercises))
        for i, name in enumerate(frequent_exercises):
            with cols[i]:
                if st.button(f"⚡ {name}", key=f"quick_ex_{name}", use_container_width=True):
                    log_exercise(name)
                    st.rerun()
        st.markdown("&nbsp;", unsafe_allow_html=True)

    # ---- すべての運動から選ぶ ----
    exercise_name = st.selectbox("その他の運動から選ぶ", list(EXERCISE_DATABASE.keys()))
    if st.button("🏃 運動を記録", type="primary"):
        log_exercise(exercise_name)
        st.rerun()

# ================================================================
# タブ3：今日のまとめ
# ================================================================
with tab3:
    st.subheader(f"📊 今日のまとめ（{date.today().strftime('%Y年%m月%d日')}）")

    today_records = get_today_records()
    meal_cal = sum(r["calories"] for r in today_records if r["type"] == "meal")
    exercise_cal = sum(r["calories"] for r in today_records if r["type"] == "exercise")
    net_cal = meal_cal - exercise_cal

    consumed_nutrients = {"carb": 0, "protein": 0, "fat": 0}
    for r in today_records:
        if r["type"] == "meal" and "nutrients" in r:
            for k in consumed_nutrients:
                consumed_nutrients[k] += r["nutrients"].get(k, 0)

    ratio = net_cal / required * 100 if required > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("摂取カロリー", f"+{meal_cal} kcal")
    with col2:
        st.metric("運動で消費", f"-{exercise_cal} kcal")
    with col3:
        st.metric("実質カロリー", f"{net_cal} / {required} kcal")

    st.progress(max(0.0, min(ratio / 100, 1.0)))
    st.caption("🔴 摂取した分　🔵 まだ足りない分")
    if ratio < 50:
        st.warning(f"⚠️ カロリーが不足しています。あと {required - net_cal} kcal 必要です。")
    elif ratio < 90:
        st.info(f"✅ もう少しで目標達成！あと {required - net_cal} kcal です。")
    elif ratio <= 110:
        st.success("🎉 今日のカロリーは理想的です！")
    else:
        st.error(f"⚠️ {net_cal - required} kcal オーバーです。運動で消費しましょう。")

    st.subheader("三大栄養素")
    nut_col1, nut_col2, nut_col3 = st.columns(3)
    with nut_col1:
        carb_ratio = consumed_nutrients["carb"] / ideal["carb"] if ideal["carb"] > 0 else 0
        st.metric("炭水化物", f"{consumed_nutrients['carb']}g / {ideal['carb']}g")
        st.progress(max(0.0, min(carb_ratio, 1.0)))
    with nut_col2:
        pro_ratio = consumed_nutrients["protein"] / ideal["protein"] if ideal["protein"] > 0 else 0
        st.metric("タンパク質", f"{consumed_nutrients['protein']}g / {ideal['protein']}g")
        st.progress(max(0.0, min(pro_ratio, 1.0)))
    with nut_col3:
        fat_ratio = consumed_nutrients["fat"] / ideal["fat"] if ideal["fat"] > 0 else 0
        st.metric("脂質", f"{consumed_nutrients['fat']}g / {ideal['fat']}g")
        st.progress(max(0.0, min(fat_ratio, 1.0)))

    st.subheader("今日の記録")
    if today_records:
        for r in today_records:
            icon = "🍽" if r["type"] == "meal" else "🏃"
            sign = "+" if r["type"] == "meal" else "-"
            color = "#e94560" if r["type"] == "meal" else "#3498db"
            row_col1, row_col2 = st.columns([6, 1])
            with row_col1:
                color = "var(--coral-dark)" if r["type"] == "meal" else "var(--turquoise-dark)"
                st.markdown(f"""
                <div class="record-item">
                    <span>{icon} {r['name']}（{r['time']}）</span>
                    <span style="color:{color}; font-weight:800;">
                        {sign}{r['calories']} kcal
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with row_col2:
                if st.button("削除", key=f"del_{r['id']}"):
                    st.session_state.meal_log = [
                        m for m in st.session_state.meal_log if m["id"] != r["id"]
                    ]
                    st.rerun()
    else:
        st.info("📸 まずは「食事を記録」タブから、今日食べたものを撮ってみましょう")

    if st.button("🤖 AIアドバイスを表示", type="primary"):
        if not gemini_ready:
            st.error("APIキーが設定されていません")
        else:
            with st.spinner("AIがアドバイスを生成中..."):
                advice = generate_ai_advice(net_cal, required, consumed_nutrients, ideal, today_records)
            st.markdown(f"""
            <div class="advice-card">
                <div style="font-weight:800; color:var(--purple-dark); margin-bottom:8px; font-size:15px;">🤖 AIからのアドバイス</div>
                {advice}
            </div>
            """, unsafe_allow_html=True)

# ================================================================
# タブ4：履歴グラフ
# ================================================================
with tab4:
    st.subheader("📈 カロリー推移（直近7日間）")

    log = st.session_state.meal_log

    # 直近7日間（今日を含む）を必ず表示する
    today_d = date.today()
    last7_dates = [(today_d - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    daily = {d: {"meal": 0, "exercise": 0} for d in last7_dates}
    for r in log:
        d = r["date"]
        if d in daily:
            if r["type"] == "meal":
                daily[d]["meal"] += r["calories"]
            else:
                daily[d]["exercise"] += r["calories"]

    chart_rows = []
    for d in last7_dates:
        label = "/".join(d.split("-")[1:])
        chart_rows.append({"日付": label, "種類": "摂取カロリー", "kcal": daily[d]["meal"]})
        chart_rows.append({"日付": label, "種類": "運動消費", "kcal": daily[d]["exercise"]})

    bar_df = pd.DataFrame(chart_rows)

    bar_chart = (
        alt.Chart(bar_df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("日付:N", sort=None, title=None),
            xOffset="種類:N",
            y=alt.Y("kcal:Q", scale=alt.Scale(domain=[0, max(1, bar_df['kcal'].max() * 1.15)]), title="kcal"),
            color=alt.Color("種類:N", scale=alt.Scale(range=["#FF6B6B", "#3DCCC7"]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["日付", "種類", "kcal"],
        )
        .properties(height=300)
    )
    st.altair_chart(bar_chart, use_container_width=True)

    net_df = pd.DataFrame({
        "日付": ["/".join(d.split("-")[1:]) for d in last7_dates],
        "実質カロリー": [daily[d]["meal"] - daily[d]["exercise"] for d in last7_dates],
    })
    net_max = max(required * 1.15, net_df["実質カロリー"].max() * 1.15, 1)

    line_chart = (
        alt.Chart(net_df)
        .mark_line(point=alt.OverlayMarkDef(size=90, filled=True, color="#9B7EDE"), color="#9B7EDE", strokeWidth=3)
        .encode(
            x=alt.X("日付:N", sort=None, title=None),
            y=alt.Y("実質カロリー:Q", scale=alt.Scale(domain=[0, net_max])),
            tooltip=["日付", "実質カロリー"],
        )
        .properties(height=220)
    )
    goal_line = (
        alt.Chart(pd.DataFrame({"目標": [required]}))
        .mark_rule(color="#FFC93C", strokeDash=[6, 4], strokeWidth=2.5)
        .encode(y="目標:Q")
    )
    st.altair_chart(line_chart + goal_line, use_container_width=True)
    st.caption(f"🟡 点線は目標カロリー（{required} kcal / 日）を示しています。棒グラフ・折れ線グラフともに0kcalから表示しています。")

    st.divider()
    if st.button("🗑 記録を全削除", type="secondary"):
        st.session_state.meal_log = []
        st.success("すべての記録を削除しました")
        st.rerun()
