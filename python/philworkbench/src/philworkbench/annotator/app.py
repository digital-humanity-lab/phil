"""Phil Annotator — Lightweight Web UI for philosophical annotation.

Three annotation modes:
1. Thesis Annotation: Label extracted theses with school + validity
2. Concept Pair Evaluation: Rate cross-cultural concept mappings
3. School Classification Review: Verify classifier predictions

Run: streamlit run python/philworkbench/src/philworkbench/annotator/app.py
"""

import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime

from philworkbench.annotator.store import AnnotationStore

STORE_PATH = Path("data/annotations")


def main():
    st.set_page_config(
        page_title="Phil Annotator",
        page_icon="📜",
        layout="wide",
    )

    store = AnnotationStore(STORE_PATH)

    st.sidebar.title("Phil Annotator")
    annotator_name = st.sidebar.text_input("評価者名", key="annotator")
    if not annotator_name:
        st.warning("サイドバーで評価者名を入力してください")
        return

    mode = st.sidebar.radio("モード", [
        "テーゼ評価",
        "概念ペア評価",
        "学派分類レビュー",
        "統計・一致度",
    ])

    if mode == "テーゼ評価":
        thesis_annotation(store, annotator_name)
    elif mode == "概念ペア評価":
        concept_pair_evaluation(store, annotator_name)
    elif mode == "学派分類レビュー":
        school_review(store, annotator_name)
    elif mode == "統計・一致度":
        show_statistics(store)


# ═══════════════════════════════════════════════════════════════
# Mode 1: Thesis Annotation
# ═══════════════════════════════════════════════════════════════

SCHOOL_OPTIONS = [
    "Platonic", "Aristotelian", "Stoic", "Epicurean", "Neoplatonic",
    "Scholastic", "Rationalist", "Empiricist", "Kantian",
    "German Idealism", "Phenomenology", "Existentialism",
    "Analytic", "Pragmatism", "Critical Theory", "Poststructuralism",
    "Process Philosophy",
    "Confucian", "Daoist", "Legalist", "Mohist", "Chan/Zen Buddhist",
    "Neo-Confucian", "Kyoto School", "New Confucianism",
    "Nyaya", "Vaisheshika", "Samkhya", "Yoga", "Mimamsa", "Vedanta",
    "Buddhist (Madhyamaka)", "Buddhist (Yogacara)", "Jain",
    "Kalam", "Falsafa", "Sufi Philosophy", "Illuminationist",
    "Other", "Multiple", "Not a thesis",
]

THESIS_TYPE_OPTIONS = [
    "ontological", "epistemological", "ethical", "metaphysical",
    "aesthetic", "logical", "political", "existential", "other",
]


def thesis_annotation(store: AnnotationStore, annotator: str):
    st.header("テーゼ評価")
    st.markdown("抽出されたテーゼが哲学的主張として妥当か、どの学派に属するかを評価します。")

    # Load or upload thesis data
    uploaded = st.file_uploader("テーゼJSONファイル", type="json", key="thesis_upload")
    if uploaded:
        theses = json.load(uploaded)
        st.session_state["theses"] = theses
    elif "theses" not in st.session_state:
        # Demo data
        st.session_state["theses"] = _demo_theses()

    theses = st.session_state["theses"]
    total = len(theses)
    done = store.count_annotations("thesis", annotator)

    st.progress(min(done / max(total, 1), 1.0))
    st.caption(f"進捗: {done}/{total}")

    # Navigate
    idx = st.number_input("テーゼ番号", min_value=0, max_value=total - 1,
                          value=min(done, total - 1), key="thesis_idx")
    thesis = theses[idx]

    # Display
    st.subheader(f"テーゼ #{idx}")
    st.info(thesis.get("text", ""))

    if thesis.get("source"):
        st.caption(f"出典: {thesis['source']}")
    if thesis.get("system_school"):
        st.caption(f"システム予測: {thesis['system_school']}")
    if thesis.get("thesis_type"):
        st.caption(f"テーゼ種別 (自動): {thesis['thesis_type']}")

    # Annotation form
    col1, col2 = st.columns(2)
    with col1:
        is_thesis = st.radio(
            "これは哲学的テーゼか？",
            ["はい（哲学的主張である）", "いいえ（例示・解説・引用等）"],
            key=f"is_thesis_{idx}",
        )
    with col2:
        school = st.selectbox(
            "学派", SCHOOL_OPTIONS, key=f"school_{idx}",
        )

    thesis_type = st.selectbox(
        "テーゼ種別", THESIS_TYPE_OPTIONS, key=f"type_{idx}",
    )
    confidence = st.slider(
        "確信度（この評価にどれだけ自信があるか）", 1, 5, 3, key=f"conf_{idx}",
    )
    notes = st.text_area("メモ（任意）", key=f"notes_{idx}")

    if st.button("保存", key=f"save_thesis_{idx}"):
        store.save_annotation("thesis", {
            "item_id": f"thesis_{idx}",
            "annotator": annotator,
            "text": thesis.get("text", ""),
            "is_thesis": is_thesis.startswith("はい"),
            "school": school,
            "thesis_type": thesis_type,
            "confidence": confidence,
            "notes": notes,
            "system_school": thesis.get("system_school", ""),
            "timestamp": datetime.now().isoformat(),
        })
        st.success("保存しました")


