import streamlit as st
import streamlit.components.v1 as components

# ページ設定（モバイル・PC双方に最適化）
st.set_page_config(
    page_title="3D AI創薬シミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 3D AI創薬シミュレータ")
st.write("白血病の原因タンパク質「BCR-ABL」のポケットにぴったりハマる薬を分子エディタで設計しましょう！")

st.subheader("🛠️ 1. 分子エディタ（JSME）で構造を描く")
st.markdown("""
右側のツール（炭素 C、窒素 N、酸素 O やベンゼン環など）を選んで、中央のキャンバスに構造を描いてください。
描き終わったら、エディタ内の **「SMILESを取得」** ボタン → **「コピー」** ボタンを押し、下の入力欄に貼り付けてください。
""")

# --- JSME埋め込み（表示専用。値はコピー＆ペーストでStreamlit側に渡す） ---
jsme_html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="text/javascript" src="https://jsme-editor.github.io/dist/jsme/jsme.nocache.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: transparent; font-family: sans-serif; }
        #jsme_container { width: 100%; height: 340px; }
        #controls { margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        #smiles_box {
            flex: 1;
            min-width: 150px;
            padding: 6px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
        }
        button {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            background-color: #ff4b4b;
            color: white;
            cursor: pointer;
        }
        button:hover { background-color: #e03e3e; }
        #copy_msg { color: green; font-size: 0.85em; }
    </style>
</head>
<body>
    <div id="jsme_container"></div>
    <div id="controls">
        <button onclick="extractSmiles()">SMILESを取得</button>
        <input id="smiles_box" type="text" readonly placeholder="ここにSMILESが表示されます">
        <button onclick="copySmiles()">コピー</button>
        <span id="copy_msg"></span>
    </div>

    <script>
        var jsmeApplet;

        // JSMEエディタが読み込まれたら自動実行
        function jsmeOnLoad() {
            jsmeApplet = new JSApplet.JSME("jsme_container", "100%", "340px", {
                "options" : "query,nocanonical,paste"
            });
        }

        function extractSmiles() {
            var smiles = jsmeApplet.smiles();
            document.getElementById("smiles_box").value = smiles;
            document.getElementById("copy_msg").innerText = "";
        }

        function copySmiles() {
            var box = document.getElementById("smiles_box");
            if (!box.value) {
                extractSmiles();
            }
            box.select();
            navigator.clipboard.writeText(box.value).then(function() {
                document.getElementById("copy_msg").innerText = "コピーしました！";
            });
        }
    </script>
</body>
</html>
"""

components.html(jsme_html_code, height=420, scrolling=False)

st.divider()

# --- 2. コピーしたSMILESを貼り付ける欄 ---
st.subheader("📋 2. SMILESを貼り付けて解析")
smiles_input = st.text_input(
    "コピーしたSMILES文字列をここに貼り付けてください",
    placeholder="例）c1ccccc1N"
)

run = st.button("🚀 ドッキング解析を実行", type="primary")

st.divider()

# --- 3. ドッキング結果の出力エリア ---
st.subheader("🔮 3. ドッキング結果")

if not run:
    st.info("💡 分子を描いてSMILESを取得・貼り付けたら、「ドッキング解析を実行」を押してください。")
elif not smiles_input.strip():
    st.warning("⚠️ SMILES文字列が入力されていません。エディタで構造を描いてから貼り付けてください。")
else:
    current_structure = smiles_input.strip()

    # 【実習用判定ロジック】文字列の長さ・原子の種類から特徴を抽出
    has_nitrogen = "N" in current_structure or "n" in current_structure
    has_oxygen = "O" in current_structure or "o" in current_structure
    mol_length = len(current_structure)

    image_file = "perfect.png"
    status_text = ""
    score = 50  # ベーススコア

    if mol_length > 45:  # 描きすぎて分子が長すぎる場合
        score = 35
        image_file = "too_long.png"
        status_text = (
            "💥 **ドッキング失敗（立体障害）**\n\n"
            "分子のサイズが大きすぎ（長すぎ）ます！ポケット入り口にある**『Thr315』の壁**に"
            "激突してしまい、奥の結合サイトへ侵入することができません。"
        )
    elif mol_length < 15:  # 短すぎる場合
        score = 40
        image_file = "too_short.png"
        status_text = (
            "🔺 **ドッキング不完全（長さ不足）**\n\n"
            "分子の長さが足りません。入り口のThr315はすり抜けましたが、"
            "ポケット最奥部にあるターゲット（Asp381）まで薬の手が届いていません。"
        )
    else:
        # 長さがちょうど良い場合、原子の種類（電荷）で選別
        if has_nitrogen and not has_oxygen:
            score = 98
            image_file = "perfect.png"
            status_text = (
                "🎯 **ドッキング大成功！ジャストフィット！**\n\n"
                "完璧な分子設計です！配置した**窒素（N）原子**が体内でプラスの電荷を帯び、"
                "ポケット最奥部にあるマイナス電荷（Asp381）と強力に引き合いました（静電相互作用）。"
            )
        elif has_oxygen:
            score = 15
            image_file = "repulsion.png"
            status_text = (
                "❌ **ドッキング失敗（電気的反発）**\n\n"
                "**酸素（O）原子**（カルボキシ基など）を配置したため、分子の先端がマイナスに"
                "帯電してしまいました。ポケット奥のマイナス電荷と磁石の同極のように激しく反発し、"
                "弾き飛ばされています。"
            )
        else:
            score = 60
            image_file = "perfect.png"
            status_text = (
                "🔺 **結合力不足（中性骨格）**\n\n"
                "形はポケットに収まっていますが、炭素（C）主体の構造であるため電気的な引き合いが"
                "発生しません。これでは結合が弱く、すぐにポケットから外れてしまいます。"
                "先端に「あの原子」を組み込んでみましょう。"
            )

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="📊 予測結合スコア", value=f"{score} / 100 点")
    with col2:
        st.caption("💻 入力されたSMILES")
        st.code(current_structure, language="text")

    st.markdown(status_text)

    # 断面図画像（同じフォルダに perfect.png / too_long.png / too_short.png / repulsion.png を配置）
    try:
        st.image(
            image_file,
            caption=f"設計された化合物（{current_structure[:20]}）のドッキングシミュレーション",
            width=350
        )
    except Exception:
        st.caption(f"（断面図画像「{image_file}」が見つかりません。app.pyと同じフォルダに配置してください）")

st.sidebar.markdown("""
### 💡 使い方
1. 上のエディタで分子を描く
2. 「SMILESを取得」→「コピー」
3. 下の入力欄にペースト
4. 「ドッキング解析を実行」を押す

※ このスコアは実習用の簡易判定であり、実際のAI創薬計算とは異なります。
""")
