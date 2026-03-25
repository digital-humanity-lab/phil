# Phil Ecosystem — 統合アーキテクチャ設計書

> **哲学研究のための計算基盤エコシステム**
>
>> Version: 2.0.0-draft
> Date: 2026-03-23
> Author: Yusuke Matsui

---

## 目次

1. [ビジョンと動機](#1-ビジョンと動機)
2. [設計原理](#2-設計原理)
3. [エコシステム全体構造](#3-エコシステム全体構造)
4. [リポジトリ構成](#4-リポジトリ構成)
5. [パッケージ仕様](#5-パッケージ仕様)
   - 5.1 [コアデータ構造層: philcore](#51-コアデータ構造層-philcore)
   - 5.2 [定量化エンジン層: philengine](#52-定量化エンジン層-philengine)
   - 5.3 [概念整列層: philmap](#53-概念整列層-philmap)
   - 5.4 [テキスト解析層: philtext](#54-テキスト解析層-philtext)
   - 5.5 [知識グラフ層: philgraph](#55-知識グラフ層-philgraph)
   - 5.6 [統合ワークベンチ層: philworkbench](#56-統合ワークベンチ層-philworkbench)
   - 5.7 [API層: philapi](#57-api層-philapi)
   - 5.8 [アノテーションデータベース](#58-アノテーションデータベース)
   - 5.9 [データリポジトリ](#59-データリポジトリ)
6. [PhilCorpus データコンテナ仕様](#6-philcorpus-データコンテナ仕様)
7. [R/Python 二言語戦略](#7-rpython-二言語戦略)
8. [既存リポジトリからの移行計画](#8-既存リポジトリからの移行計画)
9. [依存関係グラフ](#9-依存関係グラフ)
10. [実装ロードマップ](#10-実装ロードマップ)

---

## 1. ビジョンと動機

### 1.1 根本的問い

> 計算は哲学に対して、望遠鏡が天文学に対して果たしたのと同じ役割を果たせるか？

望遠鏡は「肉眼では見えなかったもの」を見えるようにし、天文学のパラダイムを変えた。
本エコシステムは、**いかなる個人の読解でも到達できなかった概念間の関係**を計算的に
可視化することで、哲学研究のパラダイムシフトを目指す。

### 1.2 哲学分野に固有の課題

| 課題 | 他分野との比較 |
|------|---------------|
| **解釈の不確定性** | 自然科学にはground truthがあるが哲学にはない |
| **概念の通約不可能性** | 和辻の「間柄」とHeideggerの「Mitsein」の類似性の意味自体が哲学的問題 |
| **テキストの多言語性** | ギリシャ語・漢文・サンスクリット語・アラビア語・現代諸語、2500年のスパン |
| **形式化への文化的抵抗** | 哲学者コミュニティの多くが形式化＝矮小化と見なす |
| **正典中心主義** | 少数テキストへの集中。周縁化された伝統の不可視化 |

### 1.3 パラダイムシフトの本質的要素

1. **概念の経験的研究への転換** — 概念を論証の対象としてだけでなく、経験的研究の対象として扱う
2. **単一学者の認知限界の超越** — いかなる個人も持ち得ない多言語・多伝統横断的視野を組織的に提供
3. **解釈の追跡可能性（hermeneutic traceability）** — 同一テキストに対する解釈の分岐・変遷を明示化
4. **正典（canon）から全体（corpus）へ** — 周縁化されたテキスト・伝統の体系的可視化

### 1.4 日常化の条件

哲学者が計算ツールを日常的に使うようになるための条件：

> **研究者が日常的に抱く問いに対して、計算なしでは到達できない回答を、低い障壁で返す**

日常的な問い：
- 「この概念は他にどこで、どのように使われているか」（→ 概念的BLAST）
- 「この議論は既に誰かがしているか」（→ 哲学的SciFinder）
- 「この解釈は、他の解釈とどう異なるか」（→ 解釈布置図）
- 「この概念の意味はどう変遷してきたか」（→ 概念系譜追跡）

---

## 2. 設計原理

### 2.1 Bioconductor に学ぶ成功パターン

Bioconductorの成功要因は解析ツールではなく**データ基盤**にある：

```
解析ツール（DESeq2, edgeR）         ← 注目されるが上層
─────────────────────────────
SummarizedExperiment / GRanges       ← 成功の本質
─────────────────────────────
AnnotationHub / ExperimentHub        ← なければ何も動かない
─────────────────────────────
BiocManager / BBS (build system)     ← 品質保証
```

本エコシステムもこの構造を踏襲するが、哲学固有の課題（解釈の多重性）に対応する。

### 2.2 設計原則

| 原則 | 内容 |
|------|------|
| **二言語対等** | R版とPython版は同格。JSON Schemaで型定義を共有 |
| **ファサードパターン** | 研究者は philworkbench の約15の動詞だけで全機能にアクセス |
| **プラガブルバックエンド** | 埋め込みモデル・グラフDB・ストレージを交換可能に |
| **解釈の多重性** | 同一テキストに対する複数解釈を第一級オブジェクトとして扱う |
| **来歴追跡** | すべての計算結果に再現性情報を付与 |
| **段階的依存** | 重い依存（torch, neo4j）はオプショナル |
| **日常化優先** | 基盤を完璧にする前に、使えるインターフェースを提供 |

---

## 3. エコシステム全体構造

### 3.1 層構造

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 7: ワークフロー層    philworkbench (R) / philbench (Py)
           読む → 注釈 → 探索 → 比較 → 可視化 → 執筆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 6: 専門分析層        philmap / philtext / philgraph
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 5: コアデータ構造層  PhilCorpus / ConceptSpans / PhilCollection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 4: 定量化エンジン層  philengine
           多モデル対応埋め込み + 語彙/構造/間テキスト特徴量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 3: アノテーション層  phil.concepts.db / phil.traditions.db
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 2: リポジトリ層      PhilCorpusHub / PhilAnnotationHub
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Layer 1: 計算バックエンド  Python: sentence-transformers / spaCy /
           (API経由)        rdflib / Neo4j / FastAPI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.2 Bioconductor対応表

```
Bioconductor                  Phil Ecosystem             役割
────────────────              ──────────────             ────
SummarizedExperiment    ←→    PhilCorpus                 コアデータコンテナ
GRanges / IRanges       ←→    ConceptSpans               テキスト上の概念位置
MultiAssayExperiment    ←→    PhilCollection             複数コーパスの統合
org.Hs.eg.db            ←→    phil.concepts.db           概念アノテーションDB
TxDb.*                  ←→    phil.traditions.db          伝統構造DB
GO.db                   ←→    phil.ontology.db           哲学オントロジー
BSgenome.*              ←→    phil.texts.*               正典テキストパッケージ
ExperimentHub           ←→    PhilCorpusHub              キュレーション済みコーパス
AnnotationHub           ←→    PhilAnnotationHub          アノテーションリソース
Rsubread/STAR           ←→    philengine                 生データ→定量値変換
featureCounts           ←→    philengine/quantifier      特徴量行列生成
tximeta                 ←→    phil_embed_corpus()        定量値→コンテナ格納
DESeq2                  ←→    philmap                    差次的解析（概念比較）
iSEE                    ←→    phil_dashboard()           インタラクティブ可視化
plyranges               ←→    phil_explore()             tidy的データ探索
GenomicFeatures         ←→    phil_lookup()              アノテーション横断参照
rtracklayer             ←→    phil_import/export         外部フォーマット変換
ComplexHeatmap          ←→    phil_concept_map()         高度な可視化
clusterProfiler         ←→    phil_compare()             エンリッチメント分析
```

---

## 4. リポジトリ構成

### 4.1 リポジトリ一覧

```
GitHub:
│
├── phil/                          ★ メインモノレポ（エコシステム本体）
│   ├── python/                       Python パッケージ群 (7個)
│   ├── r/                            R パッケージ群 (6個)
│   └── shared/                       言語共通リソース
│
├── phil-hub/                      ★ データリポジトリ基盤
├── phil-texts/                    ★ 正典テキストパッケージ群
├── phil-models/                   ★ 学習済みモデル（HuggingFace Hub連携）
│
├── openalex-philosophy-corpus-builder/  （既存：コーパス構築パイプライン）
└── phil-papers/                   論文リポジトリ群
```

### 4.2 メインモノレポ `phil/` の詳細構造

```
phil/
├── ARCHITECTURE.md              # 本文書
├── VALIDATION_PLAN.md           # 検証計画
├── LICENSE                      # MIT
├── Makefile                     # 一括ビルド・テスト
├── CLAUDE.md                    # 開発ガイド
│
├── python/                      # ===== Python パッケージ群 =====
│   │
│   ├── philcore/                # [Layer 5] コアデータモデル
│   │   ├── pyproject.toml
│   │   └── src/philcore/
│   │       ├── __init__.py
│   │       ├── models/          #   Concept, Argument, Thinker, Text, Tradition
│   │       │   ├── concept.py
│   │       │   ├── argument.py
│   │       │   ├── tradition.py
│   │       │   ├── thinker.py
│   │       │   ├── text.py
│   │       │   └── relation.py
│   │       ├── corpus.py        #   PhilCorpus (Python版データコンテナ)
│   │       ├── spans.py         #   ConceptSpans
│   │       ├── collection.py    #   PhilCollection
│   │       ├── ontology/        #   hierarchy, mapping, logic
│   │       ├── serialization/   #   RDF/JSON-LD/CIDOC-CRM
│   │       ├── registry.py
│   │       ├── namespaces.py
│   │       └── types.py
│   │
│   ├── philengine/              # [Layer 4] テキスト定量化エンジン
│   │   ├── pyproject.toml
│   │   └── src/philengine/
│   │       ├── __init__.py
│   │       ├── engine.py        #   統一API: PhilEngine class
│   │       ├── backend/         #   埋め込みバックエンド
│   │       │   ├── base.py      #     EmbeddingBackend Protocol
│   │       │   ├── sentence_transformers.py
│   │       │   ├── openai.py
│   │       │   ├── cohere.py
│   │       │   ├── huggingface.py
│   │       │   ├── local_llm.py #     vLLM / llama.cpp
│   │       │   └── cached.py    #     キャッシュラッパー
│   │       ├── quantifier/      #   非ベクトル的定量化
│   │       │   ├── base.py      #     Quantifier Protocol
│   │       │   ├── lexical.py   #     語彙・修辞特徴量
│   │       │   ├── structural.py#     論証構造特徴量
│   │       │   ├── intertextual.py    間テキスト特徴量
│   │       │   └── composite.py #     複合特徴量
│   │       ├── facet.py         #   ファセット埋め込み
│   │       ├── preprocessor.py  #   古典語前処理
│   │       ├── cache.py         #   埋め込みキャッシュ管理
│   │       └── registry.py      #   バックエンド登録・切り替え
│   │
│   ├── philmap/                 # [Layer 6] 概念整列・比較
│   │   ├── pyproject.toml
│   │   └── src/philmap/
│   │       ├── __init__.py
│   │       ├── alignment/       #   4整列手法
│   │       │   ├── semantic.py
│   │       │   ├── structural.py
│   │       │   ├── argumentative.py
│   │       │   └── hybrid.py
│   │       └── analysis/        #   分析ツール
│   │           ├── analogues.py
│   │           ├── diff.py
│   │           ├── bridge.py
│   │           └── genealogy.py
│   │
│   ├── philtext/                # [Layer 6] テキスト解析
│   │   ├── pyproject.toml
│   │   └── src/philtext/
│   │       ├── __init__.py
│   │       ├── argument/        #   論証抽出
│   │       ├── concept/         #   概念抽出・リンキング
│   │       ├── classify/        #   学派分類
│   │       ├── influence/       #   影響検出
│   │       ├── hermeneutic/     #   解釈追跡
│   │       ├── corpus/          #   コーパス管理・多言語処理
│   │       └── bridge/          #   応用哲学ブリッジ
│   │
│   ├── philgraph/               # [Layer 6] 知識グラフ
│   │   ├── pyproject.toml
│   │   └── src/philgraph/
│   │       ├── __init__.py
│   │       ├── schema.py
│   │       ├── graph.py         #   PhilGraph class
│   │       ├── backend/         #   NetworkX / Neo4j / RDFLib
│   │       ├── ingest/          #   PhilPapers/InPhO/Wikidata/CTP/Manual
│   │       ├── query/           #   グラフクエリAPI
│   │       ├── resolve.py       #   エンティティ解決
│   │       └── viz/             #   グラフ可視化
│   │
│   ├── philbench/               # [Layer 7] Python ワークベンチ
│   │   ├── pyproject.toml
│   │   └── src/philbench/
│   │       ├── __init__.py
│   │       ├── verbs.py         #   read/embed/compare/search/plot/annotate
│   │       ├── pipeline.py      #   メソッドチェーン・パイプライン
│   │       └── dashboard/       #   Streamlit/Gradio ダッシュボード
│   │
│   └── philapi/                 # [Layer 1] REST API サーバー
│       ├── pyproject.toml
│       └── src/philapi/
│           ├── __init__.py
│           ├── app.py           #   FastAPI アプリ
│           ├── routes/          #   エンドポイント定義
│           │   ├── embed.py     #     /embed
│           │   ├── search.py    #     /search
│           │   ├── compare.py   #     /compare
│           │   ├── annotate.py  #     /annotate
│           │   └── graph.py     #     /graph
│           └── schemas.py       #   APIスキーマ（shared/schemasから生成）
│
├── r/                           # ===== R パッケージ群 =====
│   │
│   ├── philcore/                # [Layer 5] コアデータ構造
│   │   ├── DESCRIPTION
│   │   ├── NAMESPACE
│   │   ├── R/
│   │   │   ├── PhilCorpus.R     #   S3: PhilCorpus class
│   │   │   ├── ConceptSpans.R   #   S3: ConceptSpans class
│   │   │   ├── PhilCollection.R #   S3: PhilCollection class
│   │   │   ├── accessors.R      #   layers(), textMetadata(), segmentData()
│   │   │   ├── subset.R         #   [.PhilCorpus, [.ConceptSpans
│   │   │   ├── io.R             #   read/write HDF5Phil, Parquet
│   │   │   ├── coerce.R         #   as.data.frame, as.PhilCorpus
│   │   │   ├── validate.R       #   データ検証
│   │   │   └── print.R          #   print/summary S3 methods
│   │   └── tests/testthat/
│   │
│   ├── philengine/              # [Layer 4] エンジンクライアント
│   │   ├── DESCRIPTION
│   │   ├── R/
│   │   │   ├── engine.R         #   phil_engine() コンストラクタ
│   │   │   ├── embed.R          #   phil_embed()
│   │   │   ├── quantify.R       #   phil_quantify()
│   │   │   ├── backends.R       #   バックエンド切り替え
│   │   │   ├── benchmark.R      #   phil_compare_backends()
│   │   │   └── cache.R          #   キャッシュ管理
│   │   └── tests/testthat/
│   │
│   ├── philmap/                 # [Layer 6] 概念整列
│   │   ├── DESCRIPTION
│   │   ├── R/
│   │   │   ├── align.R          #   phil_align()
│   │   │   ├── compare.R        #   phil_compare()
│   │   │   ├── search.R         #   phil_search()
│   │   │   └── plot.R           #   S3 plot methods
│   │   └── tests/testthat/
│   │
│   ├── philworkbench/           # [Layer 7] ★ 統合ワークベンチ
│   │   ├── DESCRIPTION
│   │   ├── R/
│   │   │   ├── read.R           #   phil_read()
│   │   │   ├── explore.R        #   phil_explore()
│   │   │   ├── compare.R        #   phil_compare() 高レベル
│   │   │   ├── annotate.R       #   phil_annotate(), phil_review()
│   │   │   ├── trace.R          #   phil_trace() 影響・系譜
│   │   │   ├── plot.R           #   phil_plot() S3 methods
│   │   │   ├── export.R         #   phil_to_latex(), phil_to_bibtex()
│   │   │   ├── dashboard.R      #   phil_dashboard() Shiny
│   │   │   ├── notebook.R       #   Quarto 統合ヘルパー
│   │   │   ├── config.R         #   phil_config()
│   │   │   └── session.R        #   phil_session() 再現性情報
│   │   ├── inst/
│   │   │   └── shiny/           #   Shiny app files
│   │   └── tests/testthat/
│   │
│   ├── phil.concepts.db/        # [Layer 3] 概念アノテーションDB
│   │   ├── DESCRIPTION
│   │   ├── R/
│   │   │   ├── db.R             #   select(), keys(), columns()
│   │   │   ├── build.R          #   DB構築
│   │   │   └── search.R         #   概念検索
│   │   └── inst/extdata/        #   SQLite DB
│   │
│   └── phil.traditions.db/      # [Layer 3] 伝統構造DB
│       ├── DESCRIPTION
│       ├── R/
│       │   ├── db.R             #   select(), keys()
│       │   └── tree.R           #   tradition_tree()
│       └── inst/extdata/        #   SQLite DB
│
├── shared/                      # ===== 言語共通リソース =====
│   │
│   ├── schemas/                 #   JSON Schema（R/Py間の型定義共有）
│   │   ├── concept.schema.json
│   │   ├── argument.schema.json
│   │   ├── phil_corpus.schema.json
│   │   ├── concept_spans.schema.json
│   │   ├── alignment_result.schema.json
│   │   └── api/                 #   OpenAPI仕様
│   │       └── openapi.yaml
│   │
│   ├── ontology/                #   哲学オントロジー定義
│   │   ├── phil-ontology.owl
│   │   ├── phil-ontology.skos.ttl
│   │   └── mappings/
│   │       ├── inpho-mapping.ttl
│   │       ├── wikidata-mapping.json
│   │       └── cidoc-crm-mapping.ttl
│   │
│   ├── benchmarks/              #   評価用データセット
│   │   ├── concept_pairs_v1.yaml
│   │   ├── concept_pairs_v2.yaml
│   │   └── ground_truth/
│   │       ├── cross_tradition_mappings.yaml
│   │       └── school_classification.yaml
│   │
│   ├── config/                  #   共通設定
│   │   ├── traditions.yaml      #     伝統定義マスタ
│   │   ├── languages.yaml       #     対応言語定義
│   │   └── models.yaml          #     推奨モデル一覧
│   │
│   └── data/                    #   小規模参照データ
│       ├── school_taxonomy.yaml
│       └── logic_families.yaml
│
├── scripts/                     # ===== ビルド・ファインチューニング =====
│   ├── finetune_alignment.py
│   ├── build_concept_db.R
│   ├── build_tradition_db.R
│   ├── generate_api_schemas.py  #   shared/schemas → philapi/schemas.py
│   └── validate_all.sh
│
├── docker/                      # ===== Docker =====
│   ├── Dockerfile.api           #   philapi サーバー
│   ├── Dockerfile.full          #   全Python環境
│   └── docker-compose.yml       #   API + Neo4j + Redis(キャッシュ)
│
└── tests/                       # ===== 統合テスト =====
    ├── integration/
    │   ├── test_r_py_roundtrip.R   # R→API→Python→R のデータ往復
    │   ├── test_pipeline.py        # E2Eパイプライン
    │   └── test_schema_sync.py     # JSON Schema↔実装の一致
    └── benchmarks/
        └── test_concept_pairs.py   # ベンチマーク評価
```

### 4.3 衛星リポジトリ

#### `phil-hub/` — データリポジトリ基盤

```
phil-hub/
├── python/
│   └── philhub/
│       ├── corpus_hub.py        # PhilCorpusHub: コーパスの登録・取得
│       ├── annotation_hub.py    # PhilAnnotationHub: アノテーションの登録・取得
│       ├── registry.py          # 利用可能データセットのレジストリ
│       └── storage/             # S3/GCS/ローカル対応
│           ├── local.py
│           └── cloud.py
│
├── r/
│   ├── PhilCorpusHub/           # ExperimentHub対応 R パッケージ
│   │   ├── DESCRIPTION
│   │   └── R/
│   │       ├── hub.R            #   PhilCorpusHub(), query(), download()
│   │       └── cache.R          #   ローカルキャッシュ管理
│   └── PhilAnnotationHub/       # AnnotationHub対応 R パッケージ
│       ├── DESCRIPTION
│       └── R/
│           └── hub.R
│
└── registry/                    # データセット定義（YAML）
    ├── corpora/
    │   ├── watsuji_rinrigaku_v1.yaml
    │   ├── heidegger_sz_v1.yaml
    │   ├── analects_v1.yaml
    │   └── ...
    └── annotations/
        ├── inpho_ontology_v4.yaml
        ├── philmap_e5_alignments_v2.yaml
        └── ...
```

#### `phil-texts/` — 正典テキストパッケージ群

```
phil-texts/
├── phil.texts.Kant.KrV/         # BSgenome方式：各テキストが独立パッケージ
│   ├── DESCRIPTION
│   ├── inst/extdata/
│   │   ├── original_de.txt
│   │   ├── translation_ja.txt
│   │   └── translation_en.txt
│   └── R/
│       └── data.R               #   phil_text() accessor
│
├── phil.texts.Watsuji.Rinrigaku/
├── phil.texts.Nagarjuna.MMK/
├── phil.texts.Heidegger.SZ/
├── phil.texts.Analects/
├── phil.texts.Zhuangzi/
└── ...
```

#### `phil-models/` — 学習済みモデル

```
phil-models/
├── philmap-e5-finetuned-v1/     # Git LFS or HuggingFace Hub
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer/
├── philmap-e5-finetuned-v2/
├── training/
│   ├── logs/
│   └── configs/
│       ├── v1_config.yaml
│       └── v2_config.yaml
└── MODEL_CARD.md
```

---

## 5. パッケージ仕様

### 5.1 コアデータ構造層: philcore

**目的**: 全パッケージが共有するデータモデルとデータコンテナの定義

#### Python版

既存の実装を継承（Pydanticモデル群は70%実装済み）：

| モデル | 説明 | 状態 |
|--------|------|------|
| `Concept` | 哲学的概念。多言語ラベル、伝統帰属、形式的性質 | ✅ 実装済み |
| `Argument` | 哲学的論証。前提、結論、論理形式、四句分別対応 | ✅ 実装済み |
| `Tradition` | 哲学的伝統/学派。階層的、時間的、地理的 | ✅ 実装済み |
| `Thinker` | 哲学者。伝記データ、概念的貢献、影響関係 | ✅ 実装済み |
| `Text` | 哲学テキスト/著作。パッセージ、著者帰属、正典参照 | ✅ 実装済み |
| `PhilCorpus` | データコンテナ（SE対応）。層・メタデータ・アノテーション | 🆕 新規 |
| `ConceptSpans` | テキスト上の概念位置（GRanges対応） | 🆕 新規 |
| `PhilCollection` | 複数PhilCorpusの統合（MAE対応） | 🆕 新規 |

非古典論理サポート（第一級）：
- **四句分別（Catuskoti）**: 4値論理（T, F, Both, Neither）+ 龍樹の全否定
- **場所論理（Basho）**: 3段階の場所階層（有の場所 ⊂ 相対無 ⊂ 絶対無）
- **矛盾許容論理**: Belnapの4値意味論
- **弁証法論理**: テーゼ-アンチテーゼ-ジンテーゼ + Aufhebung

直列化: OWL/RDF (rdflib), JSON-LD, CIDOC-CRM, Wikidata bridging

#### R版

philo-bridgeの実装を継承・拡張（philo.core, philo.store, philo.corpus, philo.store.arrowから統合）：

```r
# PhilCorpus: SummarizedExperiment対応データコンテナ
corpus <- PhilCorpus(
  layers = list(
    original  = text_matrix,     # 原文（トークン化済み）
    embedding = dense_matrix     # 文埋め込みベクトル
  ),
  segmentData = DataFrame(       # 行メタデータ: テキスト区間
    segment_id, text_id, position, section, segment_type
  ),
  textMetadata = DataFrame(      # 列メタデータ: テキスト情報
    text_id, title, author, year, tradition, language, edition
  ),
  conceptSpans = ConceptSpans(   # 概念アノテーション (GRanges対応)
    text_id, start, end, concept_id, confidence,
    annotator, interpretation_id
  ),
  provenance = list(             # 来歴情報
    source, built_with, annotation_method
  )
)

# SE的操作
corpus[i, j]                     # サブセット
layers(corpus, "embedding")      # 層アクセス
segmentData(corpus)              # 行メタデータ
textMetadata(corpus)             # 列メタデータ
conceptSpans(corpus)             # アノテーション
```

### 5.2 定量化エンジン層: philengine

**目的**: テキストを様々な方法で定量的表現に変換する統一エンジン

#### 現状の問題

現在、埋め込みモデルが4箇所に分散している：

```
philmap/embedding/embedder.py     → multilingual-e5-large-instruct
philtext/corpus/aligner.py        → paraphrase-multilingual-MiniLM-L12-v2
philtext/influence/detector.py    → paraphrase-multilingual-mpnet-base-v2
philtext/classify/school.py       → multilingual-e5-base + mDeBERTa-v3
philo.embed (R)                   → TF-IDF + SBERT
```

philengineはこれらを統一する。

#### プラガブルバックエンド

```python
class EmbeddingBackend(Protocol):
    """すべての埋め込みバックエンドが満たすインターフェース"""
    def encode(self, texts: list[str], **kwargs) -> np.ndarray: ...
    def dim(self) -> int: ...
    def max_tokens(self) -> int: ...
    def metadata(self) -> BackendMetadata: ...
```

| バックエンド | 実装 | 用途 |
|-------------|------|------|
| `SentenceTransformersBackend` | sentence-transformers | ローカル推論（主力） |
| `OpenAIBackend` | OpenAI API | text-embedding-3-large |
| `CohereBackend` | Cohere API | embed-multilingual-v3 |
| `HuggingFaceBackend` | HF Inference API | リモート推論 |
| `LocalLLMBackend` | vLLM / llama.cpp | 自前サーバー |
| `CachedBackend` | ラッパー | 任意のバックエンドにキャッシュ追加 |

#### テキスト定量化の4軸

| 軸 | 内容 | 出力 |
|----|------|------|
| **意味的ベクトル化** | embedding（密な意味表現） | float matrix [n_segments × dim] |
| **語彙・修辞的特徴量** | TTR, 論証マーカー頻度, 引用密度, 専門語比率 | float matrix [n_segments × n_features] |
| **構造的特徴量** | 論証の深さ, 前提数, 反論構造, 弁証法パターン | float matrix [n_segments × n_features] |
| **間テキスト的特徴量** | 類似度分布, 新規性スコア, 伝統内位置 | float matrix [n_segments × n_features] |

#### 哲学固有の前処理

```python
preprocessor = PhilPreprocessor(
    classical_greek = "cltk_normalize",
    classical_chinese = "kanbun_segment",
    sanskrit = "indic_transliterate",     # デーヴァナーガリー → IAST
    middle_japanese = "nkf_normalize",
    classical_latin = "cltk_lemmatize"
)
```

#### ファセット埋め込み（philmapから移動）

概念を3つのファセットで別々にベクトル化：
1. **Definition**: 概念の意味
2. **Usage**: 論証・テキストでの使われ方
3. **Relational**: 伝統内オントロジーにおける位置

重み付き結合で複合ベクトルを生成。

#### R版インターフェース

```r
engine <- phil_engine(backend = "sentence-transformers",
                      model = "philmap-e5-finetuned-v2")

# 埋め込み
embeddings <- phil_embed(engine, texts)

# 特徴量
features <- phil_quantify(corpus, type = c("lexical", "structural"))

# バックエンド比較
phil_compare_backends(engines, benchmark, metrics)
```

### 5.3 概念整列層: philmap

**目的**: 伝統・言語を超えた哲学的概念の計算的比較・整列

#### 整列手法

| 手法 | アプローチ | 捕捉するもの |
|------|-----------|-------------|
| `SemanticAlignment` | 多言語embedding余弦類似度 | 意味の重なり |
| `StructuralAlignment` | グラフベース（次数、中心性、モチーフ） | 位置的類似性 |
| `ArgumentativeAlignment` | 共有論証役割 | 機能的類似性 |
| `HybridAlignment` | 3手法の重み付き結合 (0.4/0.35/0.25) | 多次元的類似性 |

#### 分析ツール

- `find_analogues(concept, target_tradition)` — 他伝統の類似概念検索
- `concept_diff(concept_a, concept_b)` — 共通点・相違点の構造化比較
- `tradition_bridge(trad_a, trad_b)` — 伝統間の概念対応関係一覧
- `concept_genealogy(concept)` — 時間的・伝統間の概念変遷追跡

#### 学習済みモデル

| モデル | ベース | 学習データ | Spearman |
|--------|--------|-----------|----------|
| philmap-e5-v1 | multilingual-e5-base | 94ペア | 0.845 |
| philmap-e5-v2 | multilingual-e5-base | 138ペア | 0.976 |

### 5.4 テキスト解析層: philtext

**目的**: 哲学テキストへのドメイン特化型NLP

7つのコンポーネント：

| コンポーネント | 機能 | 主要クラス |
|---------------|------|-----------|
| **argument** | 論証抽出（ルールベース + LLM + ハイブリッド） | `ArgumentExtractor` |
| **concept** | 概念抽出・リンキング（辞書 + embedding） | `ConceptExtractor` |
| **classify** | 学派分類（40+学派、prototype/NLI） | `SchoolClassifier` |
| **influence** | 影響検出（dense retrieval + reranking） | `InfluenceDetector` |
| **hermeneutic** | 解釈追跡・比較・衝突検出 | `InterpretationTracker` |
| **corpus** | コーパス管理・多言語処理 | `CorpusBuilder`, `TextAligner` |
| **bridge** | 実践的応用への橋渡し | `PracticalMapper` |

多言語トークナイザ: spaCy (en/de/fr), SudachiPy (ja), jieba (zh), CLTK (la/grc/sa)

### 5.5 知識グラフ層: philgraph

**目的**: 全伝統横断の哲学知識グラフの構築・クエリ

- **8ノード型**: Concept, Thinker, Text, Tradition, Argument, Era, Institution, Language
- **15エッジ型**: influences, opposes, extends, reinterprets, translates_to, etc.
- **3バックエンド**: NetworkX (プロトタイプ), Neo4j (本番), RDFLib (セマンティックWeb)
- **5データインジェスタ**: PhilPapers, InPhO, Wikidata, CTP, Manual YAML

### 5.6 統合ワークベンチ層: philworkbench

**目的**: 全層を統一的に操作する動詞体系（ファサードパターン）

#### 設計思想

研究者は philworkbench の約15の動詞だけで全機能にアクセスできる。
内部で適切な層のAPIを呼び分ける。

#### 動詞体系

```r
# ━━━ 読む ━━━
phil_read()            # テキスト読み込み (PhilCorpusHub → PhilCorpus)
phil_segment()         # テキスト区間分割
phil_lookup()          # 概念・思想家・テキスト検索 (phil.concepts.db)

# ━━━ 定量化する ━━━
phil_embed()           # テキスト埋め込み (philengine)
phil_quantify()        # 非ベクトル特徴量 (philengine)

# ━━━ 比較する ━━━
phil_compare()         # 概念・テキスト・伝統の比較 (philmap)
phil_search()          # 類似テキスト・概念の検索
phil_align()           # 概念整列 (semantic/structural/hybrid)
phil_trace()           # 影響関係・系譜追跡 (philtext)

# ━━━ 注釈する ━━━
phil_annotate()        # 自動アノテーション
phil_review()          # 人間レビュー (インタラクティブ)
phil_tag()             # 概念タグの手動付与

# ━━━ 可視化する ━━━
phil_plot()            # 汎用可視化 (S3型別分岐)
phil_dashboard()       # Shinyダッシュボード

# ━━━ 出力する ━━━
phil_to_latex()        # LaTeX表・図の出力
phil_to_bibtex()       # BibTeX出力
phil_export()          # JSON-LD / RDF / CSV

# ━━━ 管理する ━━━
phil_save()            # 分析結果の保存
phil_session()         # 再現性情報
phil_config()          # エンジン・バックエンドの設定
```

#### 内部ディスパッチ例

```
phil_compare("間柄", "Mitsein")
    │
    ├── phil.concepts.db → 概念ID解決 (phil:C00142, phil:C00089)
    ├── PhilCorpusHub → 関連テキスト取得
    ├── philengine → 埋め込み計算（キャッシュ確認）
    ├── philmap → 整列実行 (hybrid)
    └── PhilComparison オブジェクトとして返却
          ├── print()  → テキスト要約
          ├── plot()   → 概念マップ
          ├── summary() → 統計量
          └── phil_to_latex() → 論文用表
```

#### パイプラインワークフロー

```r
# tidyverse的パイプで分析の意図が読めるコード
phil_read("watsuji_rinrigaku") |>
  phil_embed(model = "philmap-e5-v2") |>
  phil_search(concept = "間柄", traditions = "all", top_k = 30) |>
  phil_plot(type = "tradition_map", color_by = "tradition")
```

#### S3メソッドによる型ベース可視化

| オブジェクト型 | デフォルト可視化 | 利用可能な type |
|---------------|----------------|----------------|
| `PhilComparison` | 概念比較図 | radar, network, text_diff |
| `PhilCorpus` | コーパス概観 | concept_heatmap, timeline, structure |
| `PhilExploration` | 探索マップ | network, tradition_map, timeline |
| `ConceptSpans` | アノテーションオーバーレイ | density, cooccurrence |
| `PhilGenealogy` | 系譜図 | tree, sankey, timeline |

#### Shinyダッシュボード (phil_dashboard)

```
┌──────────────────────────────────────────────────────┐
│  Phil Dashboard                                      │
├────────┬─────────────────────────────────────────────┤
│        │  [テキストビューア]                           │
│ ☐ 読む │  概念アノテーションがオーバーレイ表示          │
│ ☐ 注釈 │  選択概念の類似概念がサイドパネルに           │
│ ☐ 探索 │                                             │
│ ☐ 比較 │  ──────────────────────────────             │
│ ☐ 可視 │  [可視化パネル]                              │
│ ☐ 出力 │  概念マップ / タイムライン / ヒートマップ      │
│        │  タブ切り替え                                │
│ ────── │                                             │
│ Config │  [分析パネル]                                │
│ Engine │  パラメータ設定、モデル選択、                 │
│ Model  │  結果のエクスポート                           │
└────────┴─────────────────────────────────────────────┘
```

### 5.7 API層: philapi

**目的**: R版とPython版を繋ぐ言語非依存のREST API

```
R パッケージ群                Python 計算層
┌──────────────┐            ┌───────────────────┐
│ philcore (R)  │            │ philcore (Py)     │
│ philengine(R) │──HTTP──→   │ philengine (Py)   │
│ philmap (R)   │            │ philmap (Py)      │
│ philworkbench │            │ philtext (Py)     │
└──────────────┘            │ philgraph (Py)    │
                            │ philapi (FastAPI) │
                            └───────────────────┘
```

主要エンドポイント：

| エンドポイント | メソッド | 機能 |
|---------------|---------|------|
| `/embed` | POST | テキスト埋め込み |
| `/search` | POST | 概念検索 |
| `/compare` | POST | 概念比較 |
| `/align` | POST | 概念整列 |
| `/annotate` | POST | 自動アノテーション |
| `/graph/query` | POST | 知識グラフクエリ |
| `/models` | GET | 利用可能モデル一覧 |
| `/health` | GET | ヘルスチェック |

### 5.8 アノテーションデータベース

#### phil.concepts.db（org.Hs.eg.db 対応）

```r
select(phil.concepts.db,
  keys = "autonomy",
  keytype = "LABEL_EN",
  columns = c("CONCEPT_ID", "LABEL_JA", "LABEL_DE",
              "TRADITION", "RELATED_CONCEPTS")
)
#>   CONCEPT_ID  LABEL_EN   LABEL_JA  LABEL_DE    TRADITION
#> 1 phil:C00001 autonomy   自律      Autonomie   kantian_ethics
```

列: CONCEPT_ID, LABEL_EN, LABEL_JA, LABEL_DE, LABEL_ZH, LABEL_SA,
DEFINITION_EN, TRADITION, ERA, RELATED_CONCEPTS, WIKIDATA_QID, INPHO_ID

#### phil.traditions.db（TxDb.* 対応）

```r
tradition_tree("east_asian")
#> east_asian
#> ├── confucianism
#> │   ├── classical_confucianism (-500 ~ -200)
#> │   ├── neo_confucianism (1000 ~ 1600)
#> │   └── new_confucianism (1920 ~ present)
#> ├── buddhism_ea
#> │   ├── zen (1200 ~ present)
#> │   └── pure_land (1100 ~ present)
#> └── daoism
```

### 5.9 データリポジトリ

#### PhilCorpusHub（ExperimentHub 対応）

```r
hub <- PhilCorpusHub()
query(hub, tradition = "phenomenology", language = "de")
corpus <- hub[["PCH002"]]  # ダウンロード → PhilCorpus
```

#### PhilAnnotationHub（AnnotationHub 対応）

```r
ahub <- PhilAnnotationHub()
ontology <- ahub[["PAH001"]]  # InPhO ontology v4.2
```

---

## 6. PhilCorpus データコンテナ仕様

### 6.1 設計思想

SummarizedExperimentの「行（特徴量）× 列（サンプル）× 層（アッセイ）」構造を
哲学データに対応させるが、**解釈の多重性**という哲学固有の次元を追加する。

### 6.2 構造定義

```
PhilCorpus
├── layers: dict[str, matrix]
│   ├── "original"    → テキスト行列 [n_segments × n_texts]
│   ├── "translation" → 翻訳テキスト行列
│   ├── "embedding"   → 密ベクトル行列 [n_segments × dim]
│   └── "features"    → 特徴量行列 [n_segments × n_features]
│
├── segmentData: DataFrame [n_segments rows]
│   ├── segment_id    : character  # 区間識別子
│   ├── text_id       : character  # テキスト識別子
│   ├── position      : integer    # テキスト内位置
│   ├── section       : character  # 章・節
│   └── segment_type  : character  # paragraph / sentence / argument
│
├── textMetadata: DataFrame [n_texts rows]
│   ├── text_id       : character  # テキスト識別子
│   ├── title         : character
│   ├── author        : character
│   ├── year          : integer
│   ├── tradition     : character  # "german_idealism", "zen_buddhism"
│   ├── language      : character  # ISO 639-3
│   └── edition       : character
│
├── conceptSpans: ConceptSpans
│   ├── text_id       : character
│   ├── start         : integer    # 文字位置
│   ├── end           : integer
│   ├── concept_id    : character  # phil.concepts.db 参照
│   ├── confidence    : numeric    # 0-1
│   ├── annotator     : character  # "human:dreyfus" or "model:philmap-e5-v2"
│   └── interpretation_id : character  # 解釈レイヤー
│
└── provenance: list
    ├── source         : character  # "PhilCorpusHub::watsuji_v1"
    ├── built_with     : character  # "philcore 0.1.0"
    └── annotation_method : character
```

### 6.3 Bioconductor との構造的対応

```
SummarizedExperiment          PhilCorpus
────────────────────          ──────────
assays (matrix層)       ←→    layers (original/embedding/features)
rowData (遺伝子情報)     ←→    segmentData (テキスト区間メタデータ)
colData (サンプル情報)   ←→    textMetadata (テキストメタデータ)
rowRanges (ゲノム座標)   ←→    conceptSpans (概念出現位置)
metadata (実験情報)      ←→    provenance (来歴情報)
```

### 6.4 SummarizedExperiment にない次元：解釈の多重性

ゲノムデータには基本的に一つの参照配列がある。
哲学テキストには**同一テキストに対する複数の正当な解釈**がある。

```r
# 解釈レイヤーの切り替え
interpretations(corpus)
#>   interp_id  annotator    school            year
#> 1 I001       dreyfus      pragmatist        1991
#> 2 I002       richardson   phenomenological  1963
#> 3 I003       philmap-e5   computational     2026

# 解釈ごとに異なる概念アノテーション
conceptSpans(corpus, interpretation = "I001")  # Dreyfus的読み
conceptSpans(corpus, interpretation = "I002")  # Richardson的読み
```

### 6.5 永続化フォーマット

| フォーマット | 用途 | R | Python |
|-------------|------|---|--------|
| HDF5Phil (.h5phil) | 大規模コーパス、ランダムアクセス | rhdf5 | h5py |
| Parquet | 列指向分析、Arrow互換 | arrow | pyarrow |
| JSON-LD | セマンティックWeb公開 | jsonlite | pyld |

### 6.6 PhilCollection（MultiAssayExperiment 対応）

複数のPhilCorpusを統合し、横断分析を可能にする：

```r
collection <- PhilCollection(
  watsuji   = phil_load("watsuji_rinrigaku"),
  heidegger = phil_load("heidegger_sein_und_zeit"),
  ubuntu    = phil_load("metz_ubuntu_ethics")
)

# 横断検索
phil_search(collection, concept = "intersubjectivity", top_k = 50)
```

---

## 7. R/Python 二言語戦略

### 7.1 アーキテクチャ

```
┌───────────────────────────────────────────────────┐
│               ユーザー層（二言語）                   │
│  ┌──────────────────┐    ┌─────────────────────┐  │
│  │  R パッケージ群    │    │  Python パッケージ群  │  │
│  │  philworkbench    │    │  philbench          │  │
│  │  philcore (R)     │    │  philcore (Py)      │  │
│  │  philengine (R)   │    │  philengine (Py)    │  │
│  │  philmap (R)      │    │  philmap (Py)       │  │
│  │  S3 classes       │    │  Pydantic/dataclass │  │
│  │  tidyverse/ggplot2│    │  pandas/matplotlib  │  │
│  └────────┬─────────┘    └──────────┬──────────┘  │
│           │                         │              │
├───────────┴─────────────────────────┴──────────────┤
│              API層（言語非依存）                      │
│  ┌──────────────────────────────────────────────┐  │
│  │   philapi (FastAPI) / REST + JSON            │  │
│  │   共通スキーマ: shared/schemas/*.schema.json  │  │
│  └──────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────┤
│              計算層（Python）                        │
│  philengine backends / sentence-transformers /     │
│  spaCy / rdflib / Neo4j                           │
└────────────────────────────────────────────────────┘
```

### 7.2 各言語の役割

| 側面 | R版の役割 | Python版の役割 |
|------|----------|---------------|
| データ構造 | PhilCorpus (S3), アクセサ, サブセット | PhilCorpus (dataclass), Pydanticモデル |
| 計算 | API経由で委譲 | 埋め込み計算、NLP処理の実行 |
| 可視化 | ggplot2, Shiny (本格的) | matplotlib, Streamlit (軽量) |
| 統計分析 | tidyverse, 検定, 回帰 | pandas, scipy |
| ワークフロー | パイプ (`\|>`) + S3 methods | メソッドチェーン |
| 対象ユーザー | DH研究者, 統計寄り | ML/NLP研究者, 開発者 |

### 7.3 型の同期: JSON Schema

`shared/schemas/` に型定義を配置し、R/Python両方から参照：

```json
// shared/schemas/concept.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Concept",
  "type": "object",
  "properties": {
    "concept_id": { "type": "string", "pattern": "^phil:C[0-9]+$" },
    "labels": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "text": { "type": "string" },
          "language": { "type": "string" },
          "script": { "type": "string" },
          "is_primary": { "type": "boolean" }
        }
      }
    },
    "tradition": { "type": "string" },
    "era": { "type": "string" }
  }
}
```

### 7.4 PhysioExperiment エコシステムとの構造的対応

```
PhysioExperiment             Phil Ecosystem
─────────────────            ──────────────
PhysioCore (R)         ←→    philcore (R)      コアデータ構造
PhysioIO (R)           ←→    PhilCorpusHub     データ入出力
PhysioEMG (R)          ←→    philmap (R)       ドメイン特化解析
PhysioMSKNet (R)       ←→    philgraph (R)     ネットワーク解析
PhysioMoCap (R)        ←→    philtext (R)      信号処理（テキスト処理）
PhysioOpenSim (R)      ←→    philapi           外部エンジン接続
```

S3クラス設計、`print`/`plot`/`summary`メソッド、tidyverse互換性は
PhysioExperimentで確立したパターンをそのまま転用。

---

## 8. 既存リポジトリからの移行計画

### 8.1 移行マップ

```
現在のリポジトリ                      移行先
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

digital-philosophy-ecosystem/
  philcore/                       →  phil/python/philcore/       (モデル継承)
  philmap/                        →  phil/python/philmap/        (整列手法)
    embedding/embedder.py         →  phil/python/philengine/     (エンジンとして分離)
  philtext/                       →  phil/python/philtext/       (テキスト解析)
  philgraph/                      →  phil/python/philgraph/      (知識グラフ)
  models/                         →  phil-models/                (Git LFS)
  data/                           →  phil-hub/registry/          (データ定義)
  scripts/                        →  phil/scripts/
  ARCHITECTURE.md                 →  phil/ARCHITECTURE.md        (本文書)
  VALIDATION_PLAN.md              →  phil/VALIDATION_PLAN.md

philo-bridge/ (19 R packages)
  philo.core/                     →  phil/r/philcore/            (S3化、PhilCorpus追加)
  philo.embed/                    →  phil/r/philengine/          (バックエンド統一)
  philo.corpus/                   →  phil/r/philcore/            (PhilCorpusに統合)
  philo.store/ + store.arrow/     →  phil/r/philcore/io.R        (IO統合)
  philo.bridge/                   →  phil/r/philmap/             (概念整列)
  philo.text/                     →  phil/r/philcore/            (テキスト処理基盤)
  philo.index/                    →  phil/r/philengine/          (ベクトルインデックス)
  philo.retrieve/                 →  phil/r/philmap/             (検索)
  philo.lens/                     →  phil/r/philworkbench/       (可視化)
  philo.ui/                       →  phil/r/philworkbench/       (Shiny dashboard)
  philo.workflow/                 →  phil/r/philworkbench/       (ワークフロー)
  philo.openalex/                 →  phil-hub/r/ or 存続         (データ取得)
  philo.crossref/ + philo.pubmed/ →  phil-hub/r/                 (外部データ取得)
  philo.api/                      →  phil/python/philapi/        (Python化、FastAPI)
  philo.config/                   →  phil/r/philcore/config.R
  philo.audit/                    →  phil/r/philcore/provenance.R
  philobridge/ (orchestrator)     →  phil/r/philworkbench/       (ファサード)

openalex-philosophy-corpus-builder/
  src/ scripts/                   →  存続（コーパス構築パイプライン）
  paper/                          →  phil-papers/ に分離
```

### 8.2 パッケージ数の変遷

```
現状:  4 (Python) + 19 (R) + 1 (corpus-builder) = 24パッケージ / 3リポジトリ
提案:  7 (Python) + 6 (R) + Hub 3 + 共通 = ~16パッケージ / 5リポジトリ

Python: philcore, philengine, philmap, philtext, philgraph, philbench, philapi  (7)
R:      philcore, philengine, philmap, philworkbench, phil.concepts.db,
        phil.traditions.db  (6)
Hub:    PhilCorpusHub (R+Py), PhilAnnotationHub (R+Py)  (2×2)
```

### 8.3 philo-bridge 統合の詳細

philo-bridgeの19パッケージは高品質（テスト25件、10,686行）であり、
コードを破棄するのではなく、新しい構造に**再配置**する：

| philo-bridge 機能 | 実装品質 | 移行先 | 移行方法 |
|-------------------|---------|--------|---------|
| スキーマ検証 | ✅ 完成 | philcore/validate.R | ほぼそのまま |
| DuckDB CRUD | ✅ 完成 | philcore/io.R | アダプタ化 |
| Parquet I/O | ✅ 完成 | philcore/io.R | そのまま |
| TF-IDF/SBERT | ✅ 完成 | philengine/ | バックエンド化 |
| HNSWインデックス | ✅ 完成 | philengine/cache.R | 統合 |
| 検索・比較 | ✅ 完成 | philmap/ | 拡張 |
| マッピング提案 | ✅ 完成 | philmap/ | 統合 |
| 人間レビュー | ✅ 完成 | philworkbench/annotate.R | UI統合 |
| 哲学レンズ | ✅ 完成 | philworkbench/ | 機能追加 |
| Shiny UI | ✅ 完成 | philworkbench/dashboard.R | 拡張 |
| ワークフロー | ✅ 完成 | philworkbench/ | パイプライン化 |
| 監査ログ | ✅ 完成 | philcore/provenance.R | 来歴追跡統合 |
| OpenAlex連携 | ✅ 完成 | phil-hub/ or 存続 | 再配置 |
| PubMed/Crossref | ✅ 完成 | phil-hub/ | 再配置 |
| Plumber API | ✅ 完成 | philapi (Python FastAPI) | 再実装 |

---

## 9. 依存関係グラフ

### 9.1 R パッケージ依存

```
philworkbench
├── philmap
│     └── philengine
│           └── philcore
├── phil.concepts.db
│     └── (SQLite, DBI)
├── phil.traditions.db
│     └── (SQLite, DBI)
└── PhilCorpusHub (phil-hub)
      └── (httr2, arrow)

外部依存:
  philcore:      S3 classes, data.table or tibble, jsonlite
  philengine:    httr2 (API client), arrow (Parquet), RcppHNSW (index)
  philmap:       (philengineに委譲、R内は軽量)
  philworkbench: shiny, ggplot2, ggraph, DT, quarto, knitr
  phil.*.db:     DBI, RSQLite
```

### 9.2 Python パッケージ依存

```
philbench
├── philmap
│     └── philengine
│           └── philcore
├── philtext
│     └── philengine
├── philgraph
│     └── philcore
└── philapi (FastAPI)

外部依存:
  philcore:    pydantic>=2.6, rdflib>=7.0, networkx>=3.2
  philengine:  numpy>=1.24, scipy>=1.10
    Optional:  sentence-transformers>=3.0, torch>=2.0, openai, cohere
  philmap:     (philengineに委譲)
  philtext:    spacy>=3.7, httpx>=0.27
    Optional:  sudachipy, jieba, cltk, litellm
  philgraph:   pyyaml>=6.0, httpx>=0.27
    Optional:  neo4j>=5.0, pyvis>=0.3, rapidfuzz>=3.0
  philapi:     fastapi>=0.110, uvicorn>=0.29
  philbench:   (上記全て)
    Optional:  streamlit or gradio
```

### 9.3 言語間接続

```
R (philengine) ──HTTP──→ Python (philapi) ──→ philengine (Py)
R (philmap)    ──HTTP──→ Python (philapi) ──→ philmap (Py)
R (philcore)   ──JSON──→ shared/schemas   ←── philcore (Py)
```

---

## 10. 実装ロードマップ

### Phase 0: 基盤整備（〜2026年4月）

**目標**: モノレポ構築、既存コードの移行

| タスク | 成果物 | 依存 |
|--------|--------|------|
| phil/ モノレポ作成 | リポジトリ骨格 | なし |
| shared/schemas/ JSON Schema 定義 | 型定義共有基盤 | なし |
| Python philcore 移行 | Pydanticモデル群 | モノレポ |
| R philcore 構築（philo-bridge統合） | S3クラス + PhilCorpus | モノレポ |
| philengine Python版（embedder.py分離） | プラガブルバックエンド | philcore |
| JJDH論文投稿 | 査読付き論文 | 既存実装 |

### Phase 1: エンジンとAPI（2026年5月〜7月）

**目標**: R↔Python接続の確立、概念検索MVP

| タスク | 成果物 | 依存 |
|--------|--------|------|
| philapi (FastAPI) 実装 | REST API（embed/search） | philengine |
| R philengine（API client） | R→Python埋め込み | philapi |
| R philmap 基本機能 | phil_compare(), phil_search() | philengine |
| phil-hub 基盤 | PhilCorpusHub MVP | philcore |
| philengine 多バックエンド | OpenAI/Cohere対応 | philengine |

### Phase 2: ワークベンチMVP（2026年8月〜10月）

**目標**: 哲学研究者が触れるインターフェースの提供

| タスク | 成果物 | 依存 |
|--------|--------|------|
| philworkbench 動詞体系 | phil_read/explore/compare/plot | Phase 1全体 |
| phil_dashboard() Shiny | インタラクティブUI | philworkbench |
| phil.concepts.db 構築 | 概念アノテーションDB | shared/ontology |
| ユーザーテスト（哲学研究者） | フィードバック | philworkbench |
| 科研費萌芽申請 | 申請書 | Phase 1成果 |

### Phase 3: 専門分析機能（2026年11月〜2027年3月）

**目標**: philtext/philgraphの本格実装

| タスク | 成果物 | 依存 |
|--------|--------|------|
| philtext 論証抽出 | ArgumentExtractor | philengine |
| philtext 影響検出 | InfluenceDetector | philengine |
| philgraph データインジェスタ | PhilPapers/InPhO/Wikidata | philcore |
| philgraph Neo4j バックエンド | 本番知識グラフ | philgraph |
| phil.traditions.db 構築 | 伝統構造DB | shared/config |
| philtext 解釈追跡 | InterpretationTracker | philcore |

### Phase 4: エコシステム成熟（2027年4月〜）

**目標**: 外部公開、コミュニティ構築

| タスク | 成果物 | 依存 |
|--------|--------|------|
| phil-texts パッケージ群 | 正典テキスト5件以上 | PhilCorpusHub |
| PhilAnnotationHub | アノテーション公開基盤 | Phase 3 |
| Python philbench | Streamlitダッシュボード | 全Python層 |
| CRAN/PyPI 公開 | パッケージ公開 | テスト完備 |
| 論文: エコシステム全体 | 方法論論文 | 全Phase |
| 外部研究者との共同利用 | コミュニティ形成 | 公開 |

### Phase間の依存関係

```
Phase 0 (基盤)
  │
  ├──→ Phase 1 (エンジン+API)
  │      │
  │      ├──→ Phase 2 (ワークベンチMVP)  ← 哲学研究者に最初に見せる
  │      │      │
  │      │      └──→ Phase 4 (成熟)
  │      │
  │      └──→ Phase 3 (専門分析)
  │             │
  │             └──→ Phase 4 (成熟)
  │
  └──→ JJDH論文投稿（Phase 0と並行）
```

---

## 付録

### A. 非古典論理サポート仕様

| 論理体系 | 起源 | 値 | philcoreでの実装 |
|---------|------|-----|----------------|
| 四句分別 (Catuskoti) | 龍樹 (2c) | T, F, Both, Neither + 全否定 | `CatuskotiEvaluation` |
| 場所論理 (Basho) | 西田幾多郎 (1926) | 有の場所 ⊂ 相対無 ⊂ 絶対無 | `BashoEnvelopment` |
| 矛盾許容論理 | Belnap (1977) | T, F, Both, Neither | `ParaconsistentValuation` |
| 弁証法論理 | Hegel (1807) | テーゼ→アンチテーゼ→ジンテーゼ | `DialecticalMoment` |

### B. 学派分類体系（40+学派）

```yaml
western:
  ancient: [platonism, aristotelianism, stoicism, epicureanism, skepticism, neoplatonism]
  medieval: [scholasticism, thomism, scotism, nominalism]
  modern: [rationalism, empiricism, german_idealism, utilitarianism]
  contemporary: [analytic, continental, phenomenology, existentialism,
                 pragmatism, process_philosophy, critical_theory, poststructuralism]
east_asian:
  chinese: [confucianism, neo_confucianism, new_confucianism, daoism,
            chinese_buddhism, legalism, mohism]
  japanese: [kyoto_school, zen_buddhism, japanese_confucianism, mito_school,
             national_learning, watsuji_ethics]
  korean: [korean_confucianism, korean_buddhism]
south_asian:
  hindu: [vedanta, advaita, vishishtadvaita, yoga, samkhya, nyaya, vaisheshika, mimamsa]
  buddhist: [theravada, madhyamaka, yogacara, tibetan_buddhism]
  heterodox: [jainism, carvaka, ajivika]
islamic:
  kalam: [ashari, mutazili, maturidi]
  falsafa: [avicennism, averroism]
  illuminationist: [ishraqism]
  contemporary: [islamic_modernism]
african:
  ubuntu_philosophy, sage_philosophy, ethnophilosophy, african_existentialism
```

### C. ベンチマーク概念ペア（ground truth）

VALIDATION_PLAN.md に定義された15ペア（学術文献に基づく）：

| ペア | 伝統A | 伝統B | 予想類似度 | 根拠文献 |
|------|-------|-------|-----------|---------|
| 間柄 ↔ Mitsein | 和辻倫理 | 現象学 | 高 | Krueger 2009 |
| 場所 ↔ Lichtung | 京都学派 | ハイデガー | 中-高 | Davis 2019 |
| 仁 ↔ Ubuntu | 儒教 | アフリカ | 中 | Metz 2017 |
| 空 ↔ Différance | 中観派 | 脱構築 | 中 | Loy 1987 |
| 道 ↔ Logos | 道家 | 古代ギリシャ | 低-中 | Zhang 2002 |
| ... | ... | ... | ... | ... |

### D. 既存リソースとの連携

| 外部リソース | 連携方法 | 連携先パッケージ |
|-------------|---------|----------------|
| PhilPapers | JSON API | philgraph (ingester) |
| InPhO | REST API + OWL | philgraph, phil.concepts.db |
| Wikidata | SPARQL | philgraph, openalex-corpus-builder |
| Chinese Text Project | Python API | philtext (corpus) |
| Sanskrit Library | HTTP scraping | philtext (corpus) |
| OpenAlex | REST API | openalex-philosophy-corpus-builder |
| PubMed | E-utilities API | phil-hub (metadata) |
| Crossref | REST API | phil-hub (DOI resolution) |
