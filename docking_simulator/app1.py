import streamlit as st
import streamlit.components.v1 as components
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

# ページ設定（iPhone最適化）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 薬の構造（官能基）をカスタマイズ")

# --- 1. ユーザー操作エリア（入力） ---
tab1, tab2, tab3 = st.tabs(["🔴 プラス（アミノ基）", "⚪ 中性（メチル基）", "🔵 マイナス（カルボキシ基）"])

with tab1:
    st.markdown("**アミノ基（$-NH_2$）**：溶液中でプラスに帯電し、ポケットの奥と引き合います。")
    amino_count = st.slider("配置するアミノ基の数", min_value=1, max_value=5, value=1, key="amino")
    selected_charge = "プラス"
    functional_group_count = amino_count
    group_smiles = "N"

with tab2:
    st.markdown("**メチル基（$-CH_3$）**：電気的な偏りがない、中性・疎水性のパーツです。")
    methyl_count = st.slider("配置するメチル基の数", min_value=1, max_value=5, value=1, key="methyl")
    selected_charge = "中性"
    functional_group_count = methyl_count
    group_smiles = "C"

with tab3:
    st.markdown("**カルボキシ基（$-COOH$）**：溶液中でマイナスに帯電し、ポケット奥と反発します。")
    carboxy_count = st.slider("配置するカルボキシ基の数", min_value=1, max_value=5, value=1, key="carboxy")
    selected_charge = "マイナス"
    functional_group_count = carboxy_count
    group_smiles = "C(=O)O"

# 【スライダー】疎水性とサイズ
philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 2. バックエンドでの分子データ結合とSVG自動生成（バグ完全回避） ---
attached_groups = "".join([f"({group_smiles})" for _ in range(functional_group_count)])
core_linker = "C" * size
rings = "c1ccccc1" * philic
full_smiles = f"{attached_groups}{core_linker}{rings}NC2=NC=CC(=N2)C3=CC=CC=C3"

st.subheader("🧪 あなたがデザインした薬の構造式")

try:
    mol = Chem.MolFromSmiles(full_smiles)
    if mol is not None:
        # 【最重要】Cairo等の外部依存のない、純粋なSVGベクター画像としてテキスト出力する
        drawer = rdMolDraw2D.MolDraw2DSVG(350, 250)
        options = drawer.drawOptions()
        options.bondLineWidth = 3
        options.atomLabelFontSize = 14
        
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        svg_text = drawer.GetDrawingText()
        
        # HTMLとして画面に直接埋め込む（iPhoneサイズで確実に表示）
        components.html(svg_text, height=260, width=360)
    else:
        st.error("構造式の生成に失敗しました。パラメーターを調整してください。")
except Exception as e:
    st.error("構造式の描画プロセスでエラーが発生しました。")

st.divider()

# --- 3. 固定の「タンパク質断面画像」の表示エリア ---
st.subheader("🔮 ポケット内部のシミュレーション（イメージ）")

image_file = "perfect.png"
status_text = ""

if size > 3:
    image_file = "too_long.png"
    status_text = "💥 **立体障害発生！** 分子が長すぎるため、ポケット入り口にある『Thr315』の壁に激突して奥に入れません。"
elif size < 3:
    image_file = "too_short.png"
    status_text = "🔺 **長さ不足！** 分子が短すぎて、ポケットの最奥部まで薬の手が届いていません。"
else:
    if selected_charge == "プラス":
        if functional_group_count == 1:
            image_file = "perfect.png"
            status_text = "🎯 **ジャストフィット！** 長さも完璧で、先端のプラスがポケット奥のマイナスとカチッと綺麗に引き合いました！"
        else:
            image_file = "perfect.png"
            status_text = "🔺 **おしい！** 形は入りましたが、プラスのパーツが多すぎて分子がギチギチになり、結合が少し不安定です。"
    elif selected_charge == "マイナス":
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！** 薬の先端をマイナスにしたため、ポケット奥 of マイナス電荷と磁石のように激しく反発して弾かれました。"
    else:
        image_file = "perfect.png"
        status_text = "🔺 **結合が弱い！** 収まってはいますが、電気的な引き合いがないため、すぐに外れてしまいます。"

try:
    st.image(image_file, caption="タンパク質のポケット断面と薬のハマり具合", width=350)
except:
    st.warning(f"【ポケット画像】現在 『{image_file}』 を読み込み中です。GitHubに画像を保存するとここに表示されます。")

st.info(status_text)
