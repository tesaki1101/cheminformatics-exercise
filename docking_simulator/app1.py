import streamlit as st
import py3Dmol
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(
    page_title="3D AI創薬シミュレータ：イマチニブの秘密",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 3D AI創薬シミュレータ：奇跡の薬『イマチニブ』を体感せよ！")
st.write("慢性骨髄性白血病の原因タンパク質「BCR-ABL」と、分子標的薬「イマチニブ」の3Dモデルです。マウスで回転や拡大ができます。")

# 画面を2カラムに分割
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🛠️ 創薬パラメーターの調整")
    st.markdown("高校化学の知識を使い、スライダーを動かして「薬とポケットの相性」を変化させてみましょう。")
    
    # 1. 電荷（アミノ基の修飾）
    charge = st.radio(
        "【1】官能基の電気的性質（電荷）",
        options=["プラス（アミノ基を配置）", "中性（メチル基を配置）", "マイナス（カルボキシ基を配置）"],
        index=1
    )
    
    # 2. 疎水性（ベンゼン環などの油っぽさ）
    philic = st.slider(
        "【2】ベンゼン環の数（油へなじみやすさ）",
        min_value=1, max_value=3, value=2,
        help="数を増やすほど疎水性が上がり、タンパク質の油っぽい隙間（ポケット）に馴染みます。"
    )
    
    # 3. サイズ（分子の長さ・立体障害）
    size = st.slider(
        "【3】分子の長さ（リンカー長）",
        min_value=1, max_value=5, value=3,
        help="長すぎるとアミノ酸の壁にぶつかり（立体障害）、短すぎると奥まで届きません。"
    )

    st.divider()
    
    # リアルタイムの化学変化解説
    st.markdown("### 🔍 現在の結合シミュレーション解説")
    
    score = 0
    
    if "プラス" in charge:
        score += 40
        st.success("⭕ **電荷:** ポケット奥のマイナスアミノ酸（Asp381等）と、薬のプラス（アミノ基）が磁石のように強烈に引き合っています！（静電相互作用）")
    elif "マイナス" in charge:
        score += 0
        st.error("❌ **電荷:** マイナス同士が反発！磁石の同極のように薬が弾き飛ばされてしまいます。")
    else:
        score += 15
        st.warning("🔺 **電荷:** 反発はしませんが、強い引き合いも生まれず、結合が弱いです。")
        
    if philic == 3:
        score += 30
        st.success("⭕ **疎水性:** ベンゼン環の油っぽさがポケットの疎水性領域（Leu, Ile）と完璧に密着し、水分子を追い出して安定しました。")
    elif philic == 2:
        score += 25
        st.info("🔺 **疎水性:** イマチニブの標準骨格です。十分良好な結合です。")
    else:
        score += 10
        st.error("❌ **疎水性:** 油っぽさが足りず、周りの水分子に邪魔されてポケットから滑り落ちてしまいます。")

    if size == 3:
        score += 30
        st.success("⭕ **サイズ:** 完璧な長さです！入り口にあるゲートキーパー「スレオニン315（Thr315）」の壁をすり抜けて奥まで届いています。")
    elif size > 3:
        score -= 15
        st.error("💥 **立体障害発生:** 分子が長すぎます！3Dモデルで黄色く光っている『Thr315』の壁に激突し、ポケットに入りません！")
    else:
        score += 10
        st.warning("🔺 **サイズ:** 短すぎます！奥のポケットまで手が届いていません。")

    score = max(0, min(100, score))
    st.metric(label="📊 予測される結合スコア", value=f"{score} / 100 点")

with col2:
    st.subheader("🔮 BCR-ABL ＆ イマチニブ 3D分子モデル")
    st.caption("💻 画面内をドラッグすると、好きな角度からポケットの奥を覗き込めます")
    
    # --- py3Dmolによる3Dモデル構築（Surface ＆ 単一チェーン化） ---
    view = py3Dmol.view(query='pdb:1IEP', width=600, height=500)
    
    # 1. 不要な他の対称分子などを非表示にし、「チェーンA」のタンパク質だけを表示
    # 極性（親水性・疎水性）が直感的にわかるカラー（コサダの親水性スケールなど）でサーフェス化
    view.addSurface(py3Dmol.VDW, {
        'opacity': 0.85, 
        'colorscheme': 'pqp', # Polar/Non-polarで色分け（極性=ピンク〜紫、非極性/疎水性=白〜カーボン色）
        'state': {'chain': 'A'}
    }, {'protein': True, 'chain': 'A'})
    
    # 2. 薬（イマチニブ：残基名 STI）を、サーフェスの上に重ねてくっきり表示
    # 元素色（炭素=緑、窒素=青、酸素=赤）の球棒（stick/sphere）モデルで目立たせる
    view.setStyle({'resn': 'STI'}, {
        'stick': {'colorscheme': 'greenCarbon', 'radius': 0.2},
        'sphere': {'scale': 0.3}
    })
    
    # 3. ゲートキーパー「スレオニン315 (Thr315)」のハイライト演出
    # スライダーでサイズが「長すぎ(>3)」になったら、警告としてThr315の場所を強調
    if size > 3:
        view.addStyle({'chain': 'A', 'resi': 315}, {'stick': {'colorscheme': 'yellowCarbon', 'radius': 0.4}})
        view.addLabel("💥衝突: Thr315の壁", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'red', 'backgroundOpacity': 0.9})
    else:
        view.addStyle({'chain': 'A', 'resi': 315}, {'stick': {'colorscheme': 'magentaCarbon', 'radius': 0.3}})
        view.addLabel("ゲートキーパー: Thr315", {'chain': 'A', 'resi': 315}, {'backgroundColor': 'darkgreen', 'backgroundOpacity': 0.8})
        
    view.addLabel("開発中の薬", {'resn': 'STI'}, {'backgroundColor': 'navy', 'backgroundOpacity': 0.8})
    
    # 薬が刺さっているポケット周辺にカメラをグッと近づける
    view.zoomTo({'resn': 'STI'})
    
    # HTMLソースコードに変換してStreamlitに出力
    html_source = view._make_html()
    components.html(html_source, height=500, width=600)
    
    st.info("💡 **データの見方:** 周りの「もこもこした壁」がタンパク質（チェーンA）のポケットです。色がついている部分が『極性（電気的な性質がある場所）』、白い部分が『疎水性（油っぽい場所）』です。薬が隙間にぴったり挟まっている様子をぐるぐる回して観察してください！")
