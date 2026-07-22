import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pickle
import os
import time
import random
from rdkit import Chem
from rdkit.Chem import Descriptors

# ページ設定（モバイル・PC双方に最適化）
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質"BCR-ABL"のポケットにぴったりハマる薬を設計しましょう！")

IMATINIB_SMILES = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"

# --- 自作の超シンプルな分子エディタ（Streamlitカスタムコンポーネント） ---
_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple_editor")
_simple_editor_func = components.declare_component("simple_editor", path=_COMPONENT_DIR)


def st_simple_editor(height: int = 380, key=None):
    return _simple_editor_func(height=height, key=key, default="")


# 生徒に伝わりやすい特徴量だけを厳選し、「増やす／減らす」提案文を対応づける
# 形式: 特徴量名 -> (表示名, 値を増やす提案, 値を減らす提案)
FEATURE_HINTS = {
    "MolWt": ("分子の大きさ（分子量）", "鎖を伸ばしたり環を追加したりして、分子を少し大きくしてみましょう", "不要な部分を削って、分子を少しコンパクトにしてみましょう"),
    "MolLogP": ("油になじみやすさ（LogP）", "炭素鎖やベンゼン環を増やして、油になじみやすい部分を増やしてみましょう", "OHやNH2などを増やして、水になじみやすい部分を増やしてみましょう"),
    "TPSA": ("極性表面積（TPSA）", "OH・NH・C=Oなどの極性基を追加してみましょう", "極性基を減らし、炭素骨格を増やしてみましょう"),
    "NumHDonors": ("水素結合ドナー（OH・NHの数）", "OHやNH基を追加してみましょう", "OHやNH基を減らしてみましょう"),
    "NumHAcceptors": ("水素結合アクセプター（N・Oの数）", "窒素や酸素を含む基を追加してみましょう", "窒素や酸素を含む基を減らしてみましょう"),
    "NumAromaticRings": ("芳香環の数", "ベンゼン環などの芳香環を追加してみましょう", "芳香環を減らしてみましょう"),
    "NumAromaticCarbocycles": ("ベンゼン環のような炭素だけの芳香環の数", "ベンゼン環を追加してみましょう", "ベンゼン環を減らしてみましょう"),
    "NumAromaticHeterocycles": ("窒素などを含む芳香環（ピリジンなど）の数", "ピリジンのような複素芳香環を追加してみましょう", "複素芳香環を減らしてみましょう"),
    "NumRotatableBonds": ("分子の柔らかさ（回転可能結合の数）", "鎖を伸ばして柔軟性を増やしてみましょう", "環構造を増やして分子を固くしてみましょう"),
    "RingCount": ("環構造の数", "環を追加してみましょう", "環を減らしてみましょう"),
    "FractionCSP3": ("枝分かれの度合い（sp3炭素の割合）", "枝分かれした構造を増やしてみましょう", "平面的な構造（芳香環など）を増やしてみましょう"),
    "fr_COO": ("カルボン酸（酸性）基の数", "カルボン酸基（-COOH）を追加してみましょう", "カルボン酸基を減らしてみましょう"),
    "fr_amide": ("アミド結合の数", "アミド結合（-C(=O)NH-）を追加してみましょう", "アミド結合を減らしてみましょう"),
    "fr_pyridine": ("ピリジン環の数", "ピリジン環を追加してみましょう", "ピリジン環を減らしてみましょう"),
    "fr_piperzine": ("ピペラジン環の数", "ピペラジン環を追加してみましょう", "ピペラジン環を減らしてみましょう"),
    "fr_ether": ("エーテル結合の数", "エーテル結合（-O-）を追加してみましょう", "エーテル結合を減らしてみましょう"),
    "NumHeteroatoms": ("ヘテロ原子（N・O・Sなど）の数", "窒素や酸素などを含む部分を増やしてみましょう", "炭素・水素だけの部分を増やしてみましょう"),
}


# --- モデルの読み込み（アプリ起動時に1回だけ実行） ---
@st.cache_resource
def load_model():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")
    with open(model_path, "rb") as f:
        return pickle.load(f)


model = load_model()
FEATURE_NAMES = model.feature_name_  # 学習時と全く同じ順序・名前の特徴量リスト