# ═══════════════════════════════════════════════════════════════
# Mode 2: Concept Pair Evaluation
# ═══════════════════════════════════════════════════════════════

def concept_pair_evaluation(store: AnnotationStore, annotator: str):
    st.header("概念ペア評価")
    st.markdown("異文化間の概念マッピングの妥当性を評価します。")

    uploaded = st.file_uploader("概念ペアJSONファイル", type="json", key="pair_upload")
    if uploaded:
        pairs = json.load(uploaded)
        st.session_state["pairs"] = pairs
    elif "pairs" not in st.session_state:
        st.session_state["pairs"] = _demo_pairs()

    pairs = st.session_state["pairs"]
    total = len(pairs)
    done = store.count_annotations("concept_pair", annotator)

    st.progress(min(done / max(total, 1), 1.0))
    st.caption(f"進捗: {done}/{total}")

    idx = st.number_input("ペア番号", min_value=0, max_value=total - 1,
                          value=min(done, total - 1), key="pair_idx")
    pair = pairs[idx]

    # Display
    st.subheader(f"ペア #{idx}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**概念A**: {pair.get('concept_a', '')}")
        st.markdown(f"伝統: {pair.get('tradition_a', '')}")
        if pair.get("definition_a"):
            st.markdown(f"定義: {pair['definition_a']}")
    with col2:
        st.markdown(f"**概念B**: {pair.get('concept_b', '')}")
        st.markdown(f"伝統: {pair.get('tradition_b', '')}")
        if pair.get("definition_b"):
            st.markdown(f"定義: {pair['definition_b']}")

    if pair.get("system_score") is not None:
        st.caption(f"システムスコア: {pair['system_score']:.3f}")

    # Annotation
    validity = st.slider(
        "妥当性: この比較は哲学的に意味があるか？",
        1, 5, 3, key=f"validity_{idx}",
        help="1=無意味 2=こじつけ 3=一定の根拠あり 4=有意義 5=確立された比較",
    )
    similarity = st.slider(
        "類似度: 二つの概念はどの程度近いか？",
        1, 5, 3, key=f"similarity_{idx}",
        help="1=全く異なる 2=表面的類似のみ 3=部分的重複 4=かなり近い 5=ほぼ同義",
    )

    preserved = st.text_area(
        "この比較で保存されるもの（共通点）", key=f"preserved_{idx}",
    )
    lost = st.text_area(
        "この比較で失われるもの（相違点）", key=f"lost_{idx}",
    )
    references = st.text_area(
        "この比較を支持/否定する学術文献", key=f"refs_{idx}",
    )

    if st.button("保存", key=f"save_pair_{idx}"):
        store.save_annotation("concept_pair", {
            "item_id": f"pair_{idx}",
            "annotator": annotator,
            "concept_a": pair.get("concept_a", ""),
            "concept_b": pair.get("concept_b", ""),
            "validity": validity,
            "similarity": similarity,
            "preserved": preserved,
            "lost": lost,
            "references": references,
            "system_score": pair.get("system_score"),
            "timestamp": datetime.now().isoformat(),
        })
        st.success("保存しました")


# ═══════════════════════════════════════════════════════════════
# Mode 3: School Classification Review
# ═══════════════════════════════════════════════════════════════

