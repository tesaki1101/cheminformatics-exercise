import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pickle
from rdkit import Chem
from rdkit.Chem import Descriptors

# ページ設定（モバイル・PC双方に最適化）
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」のポケットにぴったりハマる薬を分子エディタで設計しましょう！")


# --- モデルの読み込み（アプリ起動時に1回だけ実行） ---
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)


model = load_model()
FEATURE_NAMES = model.feature_name_  # 学習時と全く同じ順序・名前の特徴量リスト


def calc_features(smiles: str):
    """SMILES文字列からモデルが必要とする201個のRDKit記述子を、学習時と同じ順序で計算する"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    desc_dict = Descriptors.CalcMolDescriptors(mol)
    row = {name: desc_dict.get(name) for name in FEATURE_NAMES}
    return pd.DataFrame([row], columns=FEATURE_NAMES)


def score_to_points(score: float) -> float:
    """
    ドッキングスコア(kcal/mol)を0〜100点に変換する。
    score <= -14 -> 100点、score >= 4 -> 0点、その間は線形補間。
    """
    BEST, WORST = -14.0, 4.0
    clipped = max(BEST, min(WORST, score))
    points = (WORST - clipped) / (WORST - BEST) * 100
    return points


def score_comment(points: float):
    """0〜100点の点数を教育向けのコメントに変換。"""
    if points >= 90:
        return "🎯", "非常に強い結合（特効薬レベル）", "success"
    elif points >= 70:
        return "⭕", "強い結合", "success"
    elif points >= 50:
        return "🔺", "中程度の結合", "warning"
    else:
        return "❌", "弱い結合（結合しにくい）", "error"


st.subheader("🛠️ 1. 分子エディタ（JSME）で構造を描く")
st.markdown("""
右側のツール（炭素 C、窒素 N、酸素 O やベンゼン環など）を選んで、中央のキャンバスに構造を描いてください。
描き終わったら、エディタ内の **「SMILESを取得」** ボタン → **「コピー」** ボタンを押し、下の入力欄に貼り付けてください。
""")

# --- JSME埋め込み（表示専用。値はコピー＆ペーストでStreamlit側に渡す） ---
jsme_html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="text/javascript" src="https://jsme-editor.github.io/dist/jsme/jsme.nocache.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: transparent; font-family: sans-serif; }
        #jsme_container { width: 100%; height: 340px; }
        #controls { margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        #smiles_box {
            flex: 1;
            min-width: 150px;
            padding: 6px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
        }
        button {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            background-color: #ff4b4b;
            color: white;
            cursor: pointer;
        }
        button:hover { background-color: #e03e3e; }
        #copy_msg { color: green; font-size: 0.85em; }
    </style>
</head>
<body>
    <div id="jsme_container"></div>
    <div id="controls">
        <button onclick="extractSmiles()">SMILESを取得</button>
        <input id="smiles_box" type="text" readonly placeholder="ここにSMILESが表示されます">
        <button onclick="copySmiles()">コピー</button>
        <span id="copy_msg"></span>
    </div>

    <script>
        var jsmeApplet;

        // JSMEエディタが読み込まれたら自動実行
        function jsmeOnLoad() {
            jsmeApplet = new JSApplet.JSME("jsme_container", "100%", "340px", {
                "options" : "query,nocanonical,paste"
            });
        }

        function extractSmiles() {
            var smiles = jsmeApplet.smiles();
            document.getElementById("smiles_box").value = smiles;
            document.getElementById("copy_msg").innerText = "";
        }

        function copySmiles() {
            var box = document.getElementById("smiles_box");
            if (!box.value) {
                extractSmiles();
            }
            box.select();
            navigator.clipboard.writeText(box.value).then(function() {
                document.getElementById("copy_msg").innerText = "コピーしました！";
            });
        }
    </script>
</body>
</html>
"""

components.html(jsme_html_code, height=420, scrolling=False)

st.divider()

# --- 2. コピーしたSMILESを貼り付ける欄 ---
st.subheader("📋 2. SMILESを貼り付けて解析")
smiles_input = st.text_input(
    "コピーしたSMILES文字列をここに貼り付けてください",
    placeholder="例）c1ccccc1N"
)

run = st.button("🚀 ドッキング解析を実行", type="primary")

st.divider()

# --- 3. ドッキング結果の出力エリア ---
st.subheader("🔮 3. ドッキング結果（AIモデルによる予測）")

if not run:
    st.info("💡 分子を描いてSMILESを取得・貼り付けたら、「ドッキング解析を実行」を押してください。")
elif not smiles_input.strip():
    st.warning("⚠️ SMILES文字列が入力されていません。エディタで構造を描いてから貼り付けてください。")
else:
    current_structure = smiles_input.strip()
    features = calc_features(current_structure)

    if features is None:
        st.error("❌ このSMILES文字列は正しい化学構造として認識できませんでした。エディタで構造を描き直してみてください。")
    else:
        score = float(model.predict(features)[0])
        points = score_to_points(score)
        icon, label, box_type = score_comment(points)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="📊 判定結果", value=f"{points:.0f} / 100 点")
        with col2:
            st.caption("💻 入力されたSMILES")
            st.code(current_structure, language="text")

        message = f"{icon} **{label}**（{points:.0f}点）"
        if box_type == "success":
            st.success(message)
        elif box_type == "warning":
            st.warning(message)
        else:
            st.error(message)

        st.caption(f"※ AIが予測した結合の強さをもとに、0〜100点に変換したスコアです（参考：ドッキングスコア {score:.2f} kcal/mol）。")

        with st.expander("🔬 AIが見ている分子の特徴量（一部）"):
            preview_cols = ["MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors", "NumRotatableBonds"]
            st.dataframe(features[preview_cols].T.rename(columns={0: "値"}))

st.sidebar.markdown("""
### 💡 使い方
1. 上のエディタで分子を描く
2. 「SMILESを取得」→「コピー」
3. 下の入力欄にペースト
4. 「ドッキング解析を実行」を押す

### 🧬 このアプリについて
表示される点数は、RDKitで計算した201種類の分子記述子（分子量・LogP・極性表面積など）をもとに、
実際のドッキング計算結果から学習したLightGBMモデルが予測した**ドッキングスコア（kcal/mol）**を、
分かりやすい0〜100点に変換したものです（-14 kcal/mol以下→100点、4 kcal/mol以上→0点）。
点数が高いほど、標的タンパク質と強く結合すると予測されます。
""")
