import streamlit as st
from rdkit import Chem
from rdkit.Chem import Draw

# ページ設定（iPhone最適化）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 薬の構造（官能基）をカスタマイズ")
st.markdown("上のタブとスライダーを動かすと、あなたが設計した薬の【化学構造式】がリアルタイムに変化します。")

# --- 1. ユーザー操作エリア（入力） ---
tab1, tab2, tab3 = st.tabs(["🔴 プラス（アミノ基）", "⚪ 中性（メチル基）", "🔵 マイナス（カルボキシ基）"])

with tab1:
    st.markdown("**アミノ基（$-NH_2$）**：溶液中でプラスに帯電し、ポケットの奥と引き合います。")
    amino_count = st.slider("配置するアミノ基の数", min_value=1, max_value=5, value=1, key="amino")
    group_smiles = "N"  # 窒素パーツ
    functional_group_count = amino_count

with tab2:
    st.markdown("**メチル基（$-CH_3$）**：電気的な偏りがない、中性・疎水性（油っぽい）のパーツです。")
    methyl_count = st.slider("配置するメチル基の数", min_value=1, max_value=5, value=1, key="methyl")
    group_smiles = "C"  # 炭素パーツ
    functional_group_count = methyl_count

with tab3:
    st.markdown("**カルボキシ基（$-COOH$）**：溶液中でマイナスに帯電し、ポケット奥と反発します。")
    carboxy_count = st.slider("配置するカルボキシ基の数", min_value=1, max_value=5, value=1, key="carboxy")
    group_smiles = "C(=O)O"  # 酸パーツ
    functional_group_count = carboxy_count

# 【スライダー】疎水性とサイズ
philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 2. バックエンドでの分子データ結合と2D画像生成 ---
# 選択された数だけパーツを結合する構造文字列（SMILES）を裏側で組み立て
attached_groups = "".join([f"({group_smiles})" for _ in range(functional_group_count)])
core_linker = "C" * size
rings = "c1ccccc1" * philic

# 骨格とパーツをドッキングして1つの分子データにする
full_smiles = f"{attached_groups}{core_linker}{rings}NC2=NC=CC(=N2)C3=CC=CC=C3"

st.subheader("🧪 あなたがデザインした薬の構造式")

try:
    # RDKitを使って、文字データから本物の化学構造式（2D）を動的生成
    mol = Chem.MolFromSmiles(full_smiles)
    
    if mol is not None:
        # 高校生が見やすいよう、線の太さや原子の文字サイズを大きめに綺麗にレンダリング
        drawer_options = Draw.MolDrawOptions()
        drawer_options.bondLineWidth = 3
        drawer_options.atomLabelFontSize = 14
        
        # 構造式を画像として書き出し、Streamlit上に表示（横幅をスマホ用に350pxに固定）
        img = Draw.MolToImage(mol, size=(350, 250), options=drawer_options)
        st.image(img, caption="現在設計中の化合物の化学構造（2D）")
    else:
        st.error("構造式の生成に失敗しました。パラメーターを調整してください。")
except Exception as e:
    st.caption("※構造式の自動描画ライブラリ（RDKit）を読み込み中です...")

st.divider()

# --- 3. 別途用意した固定の「タンパク質断面画像」の表示エリア ---
st.subheader("🔮 ポケット内部のシミュレーション（イメージ）")

image_file = "perfect.png"
status_text = ""

# 断面イラスト側の分岐判定
if size > 3:
    image_file = "too_long.png"
    status_text = "💥 **立体障害発生！** 分子が長すぎるため、ポケット入り口にある『Thr315』の壁に激突して奥に入れません。"
elif size < 3:
    image_file = "too_short.png"
    status_text = "🔺 **長さ不足！** 分子が短すぎて、ポケットの最奥部まで薬の手が届いていません。"
else:
    if "amino" in st.session_state and tab1: # プラス選択時
        if functional_group_count == 1:
            image_file = "perfect.png"
            status_text = "🎯 **ジャストフィット！** 長さも完璧で、先端のプラスがポケット奥のマイナスとカチッと綺麗に引き合いました！"
        else:
            image_file = "perfect.png"
            status_text = "🔺 **おしい！** 形は入りましたが、プラスのパーツが多すぎて分子がギチギチになり、結合が少し不安定です。"
    elif tab3: # マイナス選択時
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！** 薬の先端をマイナスにしたため、ポケット奥のマイナス電荷と磁石のように激しく反発して弾かれました。"
    else: # 中性選択時
        image_file = "perfect.png"
        status_text = "🔺 **結合が弱い！** 収まってはいますが、電気的な引き合い（磁石のような力）がないため、すぐに外れてしまいます。"

try:
    st.image(image_file, caption="タンパク質のポケット断面と薬のハマり具合", width=350)
except:
    st.warning(f"【ポケット画像】現在 『{image_file}』 を読み込み中です。GitHubに画像を保存するとここに表示されます。")

st.info(status_text)
