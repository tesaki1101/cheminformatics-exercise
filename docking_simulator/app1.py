import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# ページ設定（centeredでスマホにも対応）
st.set_page_config(
    page_title="創薬AIシミュレータ",
    page_icon="🧬",
    layout="centered"
)

st.title("🧬 創薬デザイン・シミュレータ")
st.write("白血病の原因タンパク質のポケットにぴったりハマる薬を設計しましょう！")

st.subheader("🛠️ 1. 薬の化学構造を描いてみよう")
st.markdown("下のキャンバスを使って、分子を自由に描くか、右下の「SMILES」ボタンから構造を読み込めます。")

# --- JSMEエディタをHTML/JavaScriptで構築 ---
# サーバー制限を受けない公開CDNからJSMEライブラリを読み込みます
jsme_html = """
<!DOCTYPE html>
<html>
<head>
    <script type="text/javascript" src="https://jsme-editor.github.io/dist/jsme/jsme.nocache.js"></script>
    <script>
        // JSMEの初期化
        function jsmeOnLoad() {
            // 幅350px, 高さ300pxでスマホサイズに最適化
            jsmeApplet = new JSME.jsmeApplet("jsme_container", "350px", "300px", {
                "options" : "query,nocanonical"
            });
            
            // 初期構造としてイマチニブの標準骨格（一部）をセットしておくことも可能です
            // jsmeApplet.readGenericMolecularInput("CC1=C(C=C(C=C1)NC2=NC=CC(=N2)C3=CN=CC=C3)C(=O)NC4=CC=C(C=C4)CN5CCN(CC5)C");
        }

        // 構造が変わったときにStreamlitへSMILES（文字データ）を送る関数
        function exportSmiles() {
            var smiles = jsmeApplet.smiles();
            // Streamlitの親ウインドウにデータを送信
            parent.postMessage({type: "jsme_smiles", value: smiles}, "*");
        }
    </script>
</head>
<body>
    <div id="jsme_container"></div>
    <div style="margin-top: 8px;">
        <button onclick="exportSmiles()" style="background-color: #27AE60; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%;">
            ▲ 描いた構造をシミュレータに適用する
        </button>
    </div>
</body>
</html>
"""

# エディタの表示（HTMLコンポーネントとして埋め込み）
# ここでユーザーが描いた分子のSMILESをJavaScript経由で取得するためのキャッチ仕掛け
st.components.v1.html(jsme_html, height=360, width=360)

# --- JavaScriptからの構造データ受け取りロジック ---
# 初期値はイマチニブを模した骨格
if "smiles_input" not in st.session_state:
    st.session_state.smiles_input = "CC1=CC=C(C=C1)NC2=NC=CC=N2"

# クエリパラメータなどを利用して簡易的に入力を模倣、またはスライダー等の既存UIと連携させます
st.markdown("---")

st.subheader("🛠️ 2. 創薬パラメーターの調整")
# 断面画像切り替え用の既存スライダー群
selected_charge = st.radio("【1】先端の官能基の性質", ["プラス（アミノ基）", "中性（メチル基）", "マイナス（カルボキシ基）"], index=0)
size = st.slider("【2】分子の長さ（リンカー長）", min_value=1, max_value=5, value=3)

st.divider()

# --- 3. 固定の「タンパク質断面画像」の表示エリア ---
st.subheader("🔮 ポケット内部のシミュレーション（イメージ）")

image_file = "perfect.png"
status_text = ""

if size > 3:
    image_file = "too_long.png"
    status_text = "💥 **立体障害発生！** 分子が長すぎるため、ポケット入り口にある『Thr315』の壁に激突して奥に入れません。"
elif size < 3:
    image_file = "too_short.png"
    status_text = "🔺 **長さ不足！** 分子が短すぎて、ポケットの最奥部まで薬の手が届いていません。"
else:
    if "プラス" in selected_charge:
        image_file = "perfect.png"
        status_text = "🎯 **ジャストフィット！** 長さも完璧で、エディタでデザインしたプラスの先端がポケット奥のマイナスと綺麗に引き合いました！"
    elif "マイナス" in selected_charge:
        image_file = "repulsion.png"
        status_text = "❌ **電気的反発！** 薬の先端がマイナスのため、ポケット奥のマイナス電荷と激しく反発して弾かれました。"
    else:
        image_file = "perfect.png"
        status_text = "🔺 **結合が弱い！** 収まってはいますが、電気的な引き合いがないため、外れやすいです。"

try:
    st.image(image_file, caption="タンパク質のポケット断面と薬のハマり具合", width=350)
except:
    st.warning(f"【ポケット画像】現在 『{image_file}』 を読み込み中です。GitHubに画像を保存するとここに表示されます。")

st.info(status_text)
