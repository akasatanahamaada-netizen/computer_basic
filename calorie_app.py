import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image, ImageEnhance, ImageDraw
import numpy as np
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

# cv2（お皿検出・顔検出で使用）は環境によって読み込みに失敗することがあるため、
# ここで失敗してもアプリ全体が止まらないよう安全に読み込む
try:
    import cv2
    CV2_AVAILABLE = True
except Exception as _cv2_err:
    CV2_AVAILABLE = False
    _cv2_import_error = str(_cv2_err)

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
        margin-bottom: 0.1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .main-title .logo-icon {
        width: 32px;
        height: 32px;
        flex-shrink: 0;
    }
    .main-title .accent {
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        color: var(--sunny);
        -webkit-text-stroke: 2px var(--ink);
        paint-order: stroke fill;
    }
    .sub-title {
        text-align: center;
        color: #8A8494;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 0.6rem;
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

    /* ---------- タブ（スクロールしても上部に固定表示） ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--cream);
        position: sticky;
        top: 0;
        z-index: 999;
        padding: 8px 0 10px 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px !important;
        background: #FFFFFF !important;
        border: 2.5px solid #EFE6DA !important;
        padding: 6px 16px !important;
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

    /* ---------- 全体の余白を詰めて、情報密度を上げる ---------- */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div {
        gap: 0.4rem;
    }
    .stTabs { margin-top: -0.5rem; }

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

    /* プログレスバーは st.progress ではなく自前HTMLで描画するためCSS上書き不要 */

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
# ユーザー識別（ニックネームでFirebase内のデータを分ける）
# ================================================================
FIREBASE_URL = st.secrets.get("FIREBASE_DB_URL", "").rstrip("/")

def sanitize_user_id(name):
    """Firebaseのキーに使えない文字を除去する"""
    name = name.strip()
    for ch in ['.', '#', '$', '[', ']', '/']:
        name = name.replace(ch, '')
    return name[:40]

# URLのクエリパラメータにニックネームがあれば復元（ブックマークで次回も同じデータに戻れる）
if "user_id" not in st.session_state:
    st.session_state.user_id = sanitize_user_id(st.query_params.get("user", ""))

def load_meal_log_from_firebase(user_id):
    """Firebaseからそのユーザーの記録だけを取得する"""
    if not FIREBASE_URL or not user_id:
        return []
    try:
        resp = requests.get(f"{FIREBASE_URL}/users/{user_id}/meal_log.json", timeout=6)
        data = resp.json()
        if isinstance(data, list):
            return [d for d in data if d]
        if isinstance(data, dict):
            return list(data.values())
        return []
    except Exception as e:
        st.session_state["_fb_load_error"] = str(e)
        return []

def persist_log():
    """記録をFirebaseに保存する（自分のニックネーム配下にのみ保存される）"""
    user_id = st.session_state.get("user_id", "")
    if not FIREBASE_URL:
        st.session_state["_fb_save_error"] = "FIREBASE_DB_URL が設定されていません"
        return False
    if not user_id:
        st.session_state["_fb_save_error"] = "ニックネームが未設定です"
        return False
    try:
        resp = requests.put(
            f"{FIREBASE_URL}/users/{user_id}/meal_log.json",
            json=st.session_state.meal_log,
            timeout=6,
        )
        if resp.status_code == 200:
            st.session_state["_fb_save_error"] = None
            return True
        st.session_state["_fb_save_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
        return False
    except Exception as e:
        st.session_state["_fb_save_error"] = str(e)
        return False

if "meal_log" not in st.session_state:
    st.session_state.meal_log = load_meal_log_from_firebase(st.session_state.user_id)

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

def calc_ideal_nutrients(required_cal, gender="男性"):
    """五大栄養素（タンパク質・脂質・炭水化物・ビタミン・ミネラル）のうち、
    数値で管理できる炭水化物・糖質・タンパク質・脂質・塩分の目安量を計算する。
    ビタミン・ミネラルは種類のバラエティで管理する（下部の集計処理を参照）。"""
    return {
        "carb": int(required_cal * 0.60 / 4),      # 炭水化物：総カロリーの60%
        "sugar": int(required_cal * 0.10 / 4),     # 糖質：総カロリーの10%以内が目安（WHO指針）
        "protein": int(required_cal * 0.15 / 4),   # タンパク質：総カロリーの15%
        "fat": int(required_cal * 0.25 / 9),       # 脂質：総カロリーの25%
        "salt": 7.5 if gender == "男性" else 6.5,  # 塩分：厚労省の目標量（g/日）
    }

def get_today_records():
    today = date.today().strftime("%Y-%m-%d")
    return [r for r in st.session_state.meal_log if r["date"] == today]

def pop_bar(ratio, height=22):
    """摂取した分=赤、まだ足りない分=青の1本バーを描画（st.progressは使わない）"""
    ratio = max(0.0, min(ratio, 1.0))
    st.markdown(f"""
    <div style="background:#CDEFEF; border:2.5px solid #29ABA6; border-radius:999px;
                height:{height}px; overflow:hidden; margin:6px 0;">
        <div style="background:#FF6B6B; width:{ratio*100:.1f}%; height:100%;
                    border-radius:999px 0 0 999px;"></div>
    </div>
    """, unsafe_allow_html=True)

# ================================================================
# 【自作のCV処理】HSV色空間による「彩り分析」
# ----------------------------------------------------------------
# 栄養学では「食事の彩りが豊かなほど栄養バランスが良い」とされる。
# Gemini APIに頼らず、画像を自分で色空間変換・分類して彩りスコアを算出する。
# 処理の流れ：
#   ① 画像を縮小（処理を軽くする）
#   ② RGB → HSV へ色空間変換
#   ③ 彩度・明度で「無彩色（白/黒/灰）」を先に分離
#   ④ 残りを色相(Hue)の角度で6つの色カテゴリに分類
#   ⑤ 各色の占有率を計算し、色の多様性から彩りスコアを出す
# ================================================================

# 料理の彩りとして意味を持つ6色（栄養指導で使われる分類に対応させる）
COLOR_CATEGORIES = {
    "red":    {"label": "赤",   "hex": "#E74C3C", "nutrient": "リコピン・鉄分（トマト、肉、赤パプリカ）"},
    "orange": {"label": "橙",   "hex": "#E67E22", "nutrient": "β-カロテン（にんじん、かぼちゃ、鮭）"},
    "yellow": {"label": "黄",   "hex": "#F1C40F", "nutrient": "ビタミンB群（卵、とうもろこし、大豆）"},
    "green":  {"label": "緑",   "hex": "#27AE60", "nutrient": "葉酸・ビタミンK（葉物野菜、ブロッコリー）"},
    "purple": {"label": "紫",   "hex": "#8E44AD", "nutrient": "アントシアニン（なす、紫キャベツ）"},
    "brown":  {"label": "茶",   "hex": "#8B5A2B", "nutrient": "食物繊維・タンパク質（肉、きのこ、玄米）"},
    "white":  {"label": "白",   "hex": "#BDC3C7", "nutrient": "炭水化物（ごはん、パン、豆腐）"},
}

def analyze_color_variety(image, sample_size=160):
    """
    料理写真をHSV色空間で分析し、彩りスコアと色の内訳を返す。
    ※ここはAPIを使わず、すべて自前の画像処理で計算している。
    """
    # ---- ① 画像を縮小して計算量を減らす ----
    img = image.convert("RGB").resize((sample_size, sample_size))
    arr = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # ---- ② RGB → HSV へ手動で色空間変換 ----
    mx = np.max(arr, axis=2)   # 明度Vのもと
    mn = np.min(arr, axis=2)
    diff = mx - mn             # 彩度Sのもと

    # 色相 H（0〜360度）を計算
    hue = np.zeros_like(mx)
    mask = diff > 1e-6
    # 最大値がRのとき／Gのとき／Bのときで式が変わる
    idx = mask & (mx == r)
    hue[idx] = (60 * ((g[idx] - b[idx]) / diff[idx])) % 360
    idx = mask & (mx == g)
    hue[idx] = (60 * ((b[idx] - r[idx]) / diff[idx]) + 120) % 360
    idx = mask & (mx == b)
    hue[idx] = (60 * ((r[idx] - g[idx]) / diff[idx]) + 240) % 360

    sat = np.where(mx > 1e-6, diff / np.maximum(mx, 1e-6), 0.0)  # 彩度S
    val = mx                                                      # 明度V

    total = hue.size
    counts = {k: 0 for k in COLOR_CATEGORIES}

    # ---- ③ 無彩色（白っぽい／暗すぎる）を先に分離 ----
    is_dark = val < 0.22                        # 暗すぎる部分（皿の影など）は除外対象
    is_white = (sat < 0.18) & (val >= 0.62)     # 彩度が低く明るい → 白（ごはん等）
    is_gray = (sat < 0.18) & (val < 0.62) & ~is_dark  # 灰色っぽい部分

    counts["white"] += int(np.count_nonzero(is_white))

    # ---- ④ 有彩色を色相の角度で6分類 ----
    chromatic = (~is_dark) & (~is_white) & (~is_gray)
    h = hue[chromatic]
    s = sat[chromatic]
    v = val[chromatic]

    # 茶色は「オレンジ〜赤系で、暗め or くすんだ色」として先に判定する
    # （そうしないと肉や揚げ物がすべて「橙」に分類されてしまう）
    is_brownish = ((h < 45) | (h >= 340)) & (v < 0.55)
    counts["brown"] += int(np.count_nonzero(is_brownish))

    rest = ~is_brownish
    hr = h[rest]
    counts["red"]    += int(np.count_nonzero((hr < 15) | (hr >= 345)))
    counts["orange"] += int(np.count_nonzero((hr >= 15) & (hr < 45)))
    counts["yellow"] += int(np.count_nonzero((hr >= 45) & (hr < 70)))
    counts["green"]  += int(np.count_nonzero((hr >= 70) & (hr < 170)))
    counts["purple"] += int(np.count_nonzero(((hr >= 260) & (hr < 345))))
    # 青緑〜青（170-260度）は料理ではほぼ皿や背景なので、意図的にカウントしない

    # ---- ⑤ 占有率を計算 ----
    counted_total = sum(counts.values())
    if counted_total == 0:
        return {"score": 0, "ratios": {}, "present_colors": [], "message": "料理の色を検出できませんでした"}

    ratios = {k: counts[k] / counted_total * 100 for k in counts}

    # 「その色がちゃんと存在する」とみなす閾値（5%以上）
    present_colors = [k for k, v in ratios.items() if v >= 5.0]

    # ---- 彩りスコアの算出 ----
    # (a) 何色使われているか（色数）… 最大7色 → 70点満点
    color_count_score = min(len(present_colors), 6) / 6 * 70

    # (b) 特定の色に偏っていないか（分散の低さ）… 30点満点
    #     一色だけで埋まっていると単調な食事とみなす
    max_ratio = max(ratios.values())
    balance_score = max(0.0, (100 - max_ratio) / 100) * 30

    score = int(round(color_count_score + balance_score))
    score = max(0, min(100, score))

    if score >= 75:
        message = "彩り豊かでバランスの良い一皿です"
    elif score >= 50:
        message = "まずまずの彩りです。緑や赤を足すとより良くなります"
    else:
        message = "色が偏っています。野菜を足して彩りを増やしましょう"

    return {"score": score, "ratios": ratios, "present_colors": present_colors, "message": message}

def missing_color_advice(present_colors):
    """不足している色から、補うべき食材を提案する（栄養指導の色分類に基づく）"""
    missing = [k for k in ["green", "red", "yellow", "purple"] if k not in present_colors]
    if not missing:
        return None
    tips = {
        "green": "緑（ほうれん草、ブロッコリー、ピーマン）",
        "red": "赤（トマト、赤パプリカ、にんじん）",
        "yellow": "黄（卵、かぼちゃ、とうもろこし）",
        "purple": "紫（なす、紫キャベツ、ぶどう）",
    }
    return "、".join(tips[m] for m in missing[:3])

# ================================================================
# 【自作のCV処理】インスタ映え加工（画像変換）
# ----------------------------------------------------------------
# Gemini APIを使わず、PIL＋numpyだけで完結する古典的な画像処理。
# インスタグラムの編集機能にある「明るさ・コントラスト・暖かさ・彩度・
# シャドウ」の5つのスライダーを、それぞれ個別の画像処理として自作する。
# ================================================================

def apply_insta_adjustments(image, brightness=0, contrast=0, warmth=0, saturation=0, shadows=0):
    """
    インスタグラムの編集機能を模した5つのスライダーを自作で実装する。
    各値はインスタと同じ -100〜100 のスライダー値を想定。
    """
    arr = np.asarray(image.convert("RGB")).astype(np.float32) / 255.0

    # ---- ① 明るさ：画像全体を底上げ／底下げする ----
    arr = arr + (brightness / 100.0) * 0.22

    # ---- ② シャドウ：暗い部分だけを持ち上げる（明るい部分はほぼ変化しない） ----
    # (1-明るさ)^2 を重みにすることで、暗いピクセルほど強く持ち上がる
    shadow_amt = (shadows / 100.0) * 0.5
    arr = arr + shadow_amt * (1.0 - arr) ** 2

    # ---- ③ コントラスト：中間値(0.5)を基準に伸び縮みさせる ----
    contrast_factor = 1.0 + (contrast / 100.0) * 0.6
    arr = (arr - 0.5) * contrast_factor + 0.5

    # ---- ④ 暖かさ：Rチャンネルを上げ、Bチャンネルを下げて色温度をシフト ----
    warmth_amt = (warmth / 100.0) * 0.28
    arr[:, :, 0] = arr[:, :, 0] + warmth_amt
    arr[:, :, 2] = arr[:, :, 2] - warmth_amt

    arr = np.clip(arr, 0, 1)
    out = Image.fromarray((arr * 255).astype(np.uint8))

    # ---- ⑤ 彩度：PILのColorEnhanceで彩度だけを調整 ----
    sat_factor = max(0.0, 1.0 + (saturation / 100.0))
    out = ImageEnhance.Color(out).enhance(sat_factor)

    return out

def pixelate(image, block=16):
    """縮小してから最近傍補間で拡大し、モザイク（ピクセル化）を作る"""
    w, h = image.size
    small = image.resize((max(1, w // block), max(1, h // block)), Image.BILINEAR)
    return small.resize((w, h), Image.NEAREST)

def generate_instagram_photo(image, style="natural"):
    """料理写真をSNS投稿向けに加工する（すべて自作のCV処理）"""
    image = image.convert("RGB")

    if style == "muted_warm":
        # ---- 低彩度・暖色寄り ----
        # インスタの編集機能で「明るさ+10 コントラスト-5 暖かさ+10 彩度-10 シャドウ+5」
        # とした場合のイメージをそのまま再現
        return apply_insta_adjustments(
            image, brightness=10, contrast=-5, warmth=10, saturation=-10, shadows=5
        )

    elif style == "natural_vivid":
        # ---- 自然な彩度高め：くっきり鮮やかに ----
        out = apply_insta_adjustments(
            image, brightness=5, contrast=10, warmth=0, saturation=28, shadows=-5
        )
        out = ImageEnhance.Sharpness(out).enhance(1.3)
        return out

    elif style == "reduce_blue":
        # ---- 青み削り：蛍光灯などによる青被りを補正（暖かさを強めにプラス） ----
        return apply_insta_adjustments(
            image, brightness=0, contrast=0, warmth=28, saturation=5, shadows=0
        )

    return image

# ================================================================
# 【自作のCV処理】お皿の検出（色によるセグメンテーション＋Hough変換）
# ----------------------------------------------------------------
# 授業でいう「形を見つける」「色を調べる」の複合例。
# 斜め構図で撮影されるとお皿は楕円に写るため、真円検出（Hough変換）
# だけでは検出できないことがある。そこで、
#   ①まず「明るく彩度の低い(白っぽい)領域」をHSVで抽出し、
#     最大の連結領域をお皿の輪郭（楕円）とみなす
#   ②見つからなければHough変換（真円）を試す
#   ③それでも失敗したら、顔が写りやすい上部を避けた
#     控えめな楕円をフォールバックとして使う
# ================================================================

def detect_plate_region(image):
    """
    お皿らしい領域を検出し、(中心x, 中心y, 横半径, 縦半径, 検出方法) を返す。

    ※ 明るい色の服（白・クリーム色のニット等）を着た人物が写っていると、
      肌・服・手・お皿が画像上で地続きになり、色だけでは分離できないことがある。
      そこで「料理写真では皿は画面の下側に写る」という構図の制約を利用し、
      画面の上部38%（顔が写りやすい範囲）は検索対象から除外する。
    """
    arr = np.asarray(image.convert("RGB"))
    h, w = arr.shape[:2]

    roi_top = int(h * 0.38)  # 顔が写りやすい上部を検索範囲から外す
    roi = arr[roi_top:, :]
    rh, rw = roi.shape[:2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1].astype(np.float32) / 255.0
    val = hsv[:, :, 2].astype(np.float32) / 255.0

    # ---- ① 白っぽい（明るく彩度が低い）領域を抽出 ----
    white_mask = ((val > 0.62) & (sat < 0.18)).astype(np.uint8) * 255
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    # 料理がお皿の中央にあるとリング状（穴あき）になるため、輪郭を塗りつぶして
    # お皿全体を1つの塊として扱えるようにする
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(white_mask)
    if contours:
        cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(filled, connectivity=8)
    best = None
    roi_area = rh * rw
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x, y, bw, bh = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        area_ratio = area / roi_area
        # 上下左右の端に接している場合は、体や背景の一部を拾っている可能性が高いため除外
        # （下端だけは、皿が画面下端ぎりぎりに写る構図もあるため許容する）
        touches_edge = x <= 1 or (x + bw) >= rw - 1 or (y + bh) >= rh - 1
        aspect = bw / max(bh, 1)
        fill_ratio = area / max(bw * bh, 1)  # 楕円らしい塗りつぶし率かどうか
        if (0.05 <= area_ratio <= 0.6 and not touches_edge
                and 0.7 <= aspect <= 3.0 and fill_ratio >= 0.62):
            if best is None or area > best[0]:
                best = (area, i)

    if best is not None:
        i = best[1]
        x, y, bw, bh = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        cx, cy = x + bw / 2, y + bh / 2 + roi_top
        rx, ry = bw / 2 * 1.1, bh / 2 * 1.1  # 少し余裕を持たせる
        return cx, cy, rx, ry, "color"

    # ---- ② Hough変換（真円）を、同じく下部ROI内で試す ----
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    gray_blur = cv2.medianBlur(gray, 7)
    min_r = int(min(rh, rw) * 0.2)
    max_r = int(min(rh, rw) * 0.48)
    circles = cv2.HoughCircles(
        gray_blur, cv2.HOUGH_GRADIENT, dp=1.2, minDist=min(rh, rw),
        param1=80, param2=45, minRadius=min_r, maxRadius=max_r
    )
    if circles is not None and len(circles[0]) > 0:
        cx0, cy0 = rw / 2, rh / 2
        best_c = min(circles[0], key=lambda c: (c[0] - cx0) ** 2 + (c[1] - cy0) ** 2)
        return float(best_c[0]), float(best_c[1]) + roi_top, float(best_c[2]), float(best_c[2]), "hough"

    # ---- ③ 最終フォールバック：顔が写りやすい上部を避けた控えめな楕円 ----
    cx, cy = w / 2, h * 0.68
    rx, ry = w * 0.28, h * 0.22
    return cx, cy, rx, ry, "fallback"

def mosaic_background_outside_plate(image, block=18):
    """お皿の外側だけをモザイク化する（お皿の内側＝料理はそのまま残す）"""
    image = image.convert("RGB")
    arr = np.array(image)
    h, w = arr.shape[:2]

    cx, cy, rx, ry, method = detect_plate_region(image)
    detected = method != "fallback"

    mosaic_full = np.array(pixelate(image, block=block))
    y_idx, x_idx = np.ogrid[:h, :w]
    norm_dist = ((x_idx - cx) / rx) ** 2 + ((y_idx - cy) / ry) ** 2
    mask = norm_dist <= 1.0  # True = お皿の内側（楕円マスク）
    out = np.where(mask[..., None], arr, mosaic_full)
    return Image.fromarray(out.astype(np.uint8)), detected

# ================================================================
# 【自作のCV処理】料理だけを「美味しそうな色味」に補正する
# ----------------------------------------------------------------
# 料理写真と人物写真では「映える色」の方向性が違う（料理は彩度・暖色を
# 強めるほど美味しそうに見えるが、同じ補正を肌にかけると不自然になる）。
# そこで detect_plate_region で検出したお皿の内側だけに強めの補正をかけ、
# それ以外（人物・背景）は元のまま残す。境界は自作のグラデーションマスク
# でぼかし（フェザリング）、継ぎ目が目立たないようにしている。
# ================================================================

# ================================================================
# 【自作のCV処理】ユーザー選択領域からのGrabCutによる料理輪郭抽出
# ----------------------------------------------------------------
# お皿の自動検出（色・Hough変換）は照明や構図によって難しいことがある。
# そこでユーザーが大まかな矩形範囲を選び、そこからGrabCutアルゴリズム
# （対話的前景／背景分離の古典的CV手法）で料理の輪郭を精密に抽出する。
# ================================================================

def detect_food_mask_grabcut(image, roi_box, iterations=5):
    """
    ユーザーが選んだ大まかな矩形(roi_box)から、GrabCutで料理の輪郭を
    精密に抽出し、0〜1のマスク（numpy配列）を返す。
    roi_box: (x0, y0, x1, y1) 画像のピクセル座標
    """
    arr = np.asarray(image.convert("RGB"))
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = roi_box
    x0, y0 = max(0, min(x0, w - 2)), max(0, min(y0, h - 2))
    x1, y1 = max(x0 + 1, min(x1, w - 1)), max(y0 + 1, min(y1, h - 1))
    rect = (x0, y0, x1 - x0, y1 - y0)

    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(arr, mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)
    except Exception:
        # 極端に小さい範囲などでGrabCutが失敗した場合は、矩形そのものをマスクにする
        mask_fallback = np.zeros((h, w), np.float32)
        mask_fallback[y0:y1, x0:x1] = 1.0
        return mask_fallback

    food_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
    return food_mask

def enhance_food_in_selection(image, roi_box, brightness=8, contrast=12, warmth=18, saturation=32, shadows=8):
    """ユーザーが選んだ範囲からGrabCutで料理の輪郭を検出し、その部分だけ美味しそうな色味に補正する"""
    image = image.convert("RGB")
    arr = np.asarray(image).astype(np.float32)

    food_mask = detect_food_mask_grabcut(image, roi_box)
    # 境界をぼかして自然に合成する（フェザリング）
    food_mask_blurred = cv2.GaussianBlur(food_mask, (25, 25), 0)

    enhanced = apply_insta_adjustments(
        image, brightness=brightness, contrast=contrast,
        warmth=warmth, saturation=saturation, shadows=shadows,
    )
    enhanced_arr = np.asarray(enhanced).astype(np.float32)

    mask3 = food_mask_blurred[..., None]
    out = arr * (1 - mask3) + enhanced_arr * mask3
    coverage = float(food_mask.mean())
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), coverage

def draw_selection_box(image, roi_box, color=(255, 107, 107), width=4):
    """選択中の矩形をプレビュー用に描画する"""
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    draw.rectangle(roi_box, outline=color, width=width)
    return img

def enhance_food_only(image, brightness=8, contrast=12, warmth=18, saturation=32, shadows=8, feather=0.18):
    """お皿の中（料理）だけを美味しそうな色味に補正し、それ以外は元のままにする"""
    image = image.convert("RGB")
    arr = np.asarray(image).astype(np.float32)
    h, w = arr.shape[:2]

    cx, cy, rx, ry, method = detect_plate_region(image)

    # 料理向けの強めの補正（彩度・暖かさ・コントラストを強めにかける）
    enhanced = apply_insta_adjustments(
        image, brightness=brightness, contrast=contrast,
        warmth=warmth, saturation=saturation, shadows=shadows,
    )
    enhanced_arr = np.asarray(enhanced).astype(np.float32)

    # ---- 楕円マスクを自作し、境界をなめらかにフェザリング（ぼかし）する ----
    y_idx, x_idx = np.ogrid[:h, :w]
    norm_dist = np.sqrt(((x_idx - cx) / rx) ** 2 + ((y_idx - cy) / ry) ** 2)
    # norm_dist <= 1 が皿の内側。境界付近(1±feather)を線形に滑らかにする
    mask = np.clip((1.0 + feather - norm_dist) / (2 * feather), 0, 1)
    mask = mask[..., None]

    out = arr * (1 - mask) + enhanced_arr * mask
    detected = method != "fallback"
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), detected

# ================================================================
# 【CV処理】人物の顔検出（Haar Cascade / Viola-Jones法）とモザイク
# ----------------------------------------------------------------
# 料理写真に人が写り込んでいた場合、プライバシー保護のため顔だけを
# モザイク化する。OpenCV付属のHaar Cascade分類器を利用した古典的な
# 物体検出（特徴量ベース）。
# ================================================================

_FACE_CASCADE = None
_cascade_load_error = None
if CV2_AVAILABLE:
    try:
        _HAAR_PATH = os.path.join(os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml")
        _FACE_CASCADE = cv2.CascadeClassifier(_HAAR_PATH)
        if _FACE_CASCADE.empty():
            _FACE_CASCADE = None
            _cascade_load_error = "顔検出モデルの読み込みに失敗しました"
    except Exception as e:
        _FACE_CASCADE = None
        _cascade_load_error = str(e)

def detect_faces(image):
    """Haar Cascadeで画像内の顔を検出し、(x, y, w, h) のリストを返す"""
    arr = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))
    return faces

def mosaic_faces(image, block_divisor=8):
    """検出した顔の領域だけをモザイク化する（プライバシー保護）
    block_divisor が小さいほどブロックが大きくなり、粗いモザイクになる"""
    image = image.convert("RGB")
    faces = detect_faces(image)
    arr = np.array(image)
    for (x, y, fw, fh) in faces:
        pad = int(0.15 * fw)  # 顔の輪郭全体を覆うよう少し余裕を持たせる
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(image.width, x + fw + pad), min(image.height, y + fh + pad)
        region = arr[y0:y1, x0:x1]
        if region.size == 0:
            continue
        pixelated = np.array(pixelate(Image.fromarray(region), block=max(4, fw // block_divisor)))
        arr[y0:y1, x0:x1] = pixelated
    return Image.fromarray(arr), len(faces)

# ================================================================
# 【自作のCV処理】料理と人物、それぞれに合う色味を別々にかける
# ----------------------------------------------------------------
# 「料理を美味しそうに見せる色味」（暖色・彩度高め・コントラスト強め）と
# 「人の肌を自然に見せる色味」（彩度控えめ・柔らかいトーン・影を持ち上げる）は
# 本来は逆方向の処理。お皿検出と顔検出を組み合わせ、同じ写真の中で
# 領域ごとに異なる色調整を適用する。マスクの境界はぼかして自然に繋げる。
# ================================================================

def region_aware_food_portrait_enhance(image):
    """お皿の領域には食欲をそそる色味、顔の領域には自然で優しい色味をかける"""
    image = image.convert("RGB")
    arr = np.asarray(image).astype(np.float32)
    h, w = arr.shape[:2]

    # ---- 料理領域のマスク（お皿検出を流用） ----
    cx, cy, rx, ry, _ = detect_plate_region(image)
    y_idx, x_idx = np.ogrid[:h, :w]
    food_mask = (((x_idx - cx) / rx) ** 2 + ((y_idx - cy) / ry) ** 2 <= 1.0).astype(np.float32)

    # ---- 顔領域のマスク（Haar Cascadeを流用、少し広めに） ----
    face_mask = np.zeros((h, w), dtype=np.float32)
    n_faces = 0
    if CV2_AVAILABLE and _FACE_CASCADE is not None:
        faces = detect_faces(image)
        n_faces = len(faces)
        for (fx, fy, fw, fh) in faces:
            pad = int(0.25 * fw)
            x0, y0 = max(0, fx - pad), max(0, fy - pad)
            x1, y1 = min(w, fx + fw + pad), min(h, fy + fh + pad)
            face_mask[y0:y1, x0:x1] = 1.0

    # マスクの境界をぼかして自然に繋げる（継ぎ目を作らない）
    food_mask = cv2.GaussianBlur(food_mask, (31, 31), 0)
    face_mask = cv2.GaussianBlur(face_mask, (31, 31), 0)
    food_mask = food_mask * (1 - face_mask)  # 顔とお皿が重なる場合は顔を優先

    # ---- 料理向け：彩度・暖かさ・コントラストを強めて食欲をそそる発色に ----
    food_arr = np.asarray(
        apply_insta_adjustments(image, brightness=5, contrast=15, warmth=12, saturation=30, shadows=-5)
    ).astype(np.float32)

    # ---- 人物向け：彩度は抑えめ、シャドウを持ち上げて肌を優しく見せる ----
    portrait_arr = np.asarray(
        apply_insta_adjustments(image, brightness=8, contrast=-8, warmth=4, saturation=-12, shadows=15)
    ).astype(np.float32)

    out = (arr * (1 - food_mask - face_mask)[..., None]
           + food_arr * food_mask[..., None]
           + portrait_arr * face_mask[..., None])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), n_faces

def estimate_calories_gemini(image):
    prompt = """この写真に写っている料理をすべて認識してください。
カロリーや栄養素は、写真に写っている実際の量に基づいて推定してください。
五大栄養素（タンパク質・脂質・炭水化物・ビタミン・ミネラル）の観点で分析してください。

重要：
- 寿司は1貫あたり約40〜60kcalです。写真の貫数を数えて計算してください。
- 小鉢や副菜は量が少ないので、カロリーも低く見積もってください。
- 大盛りや普通盛りなど、見た目の量を考慮してください。
- 写真に写っている実際の量を正確に反映した数値にしてください。
- 糖質は炭水化物の一部（炭水化物から食物繊維を除いたもの）です。炭水化物以下の数値にしてください。
- 塩分（食塩相当量）はグラム数で推定してください。
- ビタミン・ミネラルは、その料理に多く含まれる代表的なものを日本語の名称で最大3つずつ挙げてください（例：ビタミンC、ビタミンB1、鉄、カルシウム、カリウムなど）。特に何も豊富でなければ空配列で構いません。

1つだけの場合も、複数ある場合も、以下のJSON形式で返してください。他のテキストは不要です。

{"dishes": [
  {
    "name": "料理名（日本語。寿司なら種類と貫数も書く）",
    "calories": カロリー（写真の実際の量に基づく数値のみ）,
    "carb": 炭水化物グラム数（数値のみ）,
    "sugar": 糖質グラム数（炭水化物以下の数値のみ）,
    "protein": タンパク質グラム数（数値のみ）,
    "fat": 脂質グラム数（数値のみ）,
    "salt": 食塩相当量グラム数（数値のみ、小数可）,
    "vitamins": ["含まれる代表的なビタミン（最大3つ）"],
    "minerals": ["含まれる代表的なミネラル（最大3つ）"],
    "confidence": 確信度0.0〜1.0
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
                    "sugar": int(d.get("sugar", 0)),
                    "protein": int(d.get("protein", 0)),
                    "fat": int(d.get("fat", 0)),
                    "salt": round(float(d.get("salt", 0)), 1),
                },
                "vitamins": d.get("vitamins", []) or [],
                "minerals": d.get("minerals", []) or [],
                "confidence": float(d.get("confidence", 0.5)),
            })
        if not dishes:
            raise ValueError("認識できませんでした")
        return dishes
    except Exception as e:
        st.error(f"Gemini認識エラー: {e}")
        return [{
            "name": "認識できませんでした",
            "calories": 0,
            "nutrients": {"carb": 0, "sugar": 0, "protein": 0, "fat": 0, "salt": 0},
            "vitamins": [],
            "minerals": [],
            "confidence": 0,
        }]

NUTRIENT_LABELS = {"carb": "炭水化物", "sugar": "糖質", "protein": "タンパク質", "fat": "脂質", "salt": "塩分"}
NUTRIENT_COLORS = {"carb": "#f39c12", "sugar": "#e91e8c", "protein": "#e94560", "fat": "#3498db", "salt": "#5A5462"}

def nutrient_status(consumed, ideal):
    """『目安まで摂りたい』栄養素（炭水化物・タンパク質・脂質）の状態を判定する"""
    ratio = consumed / ideal * 100 if ideal > 0 else 0
    if ratio < 70:
        return "不足", "#e74c3c", ratio
    elif ratio <= 130:
        return "ちょうど良い", "#27ae60", ratio
    else:
        return "摂りすぎ", "#e67e22", ratio

def limit_status(consumed, limit):
    """『摂りすぎに注意』な栄養素（糖質・塩分）の状態を判定する"""
    ratio = consumed / limit * 100 if limit > 0 else 0
    if ratio <= 100:
        return "良好", "#27ae60", ratio
    elif ratio <= 130:
        return "やや多い", "#e67e22", ratio
    else:
        return "摂りすぎ", "#e74c3c", ratio

def generate_ai_advice(consumed, required, consumed_nutrients, ideal_nutrients, today_records):
    """1日全体のアドバイス＋次の食事のおすすめ献立＋簡単な作り方をまとめて生成する"""
    meals = [r["name"] for r in today_records if r["type"] == "meal"]
    exercises = [r["name"] for r in today_records if r["type"] == "exercise"]
    remaining = required - consumed

    # 目安まで摂りたい栄養素（炭水化物・タンパク質・脂質）の過不足
    status_lines = []
    for key in ["carb", "protein", "fat"]:
        status, _, ratio = nutrient_status(consumed_nutrients[key], ideal_nutrients[key])
        diff = ideal_nutrients[key] - consumed_nutrients[key]
        status_lines.append(
            f"{NUTRIENT_LABELS[key]}: {consumed_nutrients[key]}g / 目安{ideal_nutrients[key]}g "
            f"（{status}、{'あと'+str(diff)+'g足りない' if diff > 0 else str(-diff)+'g多い' if diff < 0 else '適量'}）"
        )
    # 摂りすぎに注意したい栄養素（糖質・塩分）の状況
    for key, unit in [("sugar", "g"), ("salt", "g")]:
        status, _, ratio = limit_status(consumed_nutrients[key], ideal_nutrients[key])
        status_lines.append(
            f"{NUTRIENT_LABELS[key]}: {consumed_nutrients[key]}{unit} / 上限目安{ideal_nutrients[key]}{unit}（{status}）"
        )
    # ビタミン・ミネラルは「摂れた種類」で判断
    vit_list = ", ".join(sorted(set(consumed_nutrients.get("vitamins", [])))) or "特になし"
    min_list = ", ".join(sorted(set(consumed_nutrients.get("minerals", [])))) or "特になし"
    status_lines.append(f"今日摂れたビタミン: {vit_list}")
    status_lines.append(f"今日摂れたミネラル: {min_list}")

    # 自作の画像処理（HSV色分析）で求めた彩りスコアも判断材料に加える
    color_scores = [r["color_score"] for r in today_records if r.get("color_score") is not None]
    if color_scores:
        avg_color = int(round(sum(color_scores) / len(color_scores)))
        status_lines.append(f"食事写真の彩りスコア（画像の色分析による）: 平均{avg_color}点 / 100点")

    prompt = f"""あなたは栄養管理の専門家です。今日1日の食事内容を、五大栄養素（タンパク質・脂質・炭水化物・ビタミン・ミネラル）の観点で分析して、以下の情報を出してください。

1日の必要カロリー: {required} kcal
現在の摂取カロリー: {consumed} kcal（残り {remaining} kcal）
今日食べたもの: {', '.join(meals) if meals else 'まだなし'}
今日の運動: {', '.join(exercises) if exercises else 'なし'}

栄養素の状況:
{chr(10).join(status_lines)}

出してほしい情報:
1. advice: 今日全体として何が足りず何が多いかをまとめたアドバイス（120文字程度。1品ごとの感想ではなく全体の話。ビタミン・ミネラルの偏りや、彩りスコアが低い場合は色の少なさにも触れる）
2. menu_name: 不足を補うのに最適な、次の食事のおすすめ献立名（1品。家庭で作りやすいもの）
3. menu_reason: なぜその献立がおすすめか（50文字程度）
4. recipe: その料理の簡単な作り方（3〜5ステップの配列。各ステップ40文字以内）

必ず以下のJSON形式のみで返してください。他のテキストは不要です。
{{"advice": "...", "menu_name": "...", "menu_reason": "...", "recipe": ["手順1", "手順2", "手順3"]}}"""

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r'^```json|```$', '', text, flags=re.MULTILINE).strip()
        data = json.loads(text)
        return {
            "advice": data.get("advice", ""),
            "menu_name": data.get("menu_name", ""),
            "menu_reason": data.get("menu_reason", ""),
            "recipe": data.get("recipe", []),
        }
    except Exception:
        return {
            "advice": "アドバイスを生成できませんでした。もう一度お試しください。",
            "menu_name": "",
            "menu_reason": "",
            "recipe": [],
        }

# ================================================================
# サイドバー：プロフィール（決断疲れを減らすため必須項目のみ最初に表示）
# ================================================================
with st.sidebar:
    st.header("🏷️ ニックネーム")
    st.caption("記録を自分専用に分けて保存します")
    nickname_input = st.text_input(
        "ニックネームを入力してね",
        value=st.session_state.user_id,
        placeholder="例：たなか",
        label_visibility="collapsed",
    )
    new_user_id = sanitize_user_id(nickname_input)
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        st.query_params["user"] = new_user_id
        # ニックネームが変わったら、その人のデータを読み直す
        st.session_state.meal_log = load_meal_log_from_firebase(new_user_id)
        st.rerun()

    if st.session_state.user_id:
        st.caption(f"✅「{st.session_state.user_id}」として記録中")
    else:
        st.warning("⚠️ ニックネームを入れると記録できます")

    st.divider()

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
    ideal = calc_ideal_nutrients(required, gender)
    st.metric("1日の目安カロリー", f"{required} kcal")

    if gemini_ready:
        st.success("✅ AIが使える状態です")
    else:
        st.error("❌ APIキー未設定")

    if FIREBASE_URL:
        st.success("✅ データベースに接続済み")
    else:
        st.error("❌ FIREBASE_DB_URL 未設定")

    if CV2_AVAILABLE and _FACE_CASCADE is not None:
        st.success("✅ 画像検出機能（お皿・顔）が使えます")
    else:
        st.warning("⚠️ 画像検出機能は現在利用できません")
        with st.expander("詳細"):
            st.caption(f"CV2_AVAILABLE: {CV2_AVAILABLE}")
            if not CV2_AVAILABLE:
                st.caption(f"cv2 import error: {_cv2_import_error}")
            if _cascade_load_error:
                st.caption(f"cascade error: {_cascade_load_error}")

    with st.expander("💾 保存状態（デバッグ用）", expanded=False):
        st.caption(f"現在の記録件数: {len(st.session_state.meal_log)}")
        if st.session_state.get("_fb_save_error"):
            st.caption(f"⚠️ 保存エラー: {st.session_state._fb_save_error}")
        if st.session_state.get("_fb_load_error"):
            st.caption(f"⚠️ 読み込みエラー: {st.session_state._fb_load_error}")
        if st.button("🔄 データベースから再読み込み"):
            st.session_state.meal_log = load_meal_log_from_firebase(st.session_state.user_id)
            st.rerun()

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

if not st.session_state.user_id:
    st.info("👈 左のサイドバーで「ニックネーム」を入力すると、あなた専用の記録が始まります！")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🍽️ 食事を記録", "🏃 運動を記録", "📊 今日のまとめ", "📈 履歴グラフ", "🎨 写真を加工",
])

# ================================================================
# タブ1：食事を記録
# ================================================================
with tab1:
    st.subheader("料理写真をアップロードして記録")
    uploaded_file = st.file_uploader("写真を選ぶ", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:
        analyze_clicked = st.button("🔍 料理を分析して記録", type="primary", use_container_width=True)
        st.caption("💡 フィルターやモザイクなど写真の加工だけしたい場合は「🎨 写真を加工」タブへ")
    else:
        analyze_clicked = False

    if analyze_clicked:
        if not gemini_ready:
            st.error("APIキーが設定されていません")
        else:
            image = Image.open(uploaded_file).convert("RGB")
            col_img, col_result = st.columns([1, 1])

            with col_img:
                st.image(image, caption="アップロードした写真", use_container_width=True)

            with st.spinner("🤖 Gemini AIが料理を認識中..."):
                dishes = estimate_calories_gemini(image)

            # 【自作CV処理】HSV色空間で彩りを分析（APIを使わず自分で計算）
            with st.spinner("🎨 彩りを分析中..."):
                color_result = analyze_color_variety(image)

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
                    "vitamins": d.get("vitamins", []),
                    "minerals": d.get("minerals", []),
                    "color_score": color_result["score"],
                })
            persist_log()

            # ---- 彩り分析の結果を写真の下に表示 ----
            with col_img:
                score = color_result["score"]
                if score >= 75:
                    score_color, score_label = "#27AE60", "彩り豊か"
                elif score >= 50:
                    score_color, score_label = "#E67E22", "ふつう"
                else:
                    score_color, score_label = "#E74C3C", "色が偏りぎみ"

                # 検出した色を割合の帯グラフで表示
                bar_segments = ""
                for key, ratio in sorted(color_result["ratios"].items(), key=lambda x: -x[1]):
                    if ratio < 3:
                        continue
                    hexcol = COLOR_CATEGORIES[key]["hex"]
                    bar_segments += f'<div style="background:{hexcol}; width:{ratio:.1f}%; height:100%;"></div>'

                color_chips = "".join(
                    f"<span style='display:inline-flex; align-items:center; gap:4px; margin:3px 6px 3px 0; font-size:11px; color:#5A5462;'>"
                    f"<span style='width:11px; height:11px; border-radius:50%; background:{COLOR_CATEGORIES[k]['hex']}; display:inline-block;'></span>"
                    f"{COLOR_CATEGORIES[k]['label']} {color_result['ratios'][k]:.0f}%</span>"
                    for k in color_result["present_colors"]
                )

                st.markdown(f"""
                <div class="pop-card" style="background:#FFFFFF; margin-top:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:800; font-size:15px;">🎨 彩りスコア</span>
                        <span class="badge" style="background:{score_color};">{score}点 / {score_label}</span>
                    </div>
                    <div style="display:flex; height:16px; border-radius:999px; overflow:hidden;
                                border:2px solid #2D2A32; margin:10px 0 8px 0;">
                        {bar_segments}
                    </div>
                    <div style="margin-bottom:6px;">{color_chips}</div>
                    <div style="font-size:12px; color:#8A8494; font-weight:500;">{color_result['message']}</div>
                </div>
                """, unsafe_allow_html=True)

                advice = missing_color_advice(color_result["present_colors"])
                if advice:
                    st.caption(f"💡 足すとよい色：{advice}")
                st.caption("※ 彩りスコアは写真をHSV色空間に変換し、自作の色分類アルゴリズムで算出しています")

            with col_result:
                total_cal = sum(d["calories"] for d in dishes)
                st.success(f"✅ {len(dishes)}品を認識しました！（合計 {total_cal} kcal）")

                for d in dishes:
                    nut = d["nutrients"]
                    vit_tags = "".join(
                        f"<span class='badge' style='background:var(--sunny); color:#2D2A32; margin-right:4px;'>{v}</span>"
                        for v in d.get("vitamins", [])
                    )
                    min_tags = "".join(
                        f"<span class='badge' style='background:var(--green); margin-right:4px;'>{m}</span>"
                        for m in d.get("minerals", [])
                    )
                    tag_row = ""
                    if vit_tags or min_tags:
                        tag_row = f"<div style='margin-top:8px; display:flex; flex-wrap:wrap; gap:4px;'>{vit_tags}{min_tags}</div>"
                    st.markdown(f"""
                    <div class="dish-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; font-size:16px;">🍴 {d['name']}</span>
                            <span class="badge" style="background:var(--coral);">{d['calories']} kcal</span>
                        </div>
                        <div style="font-size:12px; color:#8A8494; margin-top:6px; font-weight:500;">
                            炭水化物 {nut['carb']}g（糖質 {nut['sugar']}g）・タンパク質 {nut['protein']}g・脂質 {nut['fat']}g・塩分 {nut['salt']}g
                        </div>
                        <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                            <span class="badge" style="background:var(--turquoise);">
                                確信度 {d['confidence']*100:.0f}%
                            </span>
                        </div>
                        {tag_row}
                    </div>
                    """, unsafe_allow_html=True)
                st.caption("💡 1日の栄養バランスは「今日のまとめ」タブでまとめて確認できます")

            # ---- 【自作CV処理】インスタ映え加工 ----
            st.session_state["_last_uploaded_image"] = image

    # 写真の加工（フィルター・モザイクなど）は「🎨 写真を加工」タブでできます
    if st.session_state.get("_last_uploaded_image") is not None:
        st.info("🎨 写真の加工は「写真を加工」タブでできます")

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
        persist_log()

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

    consumed_nutrients = {"carb": 0, "sugar": 0, "protein": 0, "fat": 0, "salt": 0.0, "vitamins": [], "minerals": []}
    for r in today_records:
        if r["type"] == "meal" and "nutrients" in r:
            for k in ["carb", "sugar", "protein", "fat", "salt"]:
                consumed_nutrients[k] += r["nutrients"].get(k, 0)
            consumed_nutrients["vitamins"] += r.get("vitamins", [])
            consumed_nutrients["minerals"] += r.get("minerals", [])
    consumed_nutrients["salt"] = round(consumed_nutrients["salt"], 1)

    ratio = net_cal / required * 100 if required > 0 else 0

    # ---- 🤖 AI分析（一番上に配置） ----
    if st.button("🤖 AIで今日を分析（アドバイス＋次のおすすめ献立）", type="primary", use_container_width=True):
        if not gemini_ready:
            st.error("APIキーが設定されていません")
        else:
            with st.spinner("AIが1日分をまとめて分析中..."):
                result = generate_ai_advice(net_cal, required, consumed_nutrients, ideal, today_records)
            st.session_state["_ai_result"] = result

    ai_result = st.session_state.get("_ai_result")
    if ai_result:
        st.markdown(f"""
        <div class="advice-card">
            <div style="font-weight:800; color:var(--purple-dark); margin-bottom:8px; font-size:15px;">🤖 今日1日のアドバイス</div>
            {ai_result['advice']}
        </div>
        """, unsafe_allow_html=True)

        if ai_result.get("menu_name"):
            recipe_steps = "".join(
                f"<li style='margin-bottom:6px;'>{step}</li>" for step in ai_result.get("recipe", [])
            )
            st.markdown(f"""
            <div class="dish-card" style="border-color:var(--green); box-shadow:4px 4px 0px var(--green); margin-top:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:800; font-size:16px;">🍳 次の食事のおすすめ：{ai_result['menu_name']}</span>
                </div>
                <div style="font-size:13px; color:#8A8494; margin-top:6px; font-weight:500;">
                    {ai_result['menu_reason']}
                </div>
                <div style="margin-top:10px;">
                    <div style="font-weight:700; font-size:13px; margin-bottom:4px;">かんたんな作り方</div>
                    <ol style="font-size:13px; color:#5A5462; padding-left:20px; margin:0;">
                        {recipe_steps}
                    </ol>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("摂取カロリー", f"+{meal_cal} kcal")
    with col2:
        st.metric("運動で消費", f"-{exercise_cal} kcal")
    with col3:
        st.metric("実質カロリー", f"{net_cal} / {required} kcal")

    pop_bar(ratio / 100)
    st.caption("🔴 摂取した分　🔵 まだ足りない分")
    if ratio < 50:
        st.warning(f"⚠️ カロリーが不足しています。あと {required - net_cal} kcal 必要です。")
    elif ratio < 90:
        st.info(f"✅ もう少しで目標達成！あと {required - net_cal} kcal です。")
    elif ratio <= 110:
        st.success("🎉 今日のカロリーは理想的です！")
    else:
        st.error(f"⚠️ {net_cal - required} kcal オーバーです。運動で消費しましょう。")

    st.subheader("🥗 五大栄養素のバランス")
    st.caption("炭水化物・タンパク質・脂質は「目安まで摂りたい」栄養素、糖質・塩分は「摂りすぎ注意」の栄養素です")

    col_a, col_b, col_c = st.columns(3)
    main_cols = {"carb": col_a, "protein": col_b, "fat": col_c}
    for key, col in main_cols.items():
        with col:
            status, color, nratio = nutrient_status(consumed_nutrients[key], ideal[key])
            st.metric(NUTRIENT_LABELS[key], f"{consumed_nutrients[key]}g / {ideal[key]}g")
            pop_bar(nratio / 100, height=14)
            st.markdown(
                f"<span class='badge' style='background:{color};'>{status}</span>",
                unsafe_allow_html=True,
            )

    col_d, col_e = st.columns(2)
    limit_cols = {"sugar": col_d, "salt": col_e}
    for key, col in limit_cols.items():
        with col:
            status, color, nratio = limit_status(consumed_nutrients[key], ideal[key])
            unit = "g"
            st.metric(f"{NUTRIENT_LABELS[key]}（上限目安）", f"{consumed_nutrients[key]}{unit} / {ideal[key]}{unit}")
            pop_bar(nratio / 100, height=14)
            st.markdown(
                f"<span class='badge' style='background:{color};'>{status}</span>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    vit_set = sorted(set(consumed_nutrients.get("vitamins", [])))
    min_set = sorted(set(consumed_nutrients.get("minerals", [])))
    vit_tags = "".join(f"<span class='badge' style='background:var(--sunny); color:#2D2A32; margin:2px;'>{v}</span>" for v in vit_set)
    min_tags = "".join(f"<span class='badge' style='background:var(--green); margin:2px;'>{m}</span>" for m in min_set)
    st.markdown(f"""
    <div class="pop-card" style="background:#FFFFFF;">
        <div style="font-weight:800; margin-bottom:8px;">🌈 今日摂れたビタミン・ミネラル</div>
        <div style="margin-bottom:4px;">{vit_tags if vit_tags else "<span style='color:#8A8494; font-size:13px;'>まだ記録がありません</span>"}</div>
        <div>{min_tags}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 今日の平均彩りスコア（自作CV処理の結果を1日単位で集計） ----
    color_scores = [r["color_score"] for r in today_records if r.get("color_score") is not None]
    if color_scores:
        avg_color = int(round(sum(color_scores) / len(color_scores)))
        if avg_color >= 75:
            c_col, c_label = "#27AE60", "彩り豊かな1日でした"
        elif avg_color >= 50:
            c_col, c_label = "#E67E22", "まずまずの彩りです"
        else:
            c_col, c_label = "#E74C3C", "色が偏りぎみです。野菜を足しましょう"
        st.markdown(f"""
        <div class="pop-card" style="background:#FFFFFF; margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:800; font-size:15px;">🎨 今日の平均彩りスコア</span>
                <span class="badge" style="background:{c_col};">{avg_color}点</span>
            </div>
            <div style="font-size:12px; color:#8A8494; margin-top:6px; font-weight:500;">
                {c_label}（{len(color_scores)}件の食事写真から算出）
            </div>
        </div>
        """, unsafe_allow_html=True)
        pop_bar(avg_color / 100, height=14)

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
                    persist_log()
                    st.rerun()
    else:
        st.info("📸 まずは「食事を記録」タブから、今日食べたものを撮ってみましょう")

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
        persist_log()
        st.success("すべての記録を削除しました")
        st.rerun()

# ================================================================
# タブ5：写真を加工（フィルター・お皿検出・顔モザイクなど）
# ================================================================
with tab5:
    st.subheader("🎨 写真を加工する")
    st.caption("AIは使わず、画像処理・古典的なCVアルゴリズムをすべて自分のコードで実装しています（トークンは消費しません）")

    edit_upload = st.file_uploader(
        "加工したい写真を選ぶ", type=["jpg", "jpeg", "png", "webp"], key="edit_tab_uploader"
    )
    if edit_upload is not None:
        # アップロードした瞬間、選び直すまで同じ画像を使い回す
        new_bytes = edit_upload.getvalue()
        if st.session_state.get("_edit_upload_bytes") != new_bytes:
            st.session_state["_last_uploaded_image"] = Image.open(edit_upload).convert("RGB")
            st.session_state["_edit_upload_bytes"] = new_bytes

    src_img = st.session_state.get("_last_uploaded_image")

    if src_img is None:
        st.info("📸 上のアップロード欄から写真を選ぶか、「食事を記録」タブで写真を分析すると、ここで加工できます")
    else:
        # ---- 左：プレビュー／右：操作パネル を横並びにして1画面に収める ----
        col_preview, col_controls = st.columns([1, 1], gap="medium")

        with col_controls:
            mode = st.radio(
                "加工モード",
                ["元の写真", "🎯 範囲を選んで料理を補正", "🍽️ 料理だけ美味しそうに",
                 "🍂 低彩度・暖色寄り", "🌿 自然な彩度高め", "🔥 青み削り",
                 "🎚️ カスタム調整", "🍽️ お皿検出モザイク", "🙈 顔モザイク",
                 "🍽️👤 料理と人、それぞれに合う色味"],
                key="edit_mode",
            )

            if mode == "🎯 範囲を選んで料理を補正":
                st.caption("スライダーで料理を囲む大まかな範囲を選ぶと、そこからAIなしで輪郭を自動検出します")
                iw, ih = src_img.size
                x_range = st.slider("横方向の範囲", 0, iw, (int(iw * 0.1), int(iw * 0.9)), key="roi_x")
                y_range = st.slider("縦方向の範囲", 0, ih, (int(ih * 0.4), int(ih * 0.95)), key="roi_y")

            if mode == "🎚️ カスタム調整":
                st.caption("インスタの編集機能と同じ-100〜100のスライダーです。動かすと右のプレビューが即座に変わります")
                s_brightness = st.slider("明るさ", -100, 100, 10, key="s_brightness")
                s_contrast = st.slider("コントラスト", -100, 100, -5, key="s_contrast")
                s_warmth = st.slider("暖かさ", -100, 100, 10, key="s_warmth")
                s_saturation = st.slider("彩度", -100, 100, -10, key="s_saturation")
                s_shadows = st.slider("シャドウ", -100, 100, 5, key="s_shadows")

            if mode in ("🍽️ お皿検出モザイク", "🙈 顔モザイク"):
                if not CV2_AVAILABLE or _FACE_CASCADE is None:
                    st.warning(
                        "⚠️ この環境では画像検出ライブラリ（OpenCV）を読み込めなかったため、"
                        "この機能は現在使用できません。"
                    )
                else:
                    mosaic_grain = st.radio(
                        "モザイクの粗さ", ["🔲 荒め", "🔳 細かめ"],
                        horizontal=True, key="mosaic_grain",
                    )

        # ---- プレビューを常に自動計算（ボタン不要・選択/スライダー変更で即反映） ----
        detect_note = None
        is_coarse = st.session_state.get("mosaic_grain", "🔲 荒め") == "🔲 荒め"

        if mode == "元の写真":
            edited = src_img
        elif mode == "🎯 範囲を選んで料理を補正":
            roi_box = (
                st.session_state.get("roi_x", (0, src_img.width))[0],
                st.session_state.get("roi_y", (0, src_img.height))[0],
                st.session_state.get("roi_x", (0, src_img.width))[1],
                st.session_state.get("roi_y", (0, src_img.height))[1],
            )
            with col_preview:
                st.image(
                    draw_selection_box(src_img, roi_box),
                    caption="選択中の範囲（赤い枠）",
                    use_container_width=True,
                )
            with st.spinner("🔍 GrabCutで料理の輪郭を検出しています..."):
                edited, coverage = enhance_food_in_selection(src_img, roi_box)
            detect_note = f"✅ 選んだ範囲の中から、料理らしき部分（面積の約{coverage*100:.0f}%）を検出して補正しました"
        elif mode == "🍽️ 料理だけ美味しそうに":
            with col_preview:
                with st.spinner("🔍 お皿を検出して、料理だけ色味を補正しています..."):
                    edited, plate_detected = enhance_food_only(src_img)
            detect_note = "✅ お皿を検出し、料理部分だけ食欲をそそる発色に補正しました" if plate_detected else "⚠️ お皿を検出できず、画面下側を目安に補正しました"
        elif mode == "🎚️ カスタム調整":
            edited = apply_insta_adjustments(
                src_img,
                brightness=st.session_state.get("s_brightness", 10),
                contrast=st.session_state.get("s_contrast", -5),
                warmth=st.session_state.get("s_warmth", 10),
                saturation=st.session_state.get("s_saturation", -10),
                shadows=st.session_state.get("s_shadows", 5),
            )
        elif mode == "🍽️ お皿検出モザイク":
            if not CV2_AVAILABLE or _FACE_CASCADE is None:
                edited = src_img
            else:
                plate_block = 26 if is_coarse else 10
                with col_preview:
                    with st.spinner("🔍 Hough変換でお皿の形（円）を検出中..."):
                        edited, plate_detected = mosaic_background_outside_plate(src_img, block=plate_block)
                detect_note = "✅ 円形のお皿を検出しました" if plate_detected else "⚠️ お皿の形を検出できず、中央を基準にモザイク化しました"
        elif mode == "🙈 顔モザイク":
            if not CV2_AVAILABLE or _FACE_CASCADE is None:
                edited = src_img
            else:
                face_divisor = 4 if is_coarse else 14
                with col_preview:
                    with st.spinner("🔍 Haar Cascadeで顔を検出中..."):
                        edited, n_faces = mosaic_faces(src_img, block_divisor=face_divisor)
                detect_note = f"✅ {n_faces}件の顔を検出してモザイク化しました" if n_faces > 0 else "人の顔は検出されませんでした（そのままの写真です）"
        elif mode == "🍽️👤 料理と人、それぞれに合う色味":
            with col_preview:
                with st.spinner("🔍 お皿と顔を検出して、領域ごとに色味を変えています..."):
                    edited, n_faces = region_aware_food_portrait_enhance(src_img)
            detect_note = (
                f"✅ 料理は食欲をそそる発色に、人物（{n_faces}件検出）の肌は自然な色味に分けて加工しました"
                if n_faces > 0 else
                "✅ 料理部分は食欲をそそる発色に加工しました（顔は検出されませんでした）"
            )
        else:
            style_key_map = {
                "🍂 低彩度・暖色寄り": "muted_warm",
                "🌿 自然な彩度高め": "natural_vivid",
                "🔥 青み削り": "reduce_blue",
            }
            edited = generate_instagram_photo(src_img, style_key_map[mode])

        with col_preview:
            st.image(edited, caption=f"プレビュー（{mode}）", use_container_width=True)
            if detect_note:
                st.caption(detect_note)

            buf = io.BytesIO()
            edited.convert("RGB").save(buf, format="JPEG", quality=92)
            st.download_button(
                "⬇️ この写真をダウンロード",
                data=buf.getvalue(),
                file_name="mogureco_edited.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )