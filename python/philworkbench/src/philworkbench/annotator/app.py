"""Phil Annotator — 哲学研究者のためのアノテーション支援ツール

哲学テキストから自動抽出された「テーゼ（哲学的主張）」や
「異文化間の概念対応」をレビュー・評価するためのWebアプリケーション。

起動: streamlit run app.py
"""

import sys
import re
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

PHIL_ROOT = Path(__file__).resolve().parents[5]
for pkg in ["philtext", "philcore", "philworkbench"]:
    sys.path.insert(0, str(PHIL_ROOT / "python" / pkg / "src"))

from philworkbench.annotator.store import AnnotationStore

STORE_PATH = PHIL_ROOT / "data" / "annotations"
SEED_PATH = Path("/home/matsui/github/digital-philosophy-ecosystem/data/seed")
GUT_PATH = Path("/home/matsui/github/digital-philosophy-ecosystem/data/gutenberg")
MODEL_PATH = Path("/home/matsui/github/digital-philosophy-ecosystem/models/philmap-e5-finetuned-v2")

GUTENBERG_BOOKS = {
    "Hume — A Treatise of Human Nature": "4705_hume.txt",
    "Kant — Critique of Pure Reason": "4280_kant.txt",
    "Plato — Republic": "1497_plato.txt",
    "Plato — Apology": "1656_plato.txt",
    "Locke — Essay Concerning Understanding": "10615_descartes.txt",
    "Locke — Second Treatise of Government": "7370_nietzsche.txt",
    "Schopenhauer — World as Will and Idea": "38427_nietzsche.txt",
    "Russell — Problems of Philosophy": "5827_kant.txt",
    "Machiavelli — The Prince": "1232_machiavelli.txt",
    "Mill — Utilitarianism": "11224_hobbes.txt",
    "Montaigne — Essays": "3600_locke.txt",
    "Hume — Enquiry Concerning Understanding": "9662_aristotle.txt",
}

SCHOOL_OPTIONS = [
    "— 西洋 —",
    "Platonic", "Aristotelian", "Stoic", "Epicurean", "Neoplatonic",
    "Scholastic", "Rationalist", "Empiricist", "Kantian",
    "German Idealism", "Phenomenology", "Existentialism",
    "Analytic", "Pragmatism", "Critical Theory", "Poststructuralism",
    "— 東アジア —",
    "Confucian", "Daoist", "Legalist", "Mohist",
    "Chan/Zen Buddhist", "Neo-Confucian", "Kyoto School",
    "— 南アジア —",
    "Nyaya", "Vedanta", "Buddhist (Madhyamaka)", "Buddhist (Yogacara)", "Jain",
    "— イスラーム —",
    "Kalam", "Falsafa", "Sufi Philosophy",
    "— その他 —",
    "Other", "Multiple schools", "Not a philosophical thesis",
]

THESIS_TYPES = {
    "ontological": "存在論的 — 存在・実在・本質に関する主張",
    "epistemological": "認識論的 — 知識・真理・認識に関する主張",
    "ethical": "倫理的 — 善悪・義務・徳に関する主張",
    "metaphysical": "形而上学的 — 究極的実在・因果・必然性に関する主張",
    "aesthetic": "美学的 — 美・芸術・趣味に関する主張",
    "existential": "実存的 — 自由・意味・死に関する主張",
    "political": "政治哲学的 — 正義・権利・統治に関する主張",
    "other": "その他",
}


def main():
    st.set_page_config(
        page_title="Phil Annotator",
        page_icon="📜",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS — dark-text-on-light-background, works in both light/dark themes
    st.markdown("""
    <style>
    .stExpander { border: 1px solid #888; border-radius: 8px; margin-bottom: 8px; }
    .thesis-text { font-size: 1.15em; line-height: 1.7; padding: 12px;
                   background: #1a1a2e; color: #e0e0e0;
                   border-left: 4px solid #4a86c8;
                   border-radius: 4px; margin: 8px 0; }
    .concept-card { padding: 16px; background: #1a1a2e; color: #e0e0e0;
                    border-radius: 8px; border: 1px solid #555; }
    .concept-card h3 { color: #7cb8f7; }
    .concept-card p { color: #d0d0d0; }
    .concept-card strong { color: #a0c4ff; }
    .guide-box { padding: 12px 16px; background: #2a2a1e; color: #e0d080;
                 border-radius: 8px; border-left: 4px solid #ffc107;
                 margin-bottom: 16px; }
    .guide-box strong { color: #ffe066; }
    .step-number { display: inline-block; width: 28px; height: 28px;
                   background: #4a86c8; color: white; border-radius: 50%;
                   text-align: center; line-height: 28px; font-weight: bold;
                   margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

    store = AnnotationStore(STORE_PATH)

    # ── Sidebar ──────────────────────────────────────────────
    with st.sidebar:
        st.title("📜 Phil Annotator")
        st.markdown("哲学テキスト・概念の評価ツール")
        st.divider()

        annotator_name = st.text_input(
            "👤 あなたの名前",
            placeholder="例: 松井",
            help="評価結果に記録されます。複数の評価者のデータを比較するために使います。",
        )

        st.divider()
        mode = st.radio("📋 作業を選択", [
            "テーゼの評価",
            "概念ペアの評価",
            "これまでの結果",
        ], help="左から順に進めるのがおすすめです")

        st.divider()
        st.caption("Phil Ecosystem v0.1")
        st.caption("Digital Humanity Lab")

    # ── Main ─────────────────────────────────────────────────
    if not annotator_name:
        _show_welcome()
        return

    if mode == "テーゼの評価":
        thesis_mode(store, annotator_name)
    elif mode == "概念ペアの評価":
        concept_pair_mode(store, annotator_name)
    elif mode == "これまでの結果":
        stats_mode(store, annotator_name)


# ═══════════════════════════════════════════════════════════════
# Welcome
# ═══════════════════════════════════════════════════════════════

def _show_welcome():
    st.title("📜 Phil Annotator へようこそ")
    st.markdown("""
    このツールは、哲学テキストの計算的分析の精度を向上させるために、
    **哲学研究者の専門的判断**を収集するものです。

    ---

    ### このツールで行うこと

    **1. テーゼの評価**
    > 哲学テキストからコンピュータが自動抽出した「テーゼ（哲学的主張）」を読み、
    > それが本当にテーゼか、どの学派の主張かを判定します。

    **2. 概念ペアの評価**
    > 「和辻の間柄 ↔ BuberのI-Thou」のような異文化間の概念対応について、
    > その妥当性と類似度を評価します。

    ---

    **← サイドバーで名前を入力して開始してください**
    """)


# ═══════════════════════════════════════════════════════════════
# テーゼ評価
# ═══════════════════════════════════════════════════════════════

def thesis_mode(store: AnnotationStore, annotator: str):
    st.title("テーゼの評価")

    # Step 1: テキスト選択
    st.markdown("""
    <div class="guide-box">
    <span class="step-number">1</span>
    <strong>テキストを選んでください。</strong>
    選んだテキストから、コンピュータが哲学的主張（テーゼ）を自動抽出します。
    </div>
    """, unsafe_allow_html=True)

    input_method = st.radio(
        "テキストの種類を選んでください",
        ["📚 西洋哲学古典（英語）", "📖 東洋哲学（日本語・中国語）", "✏️ テキストを貼り付け"],
        horizontal=True,
    )

    text = ""
    source_label = ""
    lang = "en"

    if input_method.startswith("📚"):
        book = st.selectbox(
            "書籍を選んでください",
            list(GUTENBERG_BOOKS.keys()),
            help="Project Gutenbergから取得した哲学書の全文です",
        )
        fname = GUTENBERG_BOOKS[book]
        fp = GUT_PATH / fname
        if fp.exists():
            raw = _load_gutenberg(fp)
            max_page = max(0, len(raw) // 3000)
            page = st.slider("テキストの位置", 0, max_page, 0,
                            help="書籍内の位置をスライドで選べます")
            text = raw[page * 3000:(page + 1) * 3000]
            source_label = book
            with st.expander("テキストを表示", expanded=False):
                st.text(text[:1500])

    elif input_method.startswith("📖"):
        ja_samples = {
            "西田幾多郎『善の研究』": (
                "純粋経験とは主客の分離に先立つ直接的な経験のことである。"
                "意識現象を精密に見れば、つねにまずこの直接的な統一的状態がある。"
                "思惟も意志もすべてこの経験の分化にほかならない。"
                "個人あって経験あるにあらず、経験あって個人あるのである。"
            ),
            "和辻哲郎『倫理学』": (
                "人間の存在は本質的に間柄的である。"
                "個人主義的な倫理学はその根本において誤っている。"
                "なぜなら個人はつねにすでに他者との関係の中にあるからである。"
                "したがって倫理学は間柄の学でなければならない。"
            ),
            "西谷啓治『宗教とは何か』": (
                "空の立場は、ニヒリズムの克服と同時に、有の立場の超越を意味する。"
                "虚無を超えて空へ至ることが宗教の本質である。"
                "絶対無の場所においてこそ自覚が成立する。"
                "空は空自身を空じる。"
            ),
            "『道徳経』": (
                "道可道、非常道。名可名、非常名。"
                "無名天地之始、有名万物之母。"
                "故常無欲以観其妙、常有欲以観其徼。"
                "此両者同出而異名、同謂之玄。玄之又玄、衆妙之門。"
            ),
            "『論語』": (
                "子曰、学而時習之、不亦説乎。"
                "有朋自遠方来、不亦楽乎。"
                "人不知而不慍、不亦君子乎。"
                "子曰、巧言令色、鮮矣仁。"
            ),
        }
        sample = st.selectbox("テキストを選んでください", list(ja_samples.keys()))
        text = ja_samples[sample]
        source_label = sample
        lang = "ja"
        st.markdown(f"> {text}")

    else:  # 貼り付け
        text = st.text_area(
            "哲学テキストを貼り付けてください",
            height=200,
            placeholder="テキストを貼り付けると、哲学的主張を自動抽出します...",
        )
        source_label = "user_input"
        if text and any(ord(c) > 0x3000 for c in text[:100]):
            lang = "ja"

    if not text or len(text.strip()) < 20:
        st.caption("↑ テキストを選択または入力すると、次のステップに進めます")
        return

    # Step 2: テーゼ抽出
    st.markdown("""
    <div class="guide-box">
    <span class="step-number">2</span>
    <strong>「テーゼを抽出」ボタンを押してください。</strong>
    コンピュータがテキストから哲学的主張を自動検出します。
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 テーゼを抽出", type="primary", use_container_width=True):
        with st.spinner("テーゼを抽出中..."):
            results = _extract_and_classify(text, lang, source_label)
        if results:
            st.session_state["thesis_results"] = results
            st.session_state["thesis_source"] = source_label
        else:
            st.warning("テーゼが見つかりませんでした。別のテキストを試してください。")
            return

    if "thesis_results" not in st.session_state:
        return

    results = st.session_state["thesis_results"]

    # Step 3: 評価
    st.markdown(f"""
    <div class="guide-box">
    <span class="step-number">3</span>
    <strong>{len(results)}件のテーゼが見つかりました。</strong>
    各テーゼを開いて評価してください。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **評価の観点:**
    - **これはテーゼか？** — 哲学的主張として成立しているか。単なる説明・例示・引用ではないか。
    - **学派** — この主張はどの哲学的伝統に最も近いか。
    - **種別** — 存在論的、認識論的、倫理的、形而上学的、...のどれか。
    """)

    done = store.count_annotations("thesis", annotator)
    remaining = len(results) - done
    if remaining > 0:
        st.info(f"📝 残り **{remaining}件** の評価があります")
    else:
        st.success("✅ 全てのテーゼを評価しました！")

    for i, r in enumerate(results):
        _render_thesis_item(i, r, store, annotator)


def _render_thesis_item(i: int, r: dict, store: AnnotationStore, annotator: str):
    """Render one thesis item with annotation form."""
    # Check if already annotated
    existing = store.load_by_item("thesis", f"thesis_{i}")
    my_annotations = [a for a in existing if a.get("annotator") == annotator]
    is_done = len(my_annotations) > 0

    # Expander label
    status = "✅" if is_done else f"#{i + 1}"
    ttype = r.get("thesis_type", "")
    ttype_ja = THESIS_TYPES.get(ttype, ttype).split("—")[0].strip() if ttype else ""
    predicted = r.get("system_school", "")

    label = f"{status}  {r['text'][:50]}..."
    if predicted:
        label += f"  →  {predicted}"

    with st.expander(label, expanded=(not is_done and i == 0)):
        # Thesis display with optional translation
        st.markdown(
            f'<div class="thesis-text">{r["text"]}</div>',
            unsafe_allow_html=True,
        )
        # Show Japanese translation for English theses
        if r.get("text") and not any(ord(c) > 0x3000 for c in r["text"][:20]):
            with st.popover("🌐 日本語訳を表示"):
                ja = _translate_cache(r["text"])
                st.markdown(f"**日本語訳（自動）:**\n\n{ja}")

        # System prediction (shown as reference, not as correct answer)
        if predicted:
            conf = r.get("system_confidence", 0)
            st.caption(
                f"🤖 コンピュータの予測: **{predicted}** "
                f"(確信度: {conf:.0%})　|　"
                f"自動検出された種別: {ttype_ja}"
            )
            if r.get("top3"):
                top3_str = "、".join(f"{s} ({sc:.0%})" for s, sc in r["top3"])
                st.caption(f"候補: {top3_str}")

        st.divider()

        # Annotation form
        st.markdown("**あなたの評価:**")

        is_thesis = st.radio(
            "これは哲学的テーゼ（主張）ですか？",
            [
                "はい — 賛否を問える哲学的主張である",
                "微妙 — 主張ではあるが哲学的とは言い切れない",
                "いいえ — 例示・説明・引用・感想であり、テーゼではない",
            ],
            key=f"is_{i}",
            help="テーゼとは「哲学者が主張として提示し、他の哲学者が同意・反論できる命題」のことです",
        )

        if not is_thesis.startswith("いいえ"):
            col1, col2 = st.columns(2)
            with col1:
                school = st.selectbox(
                    "最も近い学派・伝統",
                    [s for s in SCHOOL_OPTIONS if not s.startswith("—")],
                    key=f"sch_{i}",
                    help="この主張がどの哲学的伝統に属するか。複数にまたがる場合は「Multiple schools」を選んでください",
                )
            with col2:
                ttype_options = list(THESIS_TYPES.keys())
                ttype_labels = [THESIS_TYPES[k] for k in ttype_options]
                ttype_idx = st.selectbox(
                    "テーゼの種別",
                    range(len(ttype_options)),
                    format_func=lambda x: ttype_labels[x],
                    key=f"tt_{i}",
                    help="このテーゼが扱っている哲学的問題の領域",
                )
                thesis_type = ttype_options[ttype_idx]
        else:
            school = "Not a philosophical thesis"
            thesis_type = "other"

        notes = st.text_input(
            "メモ（任意）",
            key=f"note_{i}",
            placeholder="判断の理由や補足があれば記入してください",
        )

        if st.button("💾 保存", key=f"save_{i}", use_container_width=True):
            store.save_annotation("thesis", {
                "item_id": f"thesis_{i}",
                "annotator": annotator,
                "text": r["text"],
                "is_thesis": not is_thesis.startswith("いいえ"),
                "is_borderline": is_thesis.startswith("微妙"),
                "school": school,
                "thesis_type": thesis_type,
                "system_school": r.get("system_school", ""),
                "system_confidence": r.get("system_confidence", 0),
                "notes": notes,
                "source": r.get("source", ""),
                "timestamp": datetime.now().isoformat(),
            })
            st.success("保存しました ✓")
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# 概念ペア評価
# ═══════════════════════════════════════════════════════════════

def concept_pair_mode(store: AnnotationStore, annotator: str):
    st.title("概念ペアの評価")

    st.markdown("""
    <div class="guide-box">
    異文化間の哲学的概念の対応関係を評価します。<br>
    左右に表示される二つの概念を読み、<strong>この比較が哲学的に意味があるか</strong>、
    <strong>二つの概念がどの程度似ているか</strong>を判断してください。
    </div>
    """, unsafe_allow_html=True)

    pairs = _load_concept_pairs()
    if not pairs:
        st.warning("概念ペアデータが見つかりません")
        return

    done = store.count_annotations("concept_pair", annotator)
    remaining = len(pairs) - done
    if remaining > 0:
        st.info(f"📝 残り **{remaining}ペア** の評価があります")
    else:
        st.success("✅ 全てのペアを評価しました！")

    for i, pair in enumerate(pairs):
        existing = store.load_by_item("concept_pair", f"pair_{i}")
        my = [a for a in existing if a.get("annotator") == annotator]
        is_done = len(my) > 0
        status = "✅" if is_done else f"#{i + 1}"

        with st.expander(
            f"{status}  {pair['a_term']}  ↔  {pair['b_term']}",
            expanded=(not is_done and i == 0),
        ):
            # Two concept cards side by side
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="concept-card">
                <h3>{pair['a_term']}</h3>
                <p><strong>伝統:</strong> {pair['a_tradition']}</p>
                <p>{pair['a_def']}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="concept-card">
                <h3>{pair['b_term']}</h3>
                <p><strong>伝統:</strong> {pair['b_tradition']}</p>
                <p>{pair['b_def']}</p>
                </div>
                """, unsafe_allow_html=True)

            if pair.get("scholarly_basis"):
                st.caption(f"📚 学術的根拠: {pair['scholarly_basis']}")

            st.divider()
            st.markdown("**あなたの評価:**")

            validity = st.select_slider(
                "この比較は哲学的に意味がありますか？",
                options=[
                    "1 — 無意味な比較",
                    "2 — こじつけに近い",
                    "3 — 一定の根拠がある",
                    "4 — 有意義な比較",
                    "5 — 確立された比較",
                ],
                value="3 — 一定の根拠がある",
                key=f"val_{i}",
            )

            similarity = st.select_slider(
                "二つの概念はどの程度近いですか？",
                options=[
                    "1 — 全く異なる概念",
                    "2 — 表面的な類似のみ",
                    "3 — 部分的に重なる",
                    "4 — かなり近い",
                    "5 — ほぼ同義",
                ],
                value="3 — 部分的に重なる",
                key=f"sim_{i}",
            )

            preserved = st.text_area(
                "この比較で保存されるもの（二つの概念に共通する要素）",
                key=f"pres_{i}",
                placeholder="例: どちらも人間の本質を関係性に見出している",
                height=68,
            )
            lost = st.text_area(
                "この比較で失われるもの（見落とされる相違点）",
                key=f"lost_{i}",
                placeholder="例: 間柄には空間的・風土的要素があるがI-Thouにはない",
                height=68,
            )

            if st.button("💾 保存", key=f"save_p_{i}", use_container_width=True):
                store.save_annotation("concept_pair", {
                    "item_id": f"pair_{i}",
                    "annotator": annotator,
                    "concept_a": pair["a_term"],
                    "concept_b": pair["b_term"],
                    "validity": int(validity[0]),
                    "similarity": int(similarity[0]),
                    "preserved": preserved,
                    "lost": lost,
                    "scholarly_basis": pair.get("scholarly_basis", ""),
                    "timestamp": datetime.now().isoformat(),
                })
                st.success("保存しました ✓")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# 統計
# ═══════════════════════════════════════════════════════════════

def stats_mode(store: AnnotationStore, annotator: str):
    st.title("これまでの結果")

    # Thesis stats
    thesis_anns = store.load_all("thesis")
    st.subheader(f"テーゼ評価: {len(thesis_anns)}件")

    if thesis_anns:
        my_thesis = [a for a in thesis_anns if a.get("annotator") == annotator]
        st.markdown(f"あなたの評価: **{len(my_thesis)}件**")

        if my_thesis:
            # System accuracy vs your labels
            correct = sum(1 for a in my_thesis
                         if a.get("school") == a.get("system_school"))
            st.metric(
                "コンピュータ予測の正解率（あなたの評価に対して）",
                f"{correct} / {len(my_thesis)} = {correct/max(len(my_thesis),1):.0%}",
            )

            # Your label distribution
            from collections import Counter
            schools = Counter(a["school"] for a in my_thesis
                            if a.get("is_thesis"))
            if schools:
                st.markdown("**あなたが付けた学派ラベルの分布:**")
                for school, count in schools.most_common(10):
                    bar = "█" * count
                    st.text(f"  {school:25s} {bar} ({count})")

    # Concept pair stats
    pair_anns = store.load_all("concept_pair")
    st.subheader(f"概念ペア評価: {len(pair_anns)}件")

    if pair_anns:
        my_pairs = [a for a in pair_anns if a.get("annotator") == annotator]
        st.markdown(f"あなたの評価: **{len(my_pairs)}件**")

        if my_pairs:
            import numpy as np
            vals = [a["validity"] for a in my_pairs]
            sims = [a["similarity"] for a in my_pairs]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("平均妥当性", f"{np.mean(vals):.1f} / 5")
            with col2:
                st.metric("平均類似度", f"{np.mean(sims):.1f} / 5")

    if not thesis_anns and not pair_anns:
        st.info("まだ評価データがありません。「テーゼの評価」または「概念ペアの評価」から始めてください。")


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _load_gutenberg(fp: Path) -> str:
    raw = fp.read_text(errors="ignore")
    si = raw.find("*** START")
    if si > 0:
        raw = raw[raw.find("\n", si) + 1:]
    ei = raw.find("*** END")
    if ei > 0:
        raw = raw[:ei]
    return raw


def _extract_and_classify(text: str, lang: str, source: str) -> list[dict]:
    from philtext.argument.thesis import ThesisExtractor
    ext = ThesisExtractor(
        language=lang,
        min_philosophical_terms=1 if lang == "ja" else 2,
    )
    if lang == "en":
        paras = [re.sub(r"\s+", " ", p.strip())
                for p in text.split("\n\n") if len(p.strip()) > 50]
        theses = ext.extract_from_paragraphs(paras, top_k=15)
    else:
        theses = ext.extract(text)

    clf = _get_classifier()
    results = []
    for t in theses:
        pred = clf.classify(t.text, top_k=3) if clf else None
        results.append({
            "text": t.text,
            "thesis_type": t.thesis_type.value if t.thesis_type else "",
            "confidence": t.confidence,
            "system_school": pred.school if pred else "",
            "system_confidence": pred.confidence if pred else 0,
            "top3": [(s, round(sc, 3)) for s, sc in pred.top_k] if pred else [],
            "source": source,
        })
    return results


@st.cache_resource
def _get_classifier():
    try:
        from philtext.classify.school import SchoolClassifier
        clf = SchoolClassifier(method="prototype", embedding_model=str(MODEL_PATH))
        clf.load_default_examples()
        return clf
    except Exception:
        return None


def _load_concept_pairs():
    try:
        import yaml
        fp = SEED_PATH / "cross_tradition_pairs.yaml"
        if not fp.exists():
            return []
        with open(fp) as f:
            data = yaml.safe_load(f)
        pairs = []
        for p in data.get("positive_pairs", []):
            ca, cb = p["concept_a"], p["concept_b"]
            pairs.append({
                "a_term": ca.get("term_en", ca.get("term_ja", "")),
                "b_term": cb.get("term_en", cb.get("term_de", "")),
                "a_tradition": ca.get("tradition", ""),
                "b_tradition": cb.get("tradition", ""),
                "a_def": ca.get("definition_en", ca.get("definition_ja", "")),
                "b_def": cb.get("definition_en", cb.get("definition_de", "")),
                "expected": p.get("expected_similarity", ""),
                "scholarly_basis": p.get("scholarly_basis", ""),
            })
        return pairs
    except Exception:
        return []


@st.cache_data(ttl=3600)
def _translate_cache(text: str) -> str:
    """Translate English philosophical text to Japanese.

    Uses LLM if available, otherwise falls back to a simple
    philosophical term glossary.
    """
    # Try LLM first
    try:
        from litellm import completion
        resp = completion(
            model="claude-haiku-4-5-20251001",
            messages=[{
                "role": "user",
                "content": (
                    "以下の英語の哲学テキストを日本語に翻訳してください。"
                    "哲学用語は慣用的な訳語を使ってください。"
                    "訳文のみ出力してください。\n\n"
                    f"{text}"
                ),
            }],
            temperature=0.1,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        pass

    # Fallback: glossary-based partial translation
    GLOSSARY = {
        "being": "存在", "existence": "実存", "essence": "本質",
        "substance": "実体", "reality": "実在", "truth": "真理",
        "knowledge": "知識", "reason": "理性", "understanding": "悟性",
        "experience": "経験", "perception": "知覚", "consciousness": "意識",
        "intuition": "直観", "imagination": "構想力",
        "freedom": "自由", "will": "意志", "duty": "義務",
        "virtue": "徳", "justice": "正義", "good": "善", "evil": "悪",
        "beauty": "美", "soul": "魂", "mind": "精神", "self": "自己",
        "cause": "原因", "effect": "結果", "purpose": "目的",
        "necessary": "必然的", "possible": "可能的", "universal": "普遍的",
        "particular": "特殊的", "absolute": "絶対的", "infinite": "無限",
        "moral": "道徳的", "ethical": "倫理的", "rational": "合理的",
        "empirical": "経験的", "transcendental": "超越論的",
        "a priori": "ア・プリオリ", "a posteriori": "ア・ポステリオリ",
        "synthetic": "総合的", "analytic": "分析的",
        "phenomenon": "現象", "noumenon": "物自体",
        "the thing in itself": "物自体", "things in themselves": "物自体",
        "categorical imperative": "定言命法",
        "pure reason": "純粋理性", "practical reason": "実践理性",
    }
    result = text
    for en, ja in sorted(GLOSSARY.items(), key=lambda x: -len(x[0])):
        import re as _re
        result = _re.sub(
            r'\b' + _re.escape(en) + r'\b',
            f"{en}({ja})",
            result,
            flags=_re.IGNORECASE,
        )
    return f"[用語注釈付き原文 — LLM翻訳が利用できないため]\n\n{result}"


if __name__ == "__main__":
    main()
