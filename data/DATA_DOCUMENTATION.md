# Phil Ecosystem データドキュメント

> Version: 1.0.0
> Date: 2026-03-25
> Author: Yusuke Matsui

---

## 目次

1. [概要](#1-概要)
2. [データ収集方法](#2-データ収集方法)
3. [選択・除外基準](#3-選択除外基準)
4. [データサマリー](#4-データサマリー)
5. [詳細な内訳](#5-詳細な内訳)
6. [データベース設計](#6-データベース設計)
7. [再現性](#7-再現性)
8. [既知の制限事項](#8-既知の制限事項)
9. [ファイルインベントリ](#9-ファイルインベントリ)

---

## 1. 概要

Phil Ecosystemのデータ基盤は、哲学研究のための多言語・多伝統横断的なデータセットを提供する。
以下の4層で構成される：

```
Layer 1: 学術論文（抄録+メタデータ）  96,912件
Layer 2: 全文テキスト（OA論文PDF抽出） 5,249件
Layer 3: 一次テキスト（古典原典）       72テキスト
Layer 4: 知識グラフ（哲学者・影響関係）  5,556レコード
```

すべてのデータはDuckDBデータベース（`data/phil.duckdb`）およびParquetファイル（`data/parquet/`）に統合されている。

---

## 2. データ収集方法

### 2.1 データソース一覧

| ソース | URL | アクセス方法 | ライセンス | 収集内容 |
|--------|-----|------------|----------|---------|
| **OpenAlex** | api.openalex.org | REST API | CC0（メタデータ） | 論文メタデータ+抄録 |
| **Semantic Scholar** | api.semanticscholar.org | REST API | Open API | 論文メタデータ+TLDR |
| **Crossref** | api.crossref.org | REST API | Open | 追加抄録 |
| **J-STAGE** | api.jstage.jst.go.jp | REST API | Open | 日本語論文メタデータ |
| **Project Gutenberg** | gutenberg.org | HTTP | Public Domain | 西洋古典テキスト |
| **Chinese Text Project** | ctext.org | API | Open | 中国古典テキスト |
| **GRETIL** | gretil.sub.uni-goettingen.de | HTTP | Open | サンスクリット語テキスト |
| **Perseus Digital Library** | scaife-cts.perseus.org | CTS API | CC | 古典ギリシャ語・ラテン語 |
| **SuttaCentral** | suttacentral.net | API/HTML | CC | パーリ語経典 |
| **青空文庫** | aozora.gr.jp | HTTP/GitHub | Public Domain | 日本語近代哲学 |
| **Wikidata** | query.wikidata.org | SPARQL | CC0 | 哲学者・影響関係 |

### 2.2 収集プロセス

#### Phase 1: ジャーナル抄録の体系的収集

79の哲学専門ジャーナルを手動で選定し、OpenAlex APIから抄録付き論文を全件取得した。

**ジャーナル選定基準:**
- PhilPapersの分野別ジャーナルランキング
- 各哲学的伝統の代表的ジャーナル（分析、大陸、比較、非西洋）
- 言語的多様性（英独仏伊西語のジャーナルを含む）
- 歴史的ジャーナル（哲学史専門誌）

**取得方法:**
```
OpenAlex API → sources検索（ジャーナル名）
→ source.idでフィルタ → has_abstract:true
→ ページネーション（200件/ページ、最大50ページ/誌）
→ abstract_inverted_indexから抄録再構築
→ DuckDB + Parquetに格納
```

**レート制限:** 0.3-0.5秒/リクエスト、polite pool使用

#### Phase 2: 多言語OA論文の収集

28言語について、OpenAlex APIの言語フィルタ（`language:XX`）とPhilosophy概念タグ（`concept.id:C138885662`）を組み合わせて取得。

**重要な発見:** OpenAlexのPhilosophyタグは広義であり、教育学・看護学・経営学等の論文を大量に含む。
language フィルタ単独では哲学論文の精度が低い（日本語5%、韓国語8%のフィルタ通過率）。
このため多言語対応の関連度スコアリング（後述）を実装した。

#### Phase 3: 伝統別の対象収集

25の哲学的伝統ごとに、伝統固有のキーワード群でOpenAlexを検索。

**対象伝統:**
phenomenology, confucianism, buddhism, daoism, islamic_philosophy,
indian_philosophy, kyoto_school, african_philosophy, stoicism,
scholasticism, german_idealism, existentialism, hermeneutics,
analytic, poststructuralism, kantian, platonism, aristotelianism,
pragmatism, critical_theory, process_philosophy, korean_philosophy,
latin_american, ubuntu_philosophy, watsuji_ethics

#### Phase 4: 一次テキストの収集

著作権切れ（パブリックドメイン）のテキストをProject Gutenberg、GRETIL、Perseus、CTP、青空文庫から取得。

#### Phase 5: OA論文の全文取得

ジャーナル抄録データからOA（is_oa=true）かつ全文利用可能（has_fulltext=true）な論文のPDFをダウンロードし、PyMuPDFでテキスト抽出。

**成功率:** 6,935件中5,249件（76%）。主な失敗原因は出版社のbot access拒否（403 Forbidden）。

#### Phase 6: 知識グラフの構築

Wikidata SPARQLエンドポイントから哲学者情報（多言語ラベル付き）、影響関係、哲学的運動のデータを取得。

---

## 3. 選択・除外基準

### 3.1 論文の選択基準（`scripts/collect_corpus.py`で定義）

```python
@dataclass
class SelectionCriteria:
    min_relevance_score: int = 40        # 最低哲学関連度スコア
    min_abstract_length: int = 100       # 最低抄録長（文字）
    exclude_domains: list[str] = [       # 除外分野キーワード
        "nursing", "clinical trial", "patient care",
        "healthcare delivery", "classroom management",
        "teaching method", "curriculum design",
        "marketing strategy", "business model",
        "supply chain", "sports performance",
        "physical therapy", "rehabilitation",
        "software engineering", "agricultural", "crop yield",
    ]
```

### 3.2 哲学関連度スコアリング

各論文に0-100の関連度スコアを付与する。

**スコア構成:**
- コアキーワードマッチ: 最大50点（"philosophy", "ontology", "ethics"等）
- 伝統検出: 1伝統あたり+15点（正規表現ベースの語境界マッチング）
- 抄録品質: 200字以上で+10点
- 非英語ボーナス: 母語キーワードマッチで+25点、テキスト存在で+15点
- 除外ドメイン: マッチで-30点（英語テキストのみに適用）

**フィルタ閾値:** score >= 40 かつ excluded == False

### 3.3 伝統検出パターン

正規表現の語境界（`\b`）を使用し、部分文字列の誤検出を防止。

**修正された問題の例:**
- `"ren"` → `\bren\b` に変更（"different", "parent" 等の誤検出を防止）
- `"道"` → `"道家"`, `"道教"` に限定（中国語の一般語との混同を防止）
- `"kant"` → `\bkant\b(?!on\b)` に変更（"canton" 等の除外）

CJK文字パターンは語境界が適用されないため、複合語（"儒教", "現象学"等）を使用。

### 3.4 ジャーナル選定基準

以下の基準で79誌を手動選定：

| 基準 | 説明 |
|------|------|
| **分野代表性** | 各哲学分野（分析、大陸、比較等）の主要誌を含む |
| **言語多様性** | 英独仏伊西語の哲学誌を含む |
| **伝統カバレッジ** | 非西洋哲学（東アジア、南アジア、イスラーム、アフリカ）の専門誌 |
| **歴史的深さ** | 哲学史専門誌（J.History of Philosophy等） |
| **査読の有無** | 原則として査読付き学術誌 |

### 3.5 一次テキスト選定基準

| 基準 | 説明 |
|------|------|
| **著作権** | パブリックドメインまたはCC等のオープンライセンス |
| **哲学的重要性** | 各伝統の正典的テキスト |
| **言語的代表性** | 原典言語でのテキストを優先 |
| **デジタル利用可能性** | 信頼できるデジタルソースが存在すること |

### 3.6 除外されたデータとその理由

| 除外対象 | 理由 |
|---------|------|
| 非OA論文の全文 | 著作権制約 |
| 20世紀後半の哲学書（Heidegger, Sartre, Derrida等） | 著作権存続中 |
| OpenAlex Philosophy概念タグのみの論文 | ノイズ率99%（昆虫学、音響学等を含む） |
| 教育学・看護学・経営学の応用哲学論文 | 哲学の一次研究ではない |

---

## 4. データサマリー

### 4.1 全体統計

| 指標 | 数値 |
|------|------|
| **papers テーブル** | 96,912件 |
| 抄録付き（100字以上） | 92,267件（95.2%） |
| 全文テキスト保有 | 5,249件 |
| ジャーナル数 | 77誌 |
| 言語数 | 65言語 |
| **primary_texts テーブル** | 72テキスト |
| **philosophers テーブル** | 2,230人 |
| **influences テーブル** | 3,326関係 |
| **concepts テーブル** | 21概念 |
| **DuckDB サイズ** | 197MB |
| **Parquet サイズ** | 40MB |
| **全文テキスト（ディスク）** | 336MB |

### 4.2 言語別分布

| 言語 | 論文数 | 割合 |
|------|-------|------|
| English | 75,234 | 77.6% |
| French | 5,293 | 5.5% |
| German | 4,709 | 4.9% |
| Spanish | 3,273 | 3.4% |
| Italian | 1,275 | 1.3% |
| Chinese | 423 | 0.4% |
| Japanese | 377 | 0.4% |
| Portuguese | 374 | 0.4% |
| Indonesian | 348 | 0.4% |
| Dutch | 333 | 0.3% |
| Korean | 211 | 0.2% |
| その他20言語 | ~5,062 | 5.2% |

### 4.3 一次テキスト言語別分布

| 言語 | テキスト数 | 総文字数 |
|------|---------|---------|
| English (翻訳含む) | 29 | 21,354,387 |
| Sanskrit | 8 | 1,449,037 |
| Ancient Greek | 5 | 3,252,411 |
| Latin | 3 | 2,039,826 |
| Japanese | 15 | 606,359 |
| Chinese (古典) | 10 | 9,021 |
| Pali | 9 | 37,242 |

---

## 5. 詳細な内訳

### 5.1 ソース別内訳

| ソース | 件数 | 抄録有り | 全文有り | 説明 |
|--------|------|---------|---------|------|
| journal_abstracts | 85,161 | 83,924 | 4,373 | 79誌からの抄録 |
| oa_targeted | 2,818 | 2,571 | 0 | 伝統別対象収集 |
| oa_philosophy (EN) | 1,465 | 1,234 | 5 | 英語OA論文 |
| oa_german | 657 | 320 | 1 | ドイツ語OA |
| oa_french | 578 | 344 | 0 | フランス語OA |
| oa_chinese | 400 | 336 | 0 | 中国語OA |
| oa_italian | 399 | 214 | 0 | イタリア語OA |
| oa_japanese | 370 | 105 | 0 | 日本語OA |
| oa_turkish | 300 | 266 | 0 | トルコ語OA |
| oa_indonesian | 299 | 262 | 0 | インドネシア語OA |
| targeted | 3,017 | - | 0 | 伝統別追加取得 |
| semantic_scholar | 200 | - | 0 | Semantic Scholar |
| jstage | 337 | 0 | 0 | J-STAGE日本語 |
| その他18言語 | ~4,000 | ~3,000 | 0 | 多言語OA |

### 5.2 ジャーナル別内訳（上位20誌）

| ジャーナル | 論文数 | 抄録 | 全文 |
|---------|-------|------|------|
| Mind | 9,975 | 9,975 | 303 |
| Philosophy of Science | 7,030 | 7,030 | 0 |
| The Philosophical Quarterly | 5,796 | 5,796 | 206 |
| Journal of the History of Philosophy | 4,422 | 4,422 | 135 |
| Canadian Journal of Philosophy | 2,754 | 2,754 | 0 |
| Philosophy East and West | 2,331 | 2,331 | 105 |
| Philosophy and Phenomenological Research | 2,309 | 2,309 | 327 |
| The Philosophical Review | 2,146 | 2,146 | 46 |
| Synthese | 2,016 | 2,016 | 2,198 |
| Australasian Journal of Philosophy | 1,967 | 1,967 | 0 |
| Philosophy Today | 1,803 | 1,803 | 0 |
| Journal of the History of Ideas | 1,603 | 1,603 | 0 |
| Noûs | 1,513 | 1,513 | 179 |
| Journal of Applied Philosophy | 1,437 | 1,437 | 0 |
| Dialectica | 1,226 | 1,226 | 0 |
| Social Philosophy and Policy | 1,182 | 1,182 | 0 |
| Metaphilosophy | 1,180 | 1,180 | 0 |
| Isegoría | 1,015 | 1,015 | 0 |
| Social Epistemology | 1,013 | 1,013 | 0 |
| Kant-Studien | 1,054 | 1,054 | 0 |

### 5.3 一次テキスト詳細

#### Project Gutenberg (29テキスト)

| テキスト | 著者 | 言語 | 文字数 |
|---------|------|------|-------|
| Republic | Plato | en | 1,238,673 |
| Critique of Pure Reason (Teil 1) | Kant | de | 1,260,978 |
| Critique of Pure Reason (Teil 2) | Kant | de | 1,326,079 |
| Phänomenologie des Geistes | Hegel | de | 1,210,427 |
| Essais | Montaigne | fr | 1,908,554 |
| Summa Theologica | Aquinas | en | 2,911,838 |
| Also sprach Zarathustra | Nietzsche | de | 552,245 |
| Discours de la méthode | Descartes | fr | 711,752 |
| Pensées | Pascal | fr | 663,000 |
| ほか20テキスト | | | |

#### GRETIL Sanskrit (8テキスト)

| テキスト | 著者 | 文字数 |
|---------|------|-------|
| Abhidharmakosabhasya | Vasubandhu | 953,330 |
| Mulamadhyamakakarika | Nagarjuna | 50,971 |
| Vigrahavyavartani | Nagarjuna | 44,696 |
| Brahmasutra | Badarayana | 25,601 |
| Yogasutra | Patanjali | 13,186 |
| Bhagavadgita (English) | Anonymous | 147,382 |
| Upanishads (English) | Various | 125,356 |
| Dhammapada (English) | Anonymous | 88,515 |

#### Perseus Greek/Latin (5テキスト)

| テキスト | 著者 | 言語 | 文字数 |
|---------|------|------|-------|
| Enneads | Plotinus | grc | 1,784,015 |
| Confessions | Augustine | la | 1,011,918 |
| Republic | Plato | grc | 529,558 |
| Discourses | Epictetus | grc | 465,857 |
| Epistulae Morales | Seneca | la | 866,571 |

#### 青空文庫 (15テキスト)

| テキスト | 著者 | 文字数 |
|---------|------|-------|
| 善の研究 | 西田幾多郎 | 127,479 |
| 日本精神史研究 | 和辻哲郎 | 219,131 |
| 古寺巡礼 | 和辻哲郎 | 151,765 |
| 絶対矛盾的自己同一 | 西田幾多郎 | 51,557 |
| ほか11テキスト | | |

#### CTP Chinese (10テキスト)

論語、孟子、大学、中庸、荀子、道徳経、荘子、韓非子、墨子、心経

#### SuttaCentral Pali (9テキスト)

DN1, DN2, DN22, MN1, MN72, SN12.2, SN22.59, SN56.11, Dhp1-20

### 5.4 知識グラフ

| テーブル | レコード数 | ソース |
|---------|---------|--------|
| philosophers | 2,230 | Wikidata SPARQL |
| influences | 3,326 | Wikidata P737 |
| concepts | 21 | 手動キュレーション |

哲学者データは英語・日本語・ドイツ語のラベルを含む。

---

## 6. データベース設計

### 6.1 技術スタック

- **DuckDB** 1.5.1: 分析用組み込みデータベース
- **Parquet** (ZSTD圧縮): 列指向ストレージ、Arrow/Polars互換
- **PyArrow** 23.0.1: Parquet入出力

### 6.2 スキーマ定義

```sql
-- 論文テーブル
CREATE TABLE papers (
    id VARCHAR PRIMARY KEY,          -- OpenAlex ID or other unique ID
    title VARCHAR,                    -- 論文タイトル
    authors VARCHAR[],                -- 著者リスト
    year INTEGER,                     -- 出版年
    language VARCHAR,                 -- 言語コード (ISO 639-1)
    abstract TEXT,                    -- 抄録テキスト
    journal VARCHAR,                  -- ジャーナル名
    tradition VARCHAR[],              -- 検出された哲学的伝統
    themes VARCHAR[],                 -- 検出されたテーマ
    cited_by INTEGER DEFAULT 0,       -- 被引用数
    is_oa BOOLEAN DEFAULT FALSE,      -- OAかどうか
    doi VARCHAR,                      -- DOI
    fulltext_url VARCHAR,             -- 全文URL
    has_fulltext BOOLEAN DEFAULT FALSE, -- 全文テキスト保有フラグ
    abstract_length INTEGER,          -- 抄録長（文字数）
    source VARCHAR,                   -- データソース
    phil_score INTEGER DEFAULT 0,     -- 哲学関連度スコア
    created_at TIMESTAMP              -- 登録日時
);

-- 一次テキストテーブル
CREATE TABLE primary_texts (
    id VARCHAR PRIMARY KEY,
    title VARCHAR,
    author VARCHAR,
    language VARCHAR,                 -- 言語コード
    tradition VARCHAR,                -- 哲学的伝統
    source_collection VARCHAR,        -- gutenberg, ctp, perseus, sanskrit, pali, aozora
    year_composed INTEGER,            -- 成立年
    chars INTEGER,                    -- 文字数
    file_path VARCHAR                 -- ファイルパス
);

-- 哲学者テーブル
CREATE TABLE philosophers (
    wikidata_id VARCHAR PRIMARY KEY,  -- Wikidata QID
    name_en VARCHAR,
    name_ja VARCHAR,
    name_de VARCHAR,
    birth_year INTEGER,
    death_year INTEGER,
    country VARCHAR,
    tradition VARCHAR
);

-- 影響関係テーブル
CREATE TABLE influences (
    philosopher_id VARCHAR,           -- 影響を受けた哲学者
    influenced_by_id VARCHAR,         -- 影響を与えた哲学者
    philosopher_name VARCHAR,
    influenced_by_name VARCHAR
);

-- 概念テーブル
CREATE TABLE concepts (
    concept_id VARCHAR PRIMARY KEY,   -- phil:CXXXXX
    label_en VARCHAR,
    label_ja VARCHAR,
    label_de VARCHAR,
    label_zh VARCHAR,
    label_sa VARCHAR,
    definition_en TEXT,
    tradition VARCHAR,
    era VARCHAR,
    related_concepts VARCHAR,
    wikidata_qid VARCHAR
);

-- 埋め込みベクトルテーブル（将来使用）
CREATE TABLE embeddings (
    paper_id VARCHAR,
    model VARCHAR,                    -- モデル名
    vector FLOAT[768],                -- 768次元ベクトル
    created_at TIMESTAMP
);
```

### 6.3 インデックス

DuckDBは分析クエリに最適化されており、明示的なインデックス作成は不要。
Parquetファイルはcolumn pruningとrow group filteringにより高速にスキャンされる。

### 6.4 アクセス方法

#### Python (DuckDB)
```python
import duckdb
con = duckdb.connect("data/phil.duckdb")
results = con.sql("SELECT title, journal, cited_by FROM papers ORDER BY cited_by DESC LIMIT 10")
```

#### Python (Polars + Parquet)
```python
import polars as pl
papers = pl.read_parquet("data/parquet/papers.parquet")
papers.filter(pl.col("language") == "de").sort("cited_by", descending=True).head(10)
```

#### R (DuckDB)
```r
library(duckdb)
con <- dbConnect(duckdb(), "data/phil.duckdb")
dbGetQuery(con, "SELECT COUNT(*) FROM papers WHERE language = 'ja'")
```

#### R (Arrow + Parquet)
```r
library(arrow)
papers <- read_parquet("data/parquet/papers.parquet")
papers |> filter(language == "fr") |> nrow()
```

---

## 7. 再現性

### 7.1 再現可能なスクリプト

| スクリプト | 機能 |
|---------|------|
| `scripts/collect_corpus.py` | 体系的コーパス収集（選択基準+カバレッジレポート） |
| `scripts/fetch_oa_philosophy.py` | OA論文取得（ソース・言語・伝統指定） |
| `scripts/fetch_missing_abstracts.py` | Crossref/S2から不足抄録取得 |
| `scripts/download_nonccby_fulltext.py` | 非CC-BY OA論文のPDFダウンロード |
| `scripts/import_existing_data.py` | 既存データのインポート |
| `scripts/build_dbs.py` | SQLiteデータベース構築 |

### 7.2 再現手順

```bash
# 1. 体系的コーパス収集
python scripts/collect_corpus.py

# 2. カバレッジレポート
python scripts/collect_corpus.py --report

# 3. 事前確認（ドライラン）
python scripts/collect_corpus.py --dry-run
```

### 7.3 収集パラメータの記録

各収集実行は `data/corpus/YYYY-MM-DD/manifest.json` にパラメータ、ソース、統計量を記録する。

---

## 8. 既知の制限事項

### 8.1 選択バイアス

| バイアス | 説明 | 緩和策 |
|---------|------|--------|
| **英語優位** | 論文の77.6%が英語 | 28言語への拡張、多言語スコアリング |
| **OAバイアス** | OA論文のみ全文取得可能 | 非OA論文も抄録は取得 |
| **ジャーナル選定** | 手動選定79誌 | 選定基準の明示化 |
| **OpenAlexタグ精度** | Philosophy概念タグのノイズ99% | ジャーナル限定+関連度スコアリング |
| **時代偏重** | 2000年代以降が多い | 歴史的ジャーナルの収録 |

### 8.2 データ品質の課題

| 課題 | 説明 |
|------|------|
| **抄録再構築** | OpenAlexのabstract_inverted_indexからの再構築。語順が若干不正確な場合がある |
| **非英語抄録の少なさ** | 日本語論文の抄録率28%、ヒンディー語18% |
| **全文抽出品質** | PDFからのテキスト抽出。数式・図表・脚注が不正確な場合がある |
| **伝統分類の精度** | キーワードベースの自動分類。複数伝統にまたがる論文の扱い |

### 8.3 著作権制約

| 制約 | 影響を受けるデータ |
|------|----------------|
| **全文取得不可** | 非OA論文（出版社のペイウォール） |
| **一次テキスト不可** | Heidegger, Sartre, Derrida, Levinas, Foucault等（没後70年未経過） |
| **出版社403ブロック** | OUP, Wiley, Duke等のPDF（OAでもbot access拒否） |

### 8.4 カバレッジギャップ

| 領域 | 状態 |
|------|------|
| **キルケゴール原典（デンマーク語）** | Gutenberg非収録 |
| **アリストテレス『形而上学』（ギリシャ語原典）** | Scaife CTS非収録 |
| **フッサール原典（ドイツ語）** | 著作権要確認 |
| **アフリカ哲学の一次テキスト** | デジタル化が進んでいない |
| **イスラーム哲学の一次テキスト** | アラビア語デジタルテキストのアクセス困難 |

---

## 9. ファイルインベントリ

### 9.1 データベース

| ファイル | サイズ | 内容 |
|---------|------|------|
| `data/phil.duckdb` | 197MB | 統合データベース |
| `data/parquet/papers.parquet` | 39.5MB | 論文テーブル（ZSTD圧縮） |
| `data/parquet/philosophers.parquet` | 0.2MB | 哲学者テーブル |
| `data/parquet/influences.parquet` | 0.1MB | 影響関係テーブル |
| `data/parquet/primary_texts.parquet` | 0.01MB | 一次テキストテーブル |
| `data/parquet/concepts.parquet` | 0.01MB | 概念テーブル |

### 9.2 JSONデータ

| ディレクトリ | ファイル数 | 内容 |
|-----------|---------|------|
| `data/journal_abstracts/` | 3 | ジャーナル抄録+統計 |
| `data/journal_fulltext/` | 2+5,249 | URL索引+全文テキスト |
| `data/oa_*/` | 28 | 多言語OA論文 |
| `data/oa_targeted/` | 9 | 伝統別対象論文 |
| `data/enriched/` | 3 | エンリッチメント済みデータ |
| `data/corpus/2026-03-24/` | 4 | 体系的収集結果 |
| `data/knowledge_graph/` | 7 | Wikidata+PhilPapers |
| `data/classical_texts/` | 84+ | 一次テキスト |

### 9.3 スクリプト

| ファイル | 機能 |
|---------|------|
| `scripts/collect_corpus.py` | 体系的コーパス収集パイプライン |
| `scripts/fetch_oa_philosophy.py` | OA論文取得CLI |
| `scripts/fetch_missing_abstracts.py` | 不足抄録の追加取得 |
| `scripts/download_nonccby_fulltext.py` | 非CC-BY全文ダウンロード |
| `scripts/import_existing_data.py` | 既存データインポート |
| `scripts/build_dbs.py` | SQLiteデータベース構築 |

---

*本ドキュメントは2026-03-25時点の状態を記録している。データは継続的に拡充される予定であり、最新の状態は `python scripts/collect_corpus.py --report` で確認できる。*
