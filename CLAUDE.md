# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

個人用のAIライティングツール（Python + Streamlit + Gemini API）。DB・認証は意図的に持たない（履歴は `st.session_state` のみで、再起動すると消える）。テストとlintは未整備。

## Commands

```bash
.venv/bin/pip install -r requirements.txt     # 依存関係（仮想環境は .venv）
.venv/bin/streamlit run app.py                # 起動（http://localhost:8501）
```

APIキーは `.env` の `GEMINI_API_KEY`（雛形は `.env.example`）か、サイドバー入力で渡す。モデルの既定値は `GEMINI_MODEL` 環境変数で上書きできる（未設定時 `gemini-3.6-flash`）。

UIをAPIなしで確認するには `streamlit.testing.v1.AppTest.from_file('app.py').run()` が使える。

## Architecture

2ファイル構成で、機能定義とUI/API呼び出しを分離している。

- `tools.py`: `TOOLS` 辞書が全機能の唯一の定義元。キーがサイドバーの表示名で、値は次を持つ。
  - `fields`: 入力項目のリスト。`type` は `area` / `line` / `select`。
  - `required`: 空だと生成しない入力項目の `key`。
  - `tone` / `length`: 共通の文体・分量セレクタを出すかどうか。
  - `build`: 入力値の dict からプロンプト文字列を返す関数。
- `app.py`: `TOOLS` を走査して入力欄を動的に描画し、`build` で作ったプロンプトを `stream_gemini`（`google-genai` の `generate_content_stream`）に渡す。結果は `st.write_stream` で表示し、履歴に追加する。

新しい機能を足すときは `tools.py` に `build` 関数と `TOOLS` エントリを追加するだけでよく、`app.py` の変更は要らない。

`build` に渡る dict には、入力項目の値に加えて `tone` と `length` が常に入る。無効化した項目は `"標準"` になる。ウィジェットのキーは `f"{tool_name}-{key}"` で、機能を切り替えても入力が混ざらない。

全機能共通のシステムプロンプト（前置き禁止など）は `tools.SYSTEM_PROMPT`。
