import streamlit as st

# ページ設定（iPhone最適化）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 1. 薬の構造（官能基）を化学式で入力してみよう")
st.markdown("ポケットの最奥部（Asp381）は**マイナスの電荷**を持っています。引き合うためには、薬の先端にどんな原子を配置すればよいでしょうか？")

# 高校生が自分で文字（化学式）を打ち込むボックス
chemical_input = st.text_input(
    "薬の先端の化学式を入力してください（例: NH2, CH3, COOH など）", 
    value="NH2",
    max_chars=10
).strip().upper()  # 小文字で打たれても大文字に統一

# 【スライダー】分子の長さ
st.subheader("🛠️ 2. 分子の長さを調整しよう")
size = st.slider("分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 判定ロジックと画像の切り替え ---
st.subheader("🔮 ポケット内部のシミュレーション結果")

image_file = "perfect.png"
status_text = ""

# 先に「長さ（サイズ）」の立体障害・届かないを判定
if size > 3:
    image_file = "too_long.png"
    status_text = "💥 **立体障害発生！** 分子が長すぎるため、ポケット入り口にある『Thr315』の壁に激突して奥に入れません。"
elif size < 3:
    image_file = "too_short.png"
    status_text = "🔺 **長さ不足！** 分子が短すぎて、ポケットの最奥部まで薬の手が届いていません。"
else:
    # 長さがピッタリ（size == 3）の場合に、入力された化学式で分岐
    if "N" in chemical_input:  # 窒素（N）が含まれる場合（NH2, NH, NCH3など）
        image_file = "perfect.png"
        status_text = "🎯 **大成功！ジャストフィット！**\n\n窒素（N）を含むアミノ基は、体内で**プラスの電荷**を帯びます。これがポケットの奥にあるマイナス電荷（Asp381）と磁石のように強く引き合い（静電相互作用）、強力に癌タンパク質の働きをブロックしました！"
    elif "O" in chemical_input:  # 酸素（O）が含まれる場合（COOH, OHなど）
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！**\n\n酸素（O）を多く含むカルボキシ基などは、体内で**マイナスの電荷**を帯びてしまいます。ポケットの奥のマイナス電荷と磁石の同極のように激しく反発し、薬が弾き飛ばされてしまいました。"
    else:  # それ以外（CH3など炭化水素やその他）
        image_file = "perfect.png"
        status_text = "🔺 **おしい！結合が弱いです**\n\n形はポケットに収まりましたが、電気的な引き合い（プラスとマイナスの結合）がありません。これでは薬がポケットに留まる力が弱く、すぐに外れてしまいます。先端に『あの原子』を足してみましょう。"

# 画面への画像表示
try:
    st.image(image_file, caption=f"現在の入力（{chemical_input} / 長さ:{size}）に基づくシミュレーション", width=350)
except:
    st.warning(f"【画像エラー】現在 『{image_file}』 を読み込み中です。GitHubに保存されているか確認してください。")

st.info(status_text)