def calc_feature_dict(smiles: str):
    """SMILES文字列からモデルが必要とする201個のRDKit記述子を辞書で計算する"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    desc_dict = Descriptors.CalcMolDescriptors(mol)
    return {name: desc_dict.get(name) for name in FEATURE_NAMES}


def predict_score(feature_dict: dict) -> float:
    row = pd.DataFrame([feature_dict], columns=FEATURE_NAMES)
    return float(model.predict(row)[0])


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


@st.cache_data
def get_imatinib_reference():
    """目標分子（内部参照用、画面には表示しない）の特徴量・スコアを1回だけ計算してキャッシュする"""
    feats = calc_feature_dict(IMATINIB_SMILES)
    score = predict_score(feats)
    return feats, score


def get_suggestions(current_dict: dict, top_n: int = 3):
    """
    現在の分子について、目標分子との比較に基づく改善提案を返す。
    LightGBMのpred_contribで「今のスコアを悪くしている(正の寄与)」特徴量のうち、
    生徒に説明しやすいものだけを取り出し、目標分子の値に近づける方向を提案する。
    """
    imat_feats, _ = get_imatinib_reference()

    row = [current_dict[f] for f in FEATURE_NAMES]
    contrib = model.booster_.predict([row], pred_contrib=True)[0][:-1]  # 最後はbias項なので除く
    feat_contrib = list(zip(FEATURE_NAMES, contrib))

    # 「結合を弱くしている(正の寄与)」かつ「生徒に説明しやすい」特徴量だけを候補にする
    candidates = [(name, c) for name, c in feat_contrib if name in FEATURE_HINTS and c > 0]
    candidates.sort(key=lambda x: -x[1])

    suggestions = []
    for name, _ in candidates:
        label, inc_text, dec_text = FEATURE_HINTS[name]
        cur_val = current_dict[name]
        target_val = imat_feats[name]
        if cur_val is None or target_val is None or abs(cur_val - target_val) < 1e-6:
            continue
        text = inc_text if cur_val < target_val else dec_text
        suggestions.append({
            "label": label,
            "text": text,
            "current": cur_val,
            "target": target_val,
        })
        if len(suggestions) >= top_n:
            break
    return suggestions


st.subheader("🛠️ 1. 分子エディタで構造を描く")
st.markdown("""
結合ボタンを選んだら、原子を押さえたままドラッグしてつなげてください。
描き終わったら、下の「🚀 予測する」ボタンを押してください。
""")

# --- 分子エディタ（自作コンポーネント。ページ再読み込みなしでSMILESを直接取得） ---
current_structure = st_simple_editor(height=380)

st.write("")
predict_clicked = st.button("🚀 予測する", type="primary", use_container_width=True)

st.divider()

# --- 2. ドッキング結果の出力エリア ---
st.subheader("🔮 2. ドッキング結果（AIモデルによる予測）")

if predict_clicked:
    if not current_structure:
        st.warning("⚠️ まだ構造が描かれていません。エディタで分子を描いてから押してください。")
        st.session_state.pop("last_result", None)
    else:
        features = calc_feature_dict(current_structure)
        if features is None:
            st.session_state.pop("last_result", None)
            st.error("❌ この構造は正しい化学構造として認識できませんでした。原子の結合数などを見直してみてください。")
        else:
            with st.spinner("🧪 AIがドッキング計算を実行中..."):
                time.sleep(random.uniform(2.3, 3.7))  # 演出用のウェイト（毎回少しランダムに）
            score = predict_score(features)
            st.session_state["last_result"] = {
                "structure": current_structure,
                "features": features,
                "score": score,
            }

result = st.session_state.get("last_result")

if result is None:
    st.info("💡 上のエディタで分子を描いて「予測する」を押すと、ここに結果が表示されます。")
else:
    features = result["features"]
    score = result["score"]
    points = score_to_points(score)
    icon, label, box_type = score_comment(points)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="📊 判定結果", value=f"{points:.0f} / 100 点")
    with col2:
        st.caption("💻 解析されたSMILES")
        st.code(result["structure"], language="text")

    message = f"{icon} **{label}**（{points:.0f}点）"
    if box_type == "success":
        st.success(message)
    elif box_type == "warning":
        st.warning(message)
    else:
        st.error(message)

    st.caption(f"※ AIが予測した結合の強さをもとに、0〜100点に変換したスコアです（参考：ドッキングスコア {score:.2f} kcal/mol）。")

    # --- 3. 改善のヒント ---
    st.divider()
    st.subheader("💡 3. 得点アップのヒント")

    if points >= 90:
        st.success("すでにとても良い設計です！これ以上の改良も試してみましょう。")
    else:
        suggestions = get_suggestions(features, top_n=3)
        if not suggestions:
            st.info("すでに良いバランスの分子になっています。細部を色々変えて試してみましょう。")
        else:
            for i, s in enumerate(suggestions, start=1):
                st.markdown(f"{i}. {s['text']}")

    with st.expander("🔬 AIが見ている分子の特徴量（一部）"):
        preview_cols = ["MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors", "NumRotatableBonds"]
        row_df = pd.DataFrame([features], columns=FEATURE_NAMES)
        st.dataframe(row_df[preview_cols].T.rename(columns={0: "値"}))

st.sidebar.markdown("""
### 💡 使い方
1. ボタンで「原子の種類」または「結合の種類」を選ぶ
2. キャンバスをタップ、または押さえたままドラッグして構造を描く
3. 「🚀 予測する」ボタンを押す
4. 「得点アップのヒント」を参考に構造を改良する

### 🧬 このアプリについて
表示される点数は、RDKitで計算した201種類の分子記述子（分子量・LogP・極性表面積など）をもとに、
実際のドッキング計算結果から学習したLightGBMモデルが予測した**ドッキングスコア（kcal/mol）**を、
分かりやすい0〜100点に変換したものです（-14 kcal/mol以下→100点、4 kcal/mol以上→0点）。
点数が高いほど、標的タンパク質と強く結合すると予測されます。

改善のヒントは、実際によく効く医薬品分子の特徴と比較し、
AIモデルが特に重視している要素を優先的に提案しています。
""")