def school_review(store: AnnotationStore, annotator: str):
    st.header("学派分類レビュー")
    st.markdown("分類器の予測結果を検証します。")

    uploaded = st.file_uploader("分類結果JSONファイル", type="json", key="review_upload")
    if uploaded:
        items = json.load(uploaded)
        st.session_state["reviews"] = items
    elif "reviews" not in st.session_state:
        st.session_state["reviews"] = _demo_reviews()

    items = st.session_state["reviews"]
    total = len(items)
    done = store.count_annotations("school_review", annotator)

    st.progress(min(done / max(total, 1), 1.0))
    idx = st.number_input("番号", min_value=0, max_value=total - 1,
                          value=min(done, total - 1), key="review_idx")
    item = items[idx]

    st.subheader(f"分類 #{idx}")
    st.info(item.get("text", ""))
    st.markdown(f"**システム予測**: {item.get('predicted', '')} (確信度: {item.get('confidence', 0):.3f})")

    correct = st.radio(
        "Top-1予測は正しいか？",
        ["正しい", "正しくない", "部分的に正しい（関連する学派だが最適ではない）"],
        key=f"correct_{idx}",
    )
    correct_school = st.selectbox(
        "正しい学派（予測が誤りの場合）", ["(予測が正しい)"] + SCHOOL_OPTIONS,
        key=f"correct_school_{idx}",
    )

    if st.button("保存", key=f"save_review_{idx}"):
        store.save_annotation("school_review", {
            "item_id": f"review_{idx}",
            "annotator": annotator,
            "text": item.get("text", ""),
            "predicted": item.get("predicted", ""),
            "correct": correct,
            "correct_school": correct_school,
            "timestamp": datetime.now().isoformat(),
        })
        st.success("保存しました")


# ═══════════════════════════════════════════════════════════════
# Mode 4: Statistics & Agreement
# ═══════════════════════════════════════════════════════════════

def show_statistics(store: AnnotationStore):
    st.header("統計・評価者間一致度")

    for task_type in ["thesis", "concept_pair", "school_review"]:
        annotations = store.load_all(task_type)
        if not annotations:
            continue

        st.subheader(f"{task_type} ({len(annotations)}件)")

        # Per-annotator counts
        annotators = {}
        for a in annotations:
            name = a.get("annotator", "unknown")
            annotators[name] = annotators.get(name, 0) + 1
        st.markdown("**評価者別件数**")
        for name, count in sorted(annotators.items()):
            st.markdown(f"- {name}: {count}件")

        # Inter-annotator agreement (if multiple annotators)
        if len(annotators) >= 2 and task_type == "thesis":
            _compute_thesis_agreement(annotations, st)
        elif len(annotators) >= 2 and task_type == "concept_pair":
            _compute_pair_agreement(annotations, st)


def _compute_thesis_agreement(annotations, st):
    """Compute agreement on thesis school labels."""
    # Group by item_id
    by_item: dict[str, list] = {}
    for a in annotations:
        by_item.setdefault(a["item_id"], []).append(a)

    # Items with 2+ annotations
    multi = {k: v for k, v in by_item.items() if len(v) >= 2}
    if not multi:
        st.info("2名以上の評価がある項目がありません")
        return

    agree = 0
    total = 0
    for item_id, anns in multi.items():
        schools = [a["school"] for a in anns]
        for i in range(len(schools)):
            for j in range(i + 1, len(schools)):
                total += 1
                if schools[i] == schools[j]:
                    agree += 1

    if total > 0:
        pct = agree / total
        st.metric("学派ラベル一致率", f"{pct:.1%}", f"{agree}/{total}ペア")
        # Simple Krippendorff's alpha approximation
        # alpha ≈ 1 - (1-po)/(1-pe) where po=observed, pe=expected
        n_labels = len(set(a["school"] for a in annotations))
        pe = 1.0 / max(n_labels, 1)
        alpha = 1 - (1 - pct) / (1 - pe) if pe < 1 else 0
        st.metric("Krippendorff's α (近似)", f"{alpha:.3f}")


def _compute_pair_agreement(annotations, st):
    """Compute agreement on concept pair similarity ratings."""
    by_item: dict[str, list] = {}
    for a in annotations:
        by_item.setdefault(a["item_id"], []).append(a)

    multi = {k: v for k, v in by_item.items() if len(v) >= 2}
    if not multi:
        st.info("2名以上の評価がある項目がありません")
        return

    import numpy as np
    diffs = []
    for item_id, anns in multi.items():
        sims = [a["similarity"] for a in anns]
        for i in range(len(sims)):
            for j in range(i + 1, len(sims)):
                diffs.append(abs(sims[i] - sims[j]))

    if diffs:
        avg_diff = np.mean(diffs)
        st.metric("類似度評価の平均差異", f"{avg_diff:.2f}", "（5段階, 低いほど一致）")


