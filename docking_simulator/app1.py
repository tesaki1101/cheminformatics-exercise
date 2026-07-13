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

# イマチニブ周辺のポケットを構成するアミノ酸と薬のPDBテキストデータ
# 外部通信を発生させず、このテキストから直接3Dを生成します
PDB_DATA = """
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
HETATM 2396  C7  STI A 900      21.570  19.330  20.211  1.00 12.78           C  
HETATM 2397  N8  STI A 900      21.550  19.450  21.551  1.00 12.05           N  
HETATM 2398  C9  STI A 900      22.590  20.190  22.281  1.00 12.42           C  
HETATM 2399  N10 STI A 900      23.710  20.570  21.651  1.00 12.01           N  
HETATM 2400  C11 STI A 900      23.770  20.480  20.291  1.00 13.37           C  
HETATM 2401  C12 STI A 900      24.960  20.940  19.531  1.00 14.77           C  
HETATM 2402  C13 STI A 900      25.100  20.840  18.141  1.00 15.65           C  
HETATM 2403  C14 STI A 900      26.230  21.280  17.441  1.00 18.06           C  
HETATM 2404  C15 STI A 900      27.270  21.840  18.181  1.00 18.23           C  
HETATM 2405  C16 STI A 900      27.090  21.950  19.571  1.00 17.63           C  
HETATM 2406  C17 STI A 900      25.950  21.510  20.241  1.00 15.82           C  
HETATM 2407  N18 STI A 900      26.470  21.210  16.061  1.00 19.35           N  
HETATM 2408  C19 STI A 900      25.930  20.230  15.191  1.00 21.05           C  
HETATM 2409  O20 STI A 900      24.940  19.560  15.481  1.00 20.37           O  
HETATM 2410  C21 STI A 900      26.690  20.060  13.881  1.00 22.18           C  
HETATM 2411  C22 STI A 900      26.060  19.260  12.921  1.00 24.12           C  
HETATM 2412  C23 STI A 900      26.810  19.060  11.771  1.00 25.12           C  
HETATM 2413  C24 STI A 900      28.160  19.620  11.531  1.00 24.32           C  
HETATM 2414  C25 STI A 900      28.710  20.420  12.521  1.00 22.84           C  
HETATM 2415  C26 STI A 900      27.990  20.650  13.681  1.00 22.15           C  
HETATM 2416  C27 STI A 900      28.990  19.380  10.291  1.00 24.59           C  
HETATM 2417  N28 STI A 900      29.800  20.550   9.901  1.00 24.11           N  
HETATM 2418  C29 STI A 900      31.130  20.210   9.411  1.00 24.03           C  
HETATM 2419  C30 STI A 900      31.780  21.430   8.771  1.00 24.47           C  
HETATM 2420  N31 STI A 900      31.060  21.840   7.561  1.00 24.57           N  
HETATM 2421  C32 STI A 900      29.760  22.210   8.061  1.00 24.23           C  
HETATM 2422  C33 STI A 900      29.080  20.990   8.671  1.00 24.01           C  
HETATM 2423  C34 STI A 900      31.750  23.010   6.891  1.00 24.87           C  
ATOM    685  N   ILE A 377      21.320  13.430  19.010  1.00 14.50           N  
ATOM    686  CA  ILE A 377      20.140  12.620  18.670  1.00 13.20           C  
ATOM    687  CB  ILE A 377      20.310  11.120  19.050  1.00 13.50           C  
ATOM    688  CG1 ILE A 377      21.550  10.530  18.370  1.00 14.10           C  
ATOM    689  CG2 ILE A 377      19.080  10.270  18.620  1.00 12.80           C  
ATOM    690  CD1 ILE A 377      21.900   9.120  18.840  1.00 15.20           C  
ATOM    691  C   ILE A 377      19.820  12.750  17.180  1.00 12.90           C  
ATOM    692  O   ILE A 377      20.620  12.350  16.320  1.00 13.10           O  
ATOM    710  N   ASP A 381      25.650  14.890  22.550  1.00 16.50           N  
ATOM    711  CA  ASP A 381      26.850  15.520  23.080  1.00 17.80           C  
ATOM    712  CB  ASP A 381      27.950  14.500  23.350  1.00 19.20           C  
ATOM    713  CG  ASP A 381      29.180  15.080  24.020  1.00 21.50           C  
ATOM    714  OD1 ASP A 381      29.250  16.320  24.210  1.00 22.10           O  
ATOM    715  OD2 ASP A 381      30.110  14.280  24.350  1.00 23.00           O- 
"""

# 3Dビューアの構築
view = py3Dmol.view(width=350, height=350)
view.addModel(PDB_DATA, "pdb")
view.setStyle({}, {})

# 【解決策】確実に滑らかなSurfaceを生成する設定
view.addSurface("MS", {
    'opacity': 0.85,
    'colorscheme': 'pqp' # 極性＝ピンク、疎水性＝白
}, {'protein': True})

# 薬（STI）のみをスティック表示で重ねる
view.setStyle({'resn': 'STI'}, {
    'stick': {'colorscheme': 'greenCarbon', 'radius': 0.35}
})

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

# 3DのThr315の演出と衝突判定
if size > 3:
    view.addStyle({'resi': 315}, {'stick': {'colorscheme': 'yellowCarbon', 'radius': 0.5}})
    view.addLabel("💥衝突注意: Thr315", {'resi': 315}, {'backgroundColor': 'red', 'backgroundOpacity': 0.9})
else:
    view.addStyle({'resi': 315}, {'stick': {'colorscheme': 'magentaCarbon', 'radius': 0.35}})
    view.addLabel("Thr315", {'resi': 315}, {'backgroundColor': 'darkgreen', 'backgroundOpacity': 0.8})

view.addLabel("開発中の薬", {'resn': 'STI'}, {'backgroundColor': 'navy', 'backgroundOpacity': 0.8})
view.zoomTo({'resn': 'STI'})

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
