import streamlit as st
import cv2
import numpy as np
from PIL import Image
import json
import re
import io

# ================================================================
# ページ設定
# ================================================================
st.set_page_config(
    page_title="🍽 食事診断アプリ（CV × Gemini）",
    page_icon="🍽",
    layout="wide",
)

st.markdown("""
<style>
    .stApp { background: #FAF7F2; }
    .box-title { font-size: 1.9rem; font-weight: 800; margin-bottom: 0.2rem; }
    .sub-title { color: #8A8494; margin-bottom: 1.4rem; }
    .result-card {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 16px 20px;
        margin-top: 10px;
        border: 2.5px solid #E6DFD3;
        box-shadow: 3px 3px 0px rgba(45,42,50,0.08);
    }
    .dish-name { font-size: 1.15rem; font-weight: 800; color: #E8534F; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="box-title">🍽 食事診断アプリ（OpenCV × Gemini ハイブリッド）</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">画像認識の大部分はローカルのOpenCVで処理し、料理名の特定とアドバイスのみをGeminiに任せます</div>', unsafe_allow_html=True)


# ================================================================
# サイドバー：APIキー
# ================================================================
def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return None

with st.sidebar:
    st.header("⚙️ 設定")
    secret_key = get_api_key()
    if secret_key:
        st.success("APIキーは secrets から読み込まれています")
        api_key = secret_key
    else:
        api_key = st.text_input("Gemini API キー", type="password", help="料理名の特定・アドバイス生成にのみ使用します")

    st.divider()
    st.caption("検出パラメータ")
    canny_low = st.slider("Cannyエッジ下限", 10, 150, 50, 5)
    canny_high = st.slider("Cannyエッジ上限", 50, 300, 150, 5)
    min_area_ratio = st.slider("検出する最小面積（画像全体に対する割合）", 0.005, 0.2, 0.02, 0.005)


# ================================================================
# OpenCV 処理関数
# ================================================================
def apply_clahe(img_bgr: np.ndarray) -> np.ndarray:
    """暗い場所・影対策のコントラスト補正（CLAHE）"""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)


def detect_regions(img_bgr: np.ndarray, low: int, high: int, min_ratio: float, max_regions: int = 8):
    """Canny + findContours でお皿・料理領域を検出"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, low, high)
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = img_bgr.shape[:2]
    min_area = h * w * min_ratio

    regions = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        regions.append({"contour": c, "bbox": (x, y, bw, bh), "area": area})

    regions.sort(key=lambda r: r["area"], reverse=True)
    return regions[:max_regions]


def draw_boxes(img_bgr: np.ndarray, regions: list) -> np.ndarray:
    """検出領域に番号付き緑色バウンディングボックスを描画"""
    out = img_bgr.copy()
    for i, r in enumerate(regions):
        x, y, w, h = r["bbox"]
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 3)
        label = f"#{i + 1}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)
        label_y = max(y - 10, th + 10)
        cv2.rectangle(out, (x, label_y - th - 8), (x + tw + 8, label_y + 4), (0, 255, 0), -1)
        cv2.putText(out, label, (x + 4, label_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    return out


def get_crop_and_mask(img_bgr: np.ndarray, region: dict):
    """バウンディングボックスで切り抜き、輪郭内部のマスクを作成"""
    x, y, w, h = region["bbox"]
    crop = img_bgr[y:y + h, x:x + w].copy()
    mask = np.zeros((h, w), dtype=np.uint8)
    shifted_contour = region["contour"] - np.array([x, y])
    cv2.drawContours(mask, [shifted_contour], -1, 255, thickness=-1)
    return crop, mask


def analyze_colors(crop_bgr: np.ndarray, mask: np.ndarray) -> dict:
    """輪郭内部のHSV色彩比率を計算（緑・赤茶・黄・白）"""
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    inside = mask > 0
    total = int(np.count_nonzero(inside))

    if total == 0:
        return {"green": 0.0, "red_brown": 0.0, "yellow": 0.0, "white": 0.0}

    def pct(cond):
        return round(float(np.count_nonzero(cond & inside)) / total * 100, 1)

    green = pct((h >= 35) & (h <= 85))
    red_brown = pct(((h >= 0) & (h <= 15)) | ((h >= 170) & (h <= 180)))
    yellow = pct((h > 15) & (h < 35))
    white = pct((s < 50) & (v > 150))

    return {"green": green, "red_brown": red_brown, "yellow": yellow, "white": white}


# ================================================================
# Gemini API 連携
# ================================================================
def call_gemini_diagnosis(api_key: str, pil_image: Image.Image, area_px: int, colors: dict) -> dict:
    """CVの数値データ＋切り抜き画像から、料理名とアドバイスを生成"""
    try:
        import google.generativeai as genai
    except ImportError:
        return {"dish_name": "エラー", "advice": "google-generativeai ライブラリがインストールされていません（pip install google-generativeai）"}

    prompt = f"""あなたは管理栄養士です。以下はコンピュータビジョン(OpenCV)で解析した、ある料理1皿分の画像データです。

【CV解析データ】
- 輪郭面積: {area_px} px
- 緑色（野菜など）の割合: {colors['green']}%
- 赤茶色（肉・揚げ物など）の割合: {colors['red_brown']}%
- 黄色（卵・カレーなど）の割合: {colors['yellow']}%
- 白色（米・豆腐など）の割合: {colors['white']}%

添付された切り抜き画像を見て、以下を行ってください。
1. dish_name: この料理名を推測し、一言（10文字程度）で表してください
2. advice: 上記のCV色彩データの数値を根拠として言及しながら、簡潔な栄養アドバイスを2文程度で述べてください

出力は必ず次のJSON形式のみとし、前後に説明文やMarkdown記法（```など）を一切付けないでください。
{{"dish_name": "...", "advice": "..."}}
"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        response = model.generate_content([prompt, pil_image])
        text = (response.text or "").strip()
        text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text.strip()).strip()
        data = json.loads(text)
        return {
            "dish_name": data.get("dish_name", "不明"),
            "advice": data.get("advice", ""),
        }
    except json.JSONDecodeError:
        return {"dish_name": "解析エラー", "advice": "Geminiの応答をJSONとして解析できませんでした。もう一度お試しください。"}
    except Exception as e:
        return {"dish_name": "エラー", "advice": f"AI診断中にエラーが発生しました: {e}"}


# ================================================================
# メイン画面
# ================================================================
uploaded_file = st.file_uploader("食事の写真をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is None:
    st.info("📸 まずは写真をアップロードしてください。お皿全体が写っているとうまく検出できます。")
    st.stop()

# ---- 画像読み込み（PIL RGB → OpenCV BGR） ----
pil_original = Image.open(uploaded_file).convert("RGB")
img_rgb = np.array(pil_original)
img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

# ---- 1. 前処理（CLAHEコントラスト補正） ----
st.subheader("① 前処理：コントラスト補正（CLAHE）")
clahe_bgr = apply_clahe(img_bgr)

col_before, col_after = st.columns(2)
with col_before:
    st.image(img_rgb, caption="アップロード画像（元画像）", use_container_width=True)
with col_after:
    st.image(cv2.cvtColor(clahe_bgr, cv2.COLOR_BGR2RGB), caption="コントラスト補正後", use_container_width=True)

# ---- 2. 対象検出・切り抜き ----
st.subheader("② お皿・料理の自動検出")
regions = detect_regions(clahe_bgr, canny_low, canny_high, min_area_ratio)

if not regions:
    st.warning("⚠️ お皿・料理の領域が検出できませんでした。サイドバーの検出パラメータ（最小面積や閾値）を調整してみてください。")
    st.stop()

boxed_bgr = draw_boxes(clahe_bgr, regions)
st.image(cv2.cvtColor(boxed_bgr, cv2.COLOR_BGR2RGB), caption=f"{len(regions)} 件の領域を検出しました", use_container_width=True)

st.subheader("③ 診断したい「自分のお皿」を選択してください")

crops_info = []
n_cols = min(len(regions), 4)
cols = st.columns(n_cols)
for i, region in enumerate(regions):
    crop_bgr, mask = get_crop_and_mask(clahe_bgr, region)
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    with cols[i % n_cols]:
        st.image(crop_rgb, caption=f"#{i + 1}", use_container_width=True)
        checked = st.checkbox(f"#{i + 1} を選択", key=f"select_{i}")
    crops_info.append({"index": i, "crop_bgr": crop_bgr, "crop_rgb": crop_rgb, "mask": mask, "area": region["area"], "selected": checked})

selected_items = [c for c in crops_info if c["selected"]]

if not selected_items:
    st.info("👆 上のチェックボックスから、解析したいお皿を選んでください。")
    st.stop()

# ---- 3 & 4. 色彩・面積解析 + Gemini診断 ----
st.subheader("④ 色彩・面積解析 と AI診断")

for item in selected_items:
    idx = item["index"]
    colors = analyze_colors(item["crop_bgr"], item["mask"])
    area_px = int(item["area"])

    st.markdown(f"#### #{idx + 1} の解析結果")
    img_col, data_col = st.columns([1, 2])

    with img_col:
        st.image(item["crop_rgb"], use_container_width=True)
        st.metric("輪郭面積", f"{area_px:,} px")

    with data_col:
        color_labels = {
            "green": ("🟢 緑色（野菜など）", "#6BCB77"),
            "red_brown": ("🟤 赤茶色（肉・揚げ物など）", "#C0603F"),
            "yellow": ("🟡 黄色（卵・カレーなど）", "#FFC93C"),
            "white": ("⚪ 白色（米・豆腐など）", "#B8B0A0"),
        }
        for key, (label, color) in color_labels.items():
            pct = colors[key]
            st.markdown(f"**{label}**：{pct}%")
            st.progress(min(pct / 100, 1.0))

    diagnose_key = f"diagnose_{idx}"
    result_key = f"result_{idx}"

    if st.button(f"🤖 #{idx + 1} をGeminiで診断する", key=diagnose_key):
        if not api_key:
            st.error("Gemini APIキーが設定されていません。サイドバーから入力してください。")
        else:
            with st.spinner("Geminiが料理名とアドバイスを生成中..."):
                crop_pil = Image.fromarray(item["crop_rgb"])
                result = call_gemini_diagnosis(api_key, crop_pil, area_px, colors)
            st.session_state[result_key] = result

    if result_key in st.session_state:
        result = st.session_state[result_key]
        st.markdown(f"""
        <div class="result-card">
            <div class="dish-name">🍴 {result['dish_name']}</div>
            <div style="margin-top:8px; line-height:1.7; color:#2D2A32;">{result['advice']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