# ═══════════════════════════════════════════════════════════════
# Demo data
# ═══════════════════════════════════════════════════════════════

def _demo_theses():
    return [
        {"text": "Pure reason is a perfect unity; and therefore, if the principle presented by it prove to be insufficient for the solution of even a single one of these questions, we must reject it.",
         "source": "Kant, Critique of Pure Reason", "system_school": "Kantian", "thesis_type": "epistemological"},
        {"text": "For to me it seems evident, that the essence of the mind being equally unknown to us with that of external bodies.",
         "source": "Hume, Treatise", "system_school": "Empiricist", "thesis_type": "ontological"},
        {"text": "純粋経験とは主客の分離に先立つ直接的な経験のことである。",
         "source": "西田幾多郎, 善の研究", "system_school": "Kyoto School", "thesis_type": "epistemological"},
        {"text": "人間の存在は本質的に間柄的である。",
         "source": "和辻哲郎, 倫理学", "system_school": "Kyoto School", "thesis_type": "ontological"},
        {"text": "The virtues are based on justice, of which common honesty in buying and selling is the shadow.",
         "source": "Plato, Republic", "system_school": "Platonic", "thesis_type": "ethical"},
        {"text": "The world is my idea: this is a truth which holds good for everything that lives and knows.",
         "source": "Schopenhauer, World as Will", "system_school": "German Idealism", "thesis_type": "epistemological"},
        {"text": "Whatever is dependently co-arisen, that is explained to be emptiness.",
         "source": "Nagarjuna, MMK", "system_school": "Buddhist (Madhyamaka)", "thesis_type": "ontological"},
        {"text": "絶対無の場所においてこそ自覚が成立する。",
         "source": "西田幾多郎, 場所", "system_school": "Kyoto School", "thesis_type": "ontological"},
        {"text": "Existence precedes essence.",
         "source": "Sartre, Existentialism is a Humanism", "system_school": "Existentialism", "thesis_type": "ontological"},
        {"text": "Brahman is the ultimate reality. Atman is Brahman.",
         "source": "Mandukya Upanishad", "system_school": "Vedanta", "thesis_type": "metaphysical"},
    ]


def _demo_pairs():
    return [
        {"concept_a": "間柄 (aidagara)", "concept_b": "I-Thou (Buber)",
         "tradition_a": "Kyoto School", "tradition_b": "Western Relational Ontology",
         "definition_a": "人間存在の根本構造としての関係性", "definition_b": "The mutual, direct encounter with the other as a whole being",
         "system_score": 0.661},
        {"concept_a": "絶対無 (zettai mu)", "concept_b": "śūnyatā",
         "tradition_a": "Kyoto School", "tradition_b": "Buddhism (Madhyamaka)",
         "definition_a": "あらゆる有を包む究極の場所", "definition_b": "Emptiness of inherent existence",
         "system_score": 0.668},
        {"concept_a": "仁 (ren)", "concept_b": "karuṇā",
         "tradition_a": "Confucianism", "tradition_b": "Buddhism",
         "definition_a": "仁者愛人", "definition_b": "Compassion for all sentient beings",
         "system_score": 0.508},
        {"concept_a": "仁 (ren)", "concept_b": "will to power",
         "tradition_a": "Confucianism", "tradition_b": "Continental",
         "definition_a": "仁者愛人", "definition_b": "Self-overcoming drive",
         "system_score": 0.248},
        {"concept_a": "道 (dao)", "concept_b": "logos",
         "tradition_a": "Daoism", "tradition_b": "Presocratic",
         "definition_a": "天地万物の本源", "definition_b": "The rational principle governing the cosmos",
         "system_score": 0.476},
    ]


def _demo_reviews():
    return [
        {"text": "Human reason, in one sphere of its cognition, is called upon to consider questions, which it cannot decline.",
         "predicted": "Kantian", "confidence": 0.805},
        {"text": "Pure experience is the direct, unified state of consciousness prior to the separation of subject and object.",
         "predicted": "Kyoto School", "confidence": 0.748},
        {"text": "All men by nature desire to know.",
         "predicted": "Aristotelian", "confidence": 0.621},
    ]


if __name__ == "__main__":
    main()
