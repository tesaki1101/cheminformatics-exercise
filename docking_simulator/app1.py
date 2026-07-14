import streamlit as st
import pandas as pd
import pickle
import os
from rdkit import Chem
from rdkit.Chem import Descriptors
from streamlit_ketcher import st_ketcher

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


st.subheader("🛠️ 1. 分子エディタで構造を描く")
st.markdown("""
右側のツール（炭素・窒素・酸素やベンゼン環など）を選んで、中央のキャンバスに構造を描いてください。
描くとすぐに下の結果が自動的に更新されます。
""")

# --- 分子エディタ（公式コンポーネント。ページ再読み込みなしでSMILESを直接取得） ---
current_structure = st_ketcher(value="", height=420)

st.divider()

# --- 2. ドッキング結果の出力エリア ---
st.subheader("🔮 2. ドッキング結果（AIモデルによる予測）")

if not current_structure:
    st.info("💡 上のエディタで分子を描くと、ここに結果が表示されます。")
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
2. すぐに結果が自動的に表示される

### 🧬 このアプリについて
表示される点数は、RDKitで計算した201種類の分子記述子（分子量・LogP・極性表面積など）をもとに、
実際のドッキング計算結果から学習したLightGBMモデルが予測した**ドッキングスコア（kcal/mol）**を、
分かりやすい0〜100点に変換したものです（-14 kcal/mol以下→100点、4 kcal/mol以上→0点）。
点数が高いほど、標的タンパク質と強く結合すると予測されます。
""")
