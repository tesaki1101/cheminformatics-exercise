import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pickle
import os
import json
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
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")
    with open(model_path, "rb") as f:
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


# --- URLのクエリパラメータから、直前にエディタで送信されたSMILESを取得 ---
# （「解析する」ボタンを押すとページがこのパラメータ付きで再読み込みされる仕組み）
query_smiles = st.query_params.get("smiles", "")

st.subheader("🛠️ 1. 分子エディタ（JSME）で構造を描く")
st.markdown("""
右側のツール（炭素 C、窒素 N、酸素 O やベンゼン環など）を選んで、中央のキャンバスに構造を描いてください。
描き終わったら、エディタ内の **「この構造で解析する」** ボタンを押すと、下の解析結果が自動的に更新されます。
""")

# --- JSME埋め込み ---
# 値をStreamlitへ直接返すことはできないため、
# 「解析する」ボタンを押すとページ自身をURLパラメータ付きで再読み込みし、
# Python側がst.query_params経由でSMILESを受け取る仕組みにしている。
jsme_html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="text/javascript" src="https://jsme-editor.github.io/dist/jsme/jsme.nocache.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; font-family: sans-serif; }}
        #jsme_container {{ width: 100%; height: 340px; }}
        #controls {{ margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
        button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background-color: #ff4b4b;
            color: white;
            font-size: 1em;
            cursor: pointer;
        }}
        button:hover {{ background-color: #e03e3e; }}
        #status_msg {{ color: #666; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div id="jsme_container"></div>
    <div id="controls">
        <button onclick="submitSmiles()">🚀 この構造で解析する</button>
        <span id="status_msg"></span>
    </div>

    <script>
        var jsmeApplet;
        var initialSmiles = {json.dumps(query_smiles)};

        // JSMEエディタが読み込まれたら自動実行
        function jsmeOnLoad() {{
            jsmeApplet = new JSApplet.JSME("jsme_container", "100%", "340px", {{
                "options" : "query,nocanonical,paste"
            }});
            // 前回解析した構造があれば、そのまま再表示する
            if (initialSmiles) {{
                try {{
                    jsmeApplet.readGenericMolecularInput(initialSmiles);
                }} catch (e) {{ /* 復元に失敗しても無視 */ }}
            }}
        }}

        function submitSmiles() {{
            var smiles = jsmeApplet.smiles();
            if (!smiles) {{
                document.getElementById("status_msg").innerText = "先に構造を描いてください";
                return;
            }}
            document.getElementById("status_msg").innerText = "解析中...";
            var url = window.top.location.origin + window.top.location.pathname
                       + "?smiles=" + encodeURIComponent(smiles);
            window.top.location.href = url;
        }}
    </script>
</body>
</html>
"""

components.html(jsme_html_code, height=400, scrolling=False)

st.divider()

# --- 手動でSMILESを試したい場合の入力欄（任意） ---
with st.expander("✏️ SMILES文字列を直接入力して試す（上級者向け）"):
    manual_smiles = st.text_input(
        "SMILESを直接入力",
        placeholder="例）c1ccccc1N"
    )
    manual_run = st.button("この文字列で解析する")

# --- どちらのSMILESを解析対象にするか決定 ---
if manual_run and manual_smiles.strip():
    current_structure = manual_smiles.strip()
elif query_smiles:
    current_structure = query_smiles.strip()
else:
    current_structure = ""

st.divider()

# --- 2. ドッキング結果の出力エリア ---
st.subheader("🔮 2. ドッキング結果（AIモデルによる予測）")

if not current_structure:
    st.info("💡 上のエディタで分子を描いて「この構造で解析する」を押すと、ここに結果が表示されます。")
else:
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
            st.caption("💻 解析されたSMILES")
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
2. 「🚀 この構造で解析する」を押す
3. ページが自動的に更新され、結果が表示される

### 🧬 このアプリについて
表示される点数は、RDKitで計算した201種類の分子記述子（分子量・LogP・極性表面積など）をもとに、
実際のドッキング計算結果から学習したLightGBMモデルが予測した**ドッキングスコア（kcal/mol）**を、
分かりやすい0〜100点に変換したものです（-14 kcal/mol以下→100点、4 kcal/mol以上→0点）。
点数が高いほど、標的タンパク質と強く結合すると予測されます。
""")
