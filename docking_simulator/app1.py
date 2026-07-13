import streamlit as st
import py3Dmol
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」と、薬「イマチニブ」の3Dモデルです。スマホ画面でも指で回したり拡大できます。")

st.subheader("🔮 BCR-ABL ＆ イマチニブ 3D分子モデル")
st.caption("📱 画面内をスワイプ（ドラッグ）して好きな角度からポケットを覗き込めます")

# --- py3Dmolによる3Dモデル構築（Surface＆ゴミ分子除去 確定版） ---
view = py3Dmol.view(query='pdb:1IEP', width=350, height=350)

# 【ここが最重要修正！】
# 1. まず、データ内の全ての表示スタイルを一旦デフォルト（ワイヤーフレーム等）も含めて完全に消去します
view.setStyle({}, {})

# 2. 「チェーンAのタンパク質（アミノ酸）」だけを指定して、確実にSurfaceを描画させます
# 'VDW'ではなく、よりエラーに強く安定した 'MS'（Molecular Surface）で文字列指定します
view.addSurface("MS", {
    'opacity': 0.9,
    'colorscheme': 'pqp'  # 極性＝ピンク〜紫、疎水性＝白
}, {'chain': 'A', 'protein': True})

# 3. 薬（STI）をチェーンAのもの「だけ」指定して、太めのスティックモデルでくっきり重ねて表示
view.setStyle({'chain': 'A', 'resn': 'STI'}, {
    'stick': {'colorscheme': 'greenCarbon', 'radius': 0.35}
})

# 4. 【不要分子の完全除去】
# チェーンB、水分子（HOH）、そしてピンクの謎のゴミ分子（グリセロール等＝残基名 GOL）を完全に非表示スタイルにします
view.setStyle({'chain': 'B'}, {})
view.setStyle({'resn': 'HOH'}, {})
view.setStyle({'resn': 'GOL'}, {})

st.divider()

st.subheader("🛠️ 創薬パラメーターの調整")
st.markdown("高校化学の知識を使い、官能基の種類と数を変えて「薬とポケットの相性」を変化させてみましょう。")

# 官能基の電気的性質をタブで切り替え
tab1, tab2, tab3 = st.tabs(["🔴 プラス（アミノ基）", "⚪ 中性（メチル基）", "🔵 マイナス（カルボキシ基）"])

with tab1:
    st.markdown("**アミノ基（$-NH_2$）**：溶液中でH+を受け取り、**プラス**に帯電しやすい官能基です。")
    amino_count = st.slider("配置するアミノ基の数", min_value=1, max_value=5, value=1, key="amino")
    selected_charge = "プラス"
    functional_group_count = amino_count

with tab2:
    st.markdown("**メチル基（$-CH_3$）**：電気的な偏りがほとんどない、**中性・疎水性（油っぽい）**の官能基です。")
    methyl_count = st.slider("配置するメチル基の数", min_value=1, max_value=5, value=1, key="methyl")
    selected_charge = "中性"
    functional_group_count = methyl_count

with tab3:
    st.markdown("**カルボキシ基（$-COOH$）**：溶液中でH+を放出し、**マイナス**に帯電しやすい官能基です。")
    carboxy_count = st.slider("配置するカルボキシ基の数", min_value=1, max_value=5, value=1, key="carboxy")
    selected_charge = "マイナス"
    functional_group_count = carboxy_count

# 疎水性とサイズ
philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

# 3DのThr315の演出
if size > 3:
    view.addStyle({'chain': 'A', 'resi': 315}, {'stick': {'colorscheme': 'yellowCarbon', 'radius': 0.5}})
    view.addLabel("💥衝突注意: Thr315", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'red', 'backgroundOpacity': 0.9})
else:
    view.addStyle({'chain': 'A', 'resi': 315}, {'stick': {'colorscheme': 'magentaCarbon', 'radius': 0.35}})
    view.addLabel("Thr315", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'darkgreen', 'backgroundOpacity': 0.8})

view.addLabel("開発中の薬", {'chain': 'A', 'resn': 'STI'}, {'backgroundColor': 'navy', 'backgroundOpacity': 0.8})
view.zoomTo({'chain': 'A', 'resn': 'STI'})

# HTML埋め込み表示（スマホサイズ）
html_source = view._make_html()
components.html(html_source, height=360, width=360)

st.info("💡 **データの見方**：もこもこした壁がタンパク質のポケットです。ピンク〜紫の部分が『極性（電気的な性質がある場所）』、白色の部分が『疎水性（油っぽい場所）』です。")

st.divider()

# --- リアルタイムの化学変化解説 ＆ スコア計算 ---
st.markdown("### 🔍 現在の結合シミュレーション解説")

score = 0

if selected_charge == "プラス":
    if functional_group_count == 1:
        score += 40
        st.success("⭕ **電荷:** 素晴らしい！アミノ基が1つ配置され、ポケット奥のマイナスアミノ酸と磁石のように完璧に引き合いました！（静電相互作用）")
    else:
        score += 25
        st.warning(f"🔺 **電荷:** プラスのアミノ基が{functional_group_count}個は多すぎます。引き合いは生じますが、分子が大きくなりすぎてポケットの形を歪めてしまいます。")
elif selected_charge == "マイナス":
    score += 0
    st.error(f"❌ **電荷:** マイナスのカルボキシ基が{functional_group_count}個配置されました。ポケット奥のマイナス電荷と強烈に反発し、薬が弾き飛ばされます！")
else:
    score += 15
    st.warning(f"🔺 **電荷:** 中性のメチル基が{functional_group_count}個配置されました。電気的な反発は起きませんが、引き合う力も生まれません。")
    
if philic == 3:
    score += 30
    st.success("⭕ **疎水性:** ベンゼン環が3つになり、ポケットの油っぽい領域と完璧に密着しました。")
elif philic == 2:
    score += 25
    st.info("🔺 **疎水性:** イマチニブの標準骨格です。十分良好な結合です。")
else:
    score += 10
    st.error("❌ **疎水性:** ベンゼン環が1つでは油っぽさが足りず、周りの水分子に邪魔されて滑り落ちてしまいます。")

if size == 3:
    score += 30
    st.success("⭕ **サイズ:** 完璧な長さです！「Thr315」の壁をすり抜けて奥まで届いています。")
elif size > 3:
    score -= 15
    st.error("💥 **立体障害発生:** 分子が長すぎます！3Dモデルの『Thr315』の壁に激突しています！")
else:
    score += 10
    st.warning("🔺 **サイズ:** 短すぎます！奥のポケットまで手が届いていません。")

score = max(0, min(100, score))
st.metric(label="📊 予測される結合スコア", value=f"{score} / 100 点")
