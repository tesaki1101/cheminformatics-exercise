import streamlit as st

# ページ設定（iPhone最適化）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 創薬パラメーターの調整")
st.markdown("官能基の種類と数を変えると、下に表示される【化合物の構造情報】がリアルタイムに変化します。")

# --- 1. ユーザー操作エリア（入力） ---
# 官能基の電気的性質をタブで切り替え
tab1, tab2, tab3 = st.tabs(["🔴 プラス（アミノ基）", "⚪ 中性（メチル基）", "🔵 マイナス（カルボキシ基）"])

with tab1:
    st.markdown("**アミノ基（$-NH_2$）**：溶液中でプラスに帯電しやすい官能基です。")
    amino_count = st.slider("配置するアミノ基の数", min_value=1, max_value=5, value=1, key="amino")
    selected_charge = "プラス"
    functional_group_count = amino_count
    group_smiles = "N"  # 窒素
    group_name = "アミノ基 (-NH2)"

with tab2:
    st.markdown("**メチル基（$-CH_3$）**：電気的な偏りがない、中性・疎水性の官能基です。")
    methyl_count = st.slider("配置するメチル基の数", min_value=1, max_value=5, value=1, key="methyl")
    selected_charge = "中性"
    functional_group_count = methyl_count
    group_smiles = "C"  # 炭素
    group_name = "メチル基 (-CH3)"

with tab3:
    st.markdown("**カルボキシ基（$-COOH$）**：溶液中でマイナスに帯電しやすい官能基です。")
    carboxy_count = st.slider("配置するカルボキシ基の数", min_value=1, max_value=5, value=1, key="carboxy")
    selected_charge = "マイナス"
    functional_group_count = carboxy_count
    group_smiles = "C(=O)O"  # カルボキシル
    group_name = "カルボキシ基 (-COOH)"

# 2. 疎水性とサイズのスライダー
philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 2. 化合物のデータ構造計算（バックエンド処理） ---
# 標準のイマチニブ骨格をベースに、ユーザーの選択をSMILES（分子の文字列表記）に反映させる擬似ロジック
# ベンゼン環（c1ccccc1）の数や、リンカー（CC）の長さを動的に結合
core_linker = "C" * size
rings = "c1ccccc1" * philic
attached_groups = f"({group_smiles})" * functional_group_count

# 動的に生成されたSMILES文字列
generated_smiles = f"{attached_groups}{core_linker}{rings}NC2=NC=CC(=N2)C3=CC=CC=C3"

# 分子内の原子数の簡易計算（デモ用）
carbon_base = 15 + (philic * 6) + (size) + (functional_group_count if selected_charge != "プラス" else 0)
nitrogen_base = 5 + (functional_group_count if selected_charge == "プラス" else 0)
oxygen_base = (functional_group_count * 2) if selected_charge == "マイナス" else 0
total_atoms = carbon_base + nitrogen_base + oxygen_base + 30 # 水素等含む概算

# --- 3. 画面への反映・出力エリア（フロントエンド） ---
st.subheader("📋 設計された化合物の構造情報")

# 計算された構造データをプログラミング風のコンポーネントで表示
col1, col2 = st.columns(2)
with col1:
    st.metric(label="⚛️ 総原子数（推定）", value=f"{total_atoms} 個")
    st.text(f"炭素 (C): {carbon_base}個\n窒素 (N): {nitrogen_base}個\n酸素 (O): {oxygen_base}個")

with col2:
    st.metric(label="🧪 付加された官能基", value=f"{functional_group_count} 個")
    st.text(f"種類: {group_name}")

# AI創薬やケモインフォマティクスで最も重要な「SMILES表記」をリアルタイム表示
st.markdown("**🧬 コンピュータが認識している分子構造データ (SMILES)**")
st.code(generated_smiles, language="text")

st.divider()

# --- 4. 固定の断面図画像の表示エリア ---
st.subheader("🔮 ポケット内部のシミュレーション（イメージ）")

# ここで別途ご用意される固定の断面図画像を条件分岐で表示します
image_file = "perfect.png"
status_text = ""

if size > 3:
    image_file = "too_long.png"
    status_text = "💥 **立体障害発生！** 分子が長すぎるため、ポケット入り口にある『Thr315』の壁に激突しています。"
elif size < 3:
    image_file = "too_short.png"
    status_text = "🔺 **長さ不足！** ポケットの最奥部まで薬が届いていません。"
else:
    if selected_charge == "プラス" and functional_group_count == 1:
        image_file = "perfect.png"
        status_text = "🎯 **ジャストフィット！** 奥のマイナス電荷とプラスのアミノ基が完璧に引き合いました！"
    elif selected_charge == "マイナス":
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！** 薬の先端のマイナスと、ポケット奥のマイナスが反発しています。"
    else:
        image_file = "perfect.png"
        status_text = "🔺 **結合が弱い！** 形は収まりましたが、電気的な引き合いが足りません。"

try:
    st.image(image_file, caption="現在の設計データに基づくポケット内の様子", width=350)
except:
    st.warning(f"【画像エリア】現在、条件に対応する固定画像 『{image_file}』 を読み込み中です。GitHubに保存するとここに表示されます。")

st.info(status_text)
