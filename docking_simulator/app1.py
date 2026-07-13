import streamlit as st
import py3Dmol
import streamlit.components.v1 as components
import requests

# ==============================================================
# ページ設定
# ==============================================================
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」と、薬「イマチニブ」の3Dモデルです。スマホ画面でも指で回したり拡大できます。")

st.subheader("🔮 BCR-ABL ＆ イマチニブ 3D分子モデル")
st.caption("📱 画面内をスワイプ（ドラッグ）して好きな角度からポケットを覗き込めます")

# ==============================================================
# ① タンパク質データの取得
#    実際の結晶構造（PDB ID: 1IEP = Abl キナーゼ + イマチニブ）を
#    RCSB PDBから取得します。原子数が十分にあるので、Surface（表面）が
#    正しく・きれいに描画されます。
#    ※ネットワークに接続できない場合は簡易フォールバック構造を使用します。
# ==============================================================
PDB_ID = "1IEP"

@st.cache_data(show_spinner=False)
def fetch_pdb_text(pdb_id: str) -> str:
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

# 万一オフラインの場合の最小構造（修正版：不正な "O-" 元素表記を修正済み）
FALLBACK_PDB = """\
ATOM    205  N   THR A 315      23.513  18.783  19.641  1.00 13.92           N
ATOM    206  CA  THR A 315      22.180  19.068  19.103  1.00 15.68           C
ATOM    207  C   THR A 315      21.365  17.786  18.995  1.00 16.09           C
ATOM    208  O   THR A 315      21.144  17.275  17.904  1.00 16.79           O
ATOM    209  CB  THR A 315      21.439  20.071  20.007  1.00 15.69           C
ATOM    210  OG1 THR A 315      22.257  21.229  20.140  1.00 16.92           O
ATOM    211  CG2 THR A 315      20.113  20.443  19.382  1.00 15.42           C
HETATM 2390  N1  STI A 900      19.680  17.730  20.301  1.00 12.04           N
HETATM 2391  C2  STI A 900      18.730  16.890  19.821  1.00 12.39           C
HETATM 2392  C3  STI A 900      18.590  16.740  18.441  1.00 13.19           C
HETATM 2393  C4  STI A 900      19.460  17.480  17.621  1.00 12.60           C
HETATM 2394  C5  STI A 900      20.440  18.320  18.171  1.00 12.08           C
HETATM 2395  C6  STI A 900      20.530  18.420  19.561  1.00 12.12           C
ATOM    685  N   ILE A 377      21.320  13.430  19.010  1.00 14.50           N
ATOM    686  CA  ILE A 377      20.140  12.620  18.670  1.00 13.20           C
ATOM    710  N   ASP A 381      25.650  14.890  22.550  1.00 16.50           N
ATOM    711  CA  ASP A 381      26.850  15.520  23.080  1.00 17.80           C
ATOM    712  CB  ASP A 381      27.950  14.500  23.350  1.00 19.20           C
ATOM    713  CG  ASP A 381      29.180  15.080  24.020  1.00 21.50           C
ATOM    714  OD1 ASP A 381      29.250  16.320  24.210  1.00 22.10           O
ATOM    715  OD2 ASP A 381      30.110  14.280  24.350  1.00 23.00           O
END
"""

try:
    pdb_text = fetch_pdb_text(PDB_ID)
    using_real_structure = True
except Exception:
    st.info("⚠️ 実際のPDB構造を取得できなかったため、簡易モデルで表示しています（機能・操作は同じです）。")
    pdb_text = FALLBACK_PDB
    using_real_structure = False

# ==============================================================
# ② 3Dビューアの構築
#
#   ★バグ修正ポイント★
#   1) 「Surfaceが表示されない」→ 原因は addSurface の対象選択に
#      {'protein': True} という（3Dmol.jsでは認識されない）指定を使っていたため、
#      対象原子が0件になり表面が生成されていませんでした。
#      → {'hetflag': False, 'water': False} という正式な選択方法に変更。
#
#   2) 「ピンクの邪魔な分子がある」→ 原因は colorscheme に存在しない
#      'pqp' という値を指定していたため、意図しない色（ピンク）で
#      描画されていました。
#      → アミノ酸の性質（疎水性・極性・電荷）に対応した「正しい」
#      カラーマップを自作して colorscheme に渡すよう修正。
#      これにより、高校化学の「官能基の性質」がそのまま色で
#      可視化されます。
# ==============================================================
view = py3Dmol.view(width=350, height=350)
view.addModel(pdb_text, "pdb")

# まず全原子を非表示にする（この上にSurfaceと薬だけを描画する）
view.setStyle({}, {})

# ★修正: 1IEPには2本のタンパク質鎖（A鎖・B鎖）が含まれ、それぞれに
#   薬（イマチニブ=STI）が1つずつ結合しています。そのままだと
#   「化合物が2つ」「表面がまばらで出ない」原因になるため、
#   A鎖（Chain A）だけに限定して描画します。
CHAIN = "A"

# タンパク質（A鎖のみ・HETATMと水を除く）のSurfaceを表示
# ※色指定は最も確実に描画される単色＋半透明にしています
view.addSurface(py3Dmol.VDW, {
    "opacity": 0.85,
    "color": "white"
}, {
    "chain": CHAIN,
    "hetflag": False,
    "water": False
})

# 薬（イマチニブ = STI、A鎖のもの1つだけ）はスティック表示で重ねる
view.setStyle({"chain": CHAIN, "resn": "STI"}, {
    "stick": {"colorscheme": "greenCarbon", "radius": 0.35}
})

st.divider()

# ==============================================================
# ③ 創薬パラメーターの調整（高校化学の官能基と連動）
# ==============================================================
st.subheader("🛠️ 創薬パラメーターの調整")
st.markdown("高校化学の知識を使い、官能基の種類と数を変えて「薬とポケットの相性」を変化させてみましょう。")

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

philic = st.slider("【2】ベンゼン環の数（油へなじみやすさ）", min_value=1, max_value=3, value=2)
size = st.slider("【3】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

# Thr315（ゲートキーパー残基）の見た目を、リンカー長に応じて動的に変更
# ※テキストラベルは表示せず、色の変化だけで衝突を表現する
if size > 3:
    view.addStyle({"resi": 315, "chain": CHAIN, "hetflag": False}, {
        "stick": {"color": "red", "radius": 0.5}
    })
else:
    view.addStyle({"resi": 315, "chain": CHAIN, "hetflag": False}, {
        "stick": {"color": "orange", "radius": 0.35}
    })

view.zoomTo({"chain": CHAIN, "resn": "STI"})

# ==============================================================
# ④ HTML埋め込み表示（スマホサイズ）
# ==============================================================
html_source = view._make_html()
components.html(html_source, height=380, width=360)

st.info(
    "💡 **見方**：半透明の白い壁＝タンパク質のポケット（鍵穴）の表面、緑のスティック＝薬（イマチニブ）です。\n\n"
    "オレンジ色の部分は「Thr315」という重要なアミノ酸（ゲートキーパー）。薬の分子が長すぎるとここに衝突し、赤色に変わります。"
)
if not using_real_structure:
    st.caption("（現在は簡易モデル表示中。ネットワーク接続が回復すると実際の結晶構造で表示されます）")

st.divider()

# ==============================================================
# ⑤ リアルタイムの化学変化解説 ＆ スコア計算
# ==============================================================
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
