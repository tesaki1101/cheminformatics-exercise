import streamlit as st
import py3Dmol
import streamlit.components.v1 as components

# ページ設定（モバイルファーストのため、初期はcenteredが扱いやすいです）
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」と、薬「イマチニブ」の3Dモデルです。スマホ画面でも指で回したり拡大できます。")

st.subheader("🔮 BCR-ABL ＆ イマチニブ 3D分子モデル")
st.caption("📱 画面内をスワイプ（ドラッグ）すると、好きな角度からポケットを覗き込めます")

# --- py3Dmolによる3Dモデル構築（完全指定＆モバイルサイズ版） ---
view = py3Dmol.view(query='pdb:1IEP', width=350, height=350) # スマホの横幅に合わせて350pxに最適化
view.setStyle({}, {})

# 【バグ対策】曖昧な'protein'セレクタを廃止し、「チェーンA」の主要原子を直接指定して確実に表示させる
view.setStyle({'chain': 'A', 'elem': ['C', 'N', 'O', 'S']}, {
    'sphere': {'colorscheme': 'pqp', 'radius': 1.6, 'opacity': 0.9}
})

# 薬（STI）のうち、チェーンAに結合しているものだけを表示（上から太めのスティックで重ねる）
view.setStyle({'chain': 'A', 'resn': 'STI'}, {
    'stick': {'colorscheme': 'greenCarbon', 'radius': 0.35}
})

# 不要な他のチェーンや水分子を完全に除外
view.setStyle({'chain': 'B'}, {})
view.setStyle({'resn': 'HOH'}, {})

# スローニン315 (Thr315) の演出（スライダー変数 size は下で定義しますが、Streamlitの仕様上問題ありません）
# セッション状態からサイズを取得するか、安全のために初期値ベースで判定（あるいは下のスライダーを先読み）
# ここでは直感的に動くよう、下で定義するスライダー変数を先に持ってきます
st.divider()

st.subheader("🛠️ 創薬パラメーターの調整")
st.markdown("高校化学の知識を使い、スライダーを動かして「薬とポケットの相性」を変化させてみましょう。")

# スマホで見やすいよう、選択肢やスライダーを縦に並べます
charge = st.radio(
    "【1】官能基の電気的性質（電荷）",
    options=["プラス（アミノ基を配置）", "中性（メチル基を配置）", "マイナス（カルボキシ基を配置）"],
    index=1
)

philic = st.slider(
    "【2】ベンゼン環の数（油へなじみやすさ）",
    min_value=1, max_value=3, value=2
)

size = st.slider(
    "【3】分子の長さ（リンカー長）",
    min_value=1, max_value=5, value=3
)

# スライダーの値に応じて3Dの Thr315 の色とラベルを変更
if size > 3:
    view.addStyle({'chain': 'A', 'resi': 315}, {'sphere': {'colorscheme': 'yellowCarbon', 'radius': 1.8}})
    view.addLabel("💥衝突注意: Thr315", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'red', 'backgroundOpacity': 0.9})
else:
    view.addStyle({'chain': 'A', 'resi': 315}, {'sphere': {'colorscheme': 'magentaCarbon', 'radius': 1.7}})
    view.addLabel("Thr315", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'darkgreen', 'backgroundOpacity': 0.8})

view.addLabel("開発中の薬", {'chain': 'A', 'resn': 'STI'}, {'backgroundColor': 'navy', 'backgroundOpacity': 0.8})
view.zoomTo({'chain': 'A', 'resn': 'STI'})

# --- 3Dモデルを上部に表示するためのHTML埋め込み（スマホ対応） ---
html_source = view._make_html()
# スライダーの下ではなく、タイトル直下に表示されるよう、上にコンポーネントを配置したいですが、
# Streamlitはコードの順序通りに描画するため、見やすさを考慮してここでレンダリングします。
# 順番を「3Dモデル -> スライダー -> 解説」のスマホ最適化配置にします。
st.components.v1.html(html_source, height=360, width=360)

st.info("💡 **データの見方:** 周りの「もこもこした球体の壁」がタンパク質のポケットです。ピンク〜紫の部分が『極性（電気的な性質がある場所）』、白色の部分が『疎水性（油っぽい場所）』です。")

st.divider()

# リアルタイムの化学変化解説
st.markdown("### 🔍 現在の結合シミュレーション解説")

score = 0

if "プラス" in charge:
    score += 40
    st.success("⭕ **電荷:** ポケット奥のマイナスアミノ酸と、薬のプラス（アミノ基）が磁石のように強烈に引き合っています！（静電相互作用）")
elif "マイナス" in charge:
    score += 0
    st.error("❌ **電荷:** マイナス同士が反発！磁石の同極のように薬が弾き飛ばされてしまいます。")
else:
    score += 15
    st.warning("🔺 **電荷:** 反発はしませんが、強い引き合いも生まれず、結合が弱いです。")
    
if philic == 3:
    score += 30
    st.success("⭕ **疎水性:** ベンゼン環の油っぽさがポケットの疎水性領域と完璧に密着し、安定しました。")
elif philic == 2:
    score += 25
    st.info("🔺 **疎水性:** イマチニブの標準骨格です。十分良好な結合です。")
else:
    score += 10
    st.error("❌ **疎水性:** 油っぽさが足りず、周りの水分子に邪魔されてポケットから滑り落ちてしまいます。")

if size == 3:
    score += 30
    st.success("⭕ **サイズ:** 完璧な長さです！入り口にある「スレオニン315（Thr315）」の壁をすり抜けて奥まで届いています。")
elif size > 3:
    score -= 15
    st.error("💥 **立体障害発生:** 分子が長すぎます！3Dモデルで黄色く光っている『Thr315』の壁に激突しています！")
else:
    score += 10
    st.warning("🔺 **サイズ:** 短すぎます！奥のポケットまで手が届いていません。")

score = max(0, min(100, score))
st.metric(label="📊 予測される結合スコア", value=f"{score} / 100 点")
