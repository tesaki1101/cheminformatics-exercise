import streamlit as st
import streamlit.components.v1 as components
import json

# ページ設定（モバイル・PC双方に最適化）
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」のポケットにぴったりハマる薬を分子エディタで設計しましょう！")

st.subheader("🛠️ 1. 分子エディタ（JSME）で構造を描く")
st.markdown("右側のツール（炭素 C、窒素 N、酸素 O やベンゼン環など）を選んで、中央のキャンバスに結合を引っ張って描いてみてください。")

# --- 【最重要】JSME埋め込み ＆ Streamlitへの双方向通信HTML ---
# JavaScriptの通信バグ・セキュリティブロックを完全に回避する仕組みです
jsme_html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="text/javascript" src="https://jsme-editor.github.io/dist/jsme/jsme.nocache.js"></script>
    <script>
        var jsmeApplet;

        // JSMEエディタが読み込まれたら自動実行
        function jsmeOnLoad() {
            // 画面サイズに合わせてエディタを生成
            jsmeApplet = new JSME.jsmeApplet("jsme_container", "100%", "340px", {
                "options" : "query,nocanonical,paste"
            });

            // 構造変更（お絵かき）イベントを感知してリアルタイムにデータを親(Streamlit)に送信
            jsmeApplet.setCallBack("AfterStructureModified", function(event) {
                var smiles = event.src.smiles();
                sendToStreamlit(smiles);
            });
        }

        // Streamlit側にデータを安全に引き渡す関数
        function sendToStreamlit(smilesData) {
            // StreamlitのコンポーネントAPIを介してテキストデータを送出
            const targetWindow = window.parent;
            targetWindow.postMessage({
                isstreamlit: true,
                type: "streamlit:setComponentValue",
                value: smilesData
            }, "*");
        }
    </script>
    <style>
        body { margin: 0; padding: 0; background-color: transparent; }
        #jsme_container { width: 100%; height: 340px; }
    </style>
</head>
<body>
    <div id="jsme_container"></div>
</body>
</html>
"""

# HTMLコンポーネントを実行し、戻り値としてユーザーが描いた「SMILESデータ」を直接取得
# 描画が変わるたびに、この `captured_smiles` の値がリアルタイムに自動更新されます
captured_smiles = components.html(jsme_html_code, height=350, scrolling=False)

# ページ読み込み直後など、まだ何も描かれていない場合のデフォルト設定
if not captured_smiles:
    current_structure = "未描画（キャンバスが空です）"
    has_nitrogen = False
    has_oxygen = False
    mol_length = 0
else:
    current_structure = str(captured_smiles)
    # 描かれた分子の「構造情報（テキスト）」から特徴を自動解析
    has_nitrogen = "N" in current_structure or "n" in current_structure
    has_oxygen = "O" in current_structure or "o" in current_structure
    # 文字の長さから擬似的に分子の長さを推定（実習用のロジック）
    mol_length = len(current_structure)

st.divider()

# --- 2. ドッキング結果を出力するエリア ---
st.subheader("🔮 2. ドッキング結果の出力")

# 初期状態（何も描かれていないとき）
if not captured_smiles or current_structure == "C":
    st.info("💡 画面上のエディタに原子や結合を描くと、ここにドッキングの解析結果がリアルタイムに出力されます。まずはベンゼン環などを置いてみましょう！")
else:
    # 描かれた構造テキストに基づいて、表示する断面図（ドッキング成否）を完全判定
    image_file = "perfect.png"
    status_text = ""
    score = 50 # ベーススコア

    # 【実習用判定ロジック】長さ・電気的性質をエディタのデータから自動抽出
    if mol_length > 45: # 描きすぎて分子が長すぎる場合
        score = 35
        image_file = "too_long.png"
        status_text = "💥 **ドッキング失敗（立体障害）**\n\nエディタで描いた分子のサイズが大きすぎ（長すぎ）ます！ポケット入り口にある**『Thr315』の壁**に激突してしまい、奥の結合サイトへ侵入することができません。"
    elif mol_length < 15: # 短すぎる場合
        score = 40
        image_file = "too_short.png"
        status_text = "🔺 **ドッキング不完全（長さ不足）**\n\n分子の長さが足りません。入り口のThr315はすり抜けましたが、ポケット最奥部にあるターゲット（Asp381）まで薬の手が届いていません。"
    else:
        # 長さがちょうど良い場合、原子の種類（電荷）で選別
        if has_nitrogen and not has_oxygen:
            score = 98
            image_file = "perfect.png"
            status_text = "🎯 **ドッキング大成功！ジャストフィット！**\n\n完璧な分子設計です！エディタで配置した**窒素（N）原子**が、体内でプラスの電荷を帯び、ポケット最奥部にあるマイナス電荷（Asp381）と強力に引き合いました（静電相互作用）。"
        elif has_oxygen:
            score = 15
            image_file = "repulsion.png"
            status_text = "❌ **ドッキング失敗（電気的反発）**\n\nエディタで**酸素（O）原子**（カルボキシ基など）を配置したため、分子の先端がマイナスに帯電してしまいました。ポケット奥のマイナス電荷と磁石の同極のように激しく反発し、弾き飛ばされています。"
        else:
            score = 60
            image_file = "perfect.png"
            status_text = "🔺 **結合力不足（中性骨格）**\n\n形はポケットに収まっていますが、炭素（C）主体の構造であるため電気的な引き合いが発生しません。これでは結合が弱く、すぐにポケットから外れてしまいます。先端に「あの原子」を組み込んでみましょう。"

    # 解析データのステータス表示
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric(label="📊 予測結合スコア", value=f"{score} / 100 点")
    with col2:
        st.caption("💻 コンピュータが認識した構造データ (SMILES)")
        st.code(current_structure, language="text")

    # ご用意いただいた完璧な断面図画像を表示
    try:
        st.image(image_file, caption=f"設計された化合物（{current_structure[:20]}...）のドッキングシミュレーション", width=350)
    except:
        st.warning
