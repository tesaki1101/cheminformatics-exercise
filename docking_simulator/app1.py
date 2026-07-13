import streamlit as st

# ページ設定（iPhone最適化）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 薬の構造（官能基）をカスタマイズ")
st.markdown("上のタブとスライダーを動かすと、あなたが設計した薬の【構造】がリアルタイムに変化します。")

# --- 1. ユーザー操作エリア（入力） ---
tab1, tab2, tab3 = st.tabs(["🔴 プラス（アミノ基）", "⚪ 中性（メチル基）", "🔵 マイナス（カルボキシ基）"])

with tab1:
    st.markdown("**アミノ基（$-NH_2$）**：溶液中でプラスに帯電し、ポケットの奥と引き合います。")
    amino_count = st.slider("配置するアミノ基の数", min_value=1, max_value=5, value=1, key="amino")
    selected_charge = "プラス"
    functional_group_count = amino_count
    group_symbol = "[-NH2(+)]"

with tab2:
    st.markdown("**メチル基（$-CH_3$）**：電気的な偏りがない、中性・疎水性（油っぽい）のパーツです。")
    methyl_count = st.slider("配置するメチル基の数", min_value=1, max_value=5, value=1, key="methyl")
    selected_charge = "中性"
    functional_group_count = methyl_count
    group_symbol = "[-CH3]"

with tab3:
    st.markdown("**カルボキシ基（$-COOH$）**：溶液中でマイナスに帯電し、ポケット奥と反発します。")
    carboxy_count = st.slider("配置するカルボキシ基の数", min_value=1, max_value=5, value=1, key="carboxy")
    selected_charge = "マイナス"
    functional_group_count = carboxy_count
    group_symbol = "[-COOH(-)]"

# 【スライダー】疎水性とサイズ
philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 2. 視覚的なテキスト構造式の動的組み立て ---
# 高校生にも分かりやすいよう、直感的な記号で薬が伸び縮みする様子を表現します
attached_branch = "  │  \n".join([f"    {group_symbol}" for _ in range(functional_group_count)])
linker_line = "──" * size
benzene_rings = "＝[ベンゼン環]" * philic
imatinib_tail = "──[イマチニブ基本骨格]"

st.subheader("🧪 あなたがデザインした薬の構造イメージ")

# 見やすいように大きな太字枠で囲って表示
st.markdown(
    f"""
    <div style="background-color: #F8F9FA; border-radius: 10px; padding: 20px; font-family: monospace; font-size: 16px; border-left: 5px solid #27AE60; line-height: 1.8;">
    <strong>【薬の先端パーツ】</strong><br>
    {attached_branch}<br>
    &nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    <strong>【設計した本体】</strong><br>
    (先端){linker_line}{benzene_rings}{imatinib_tail}(末端)
    </div>
    """, 
    unsafe_allow_html=True
)

st.divider()

# --- 3. 固定の「タンパク質断面画像」の表示エリア ---
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
    if selected_charge == "プラス":
        if functional_group_count == 1:
            image_file = "perfect.png"
            status_text = "🎯 **ジャストフィット！** 長さも完璧で、先端のプラスがポケット奥のマイナスとカチッと綺麗に引き合いました！"
        else:
            image_file = "perfect.png"
            status_text = "🔺 **おしい！** 形は入りましたが、プラスのパーツが多すぎて分子がギチギチになり、結合が少し不安定です。"
    elif selected_charge == "マイナス":
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！** 薬の先端をマイナスにしたため、ポケット奥のマイナス電荷と磁石のように激しく反発して弾かれました。"
    else:
        image_file = "perfect.png"
        status_text = "🔺 **結合が弱い！** 収まってはいますが、電気的な引き合い（磁石のような力）がないため、すぐに外れてしまいます。"

try:
    st.image(image_file, caption="タンパク質のポケット断面と薬のハマり具合", width=350)
except:
    st.warning(f"【ポケット画像】現在 『{image_file}』 を読み込み中です。GitHubに画像を保存するとここに表示されます。")

st.info(status_text)
