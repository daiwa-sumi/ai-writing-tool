"""各ライティング機能の定義（入力項目とプロンプト生成）。"""

TONES = ["標準", "丁寧・フォーマル", "カジュアル・親しみやすい", "簡潔・ビジネス", "専門的・論理的"]
LENGTHS = ["短め", "標準", "長め"]

SYSTEM_PROMPT = (
    "あなたは優秀な日本語ライターであり編集者です。"
    "指示に忠実に、自然で読みやすい日本語で出力してください。"
    "前置きや『承知しました』などの余計な説明は書かず、成果物のみを出力してください。"
    "出力はMarkdown形式で構わない場合のみMarkdownを使ってください。"
)


def _common(tone: str, length: str) -> str:
    return f"\n\n# 共通条件\n- 文体・トーン: {tone}\n- 分量: {length}"


def blog(v: dict) -> str:
    return (
        "以下の条件でブログ記事を執筆してください。"
        "タイトル、導入、見出し付きの本文、まとめの構成にしてください。\n\n"
        f"# テーマ\n{v['topic']}\n\n"
        f"# 想定読者\n{v['audience'] or '指定なし'}\n\n"
        f"# 含めたいキーワード・要点\n{v['keywords'] or '指定なし'}"
        + _common(v["tone"], v["length"])
    )


def email(v: dict) -> str:
    return (
        "受信したメールに対する返信文を作成してください。"
        "件名（Re:）と本文を出力し、宛名・挨拶・結びも含めてください。\n\n"
        f"# 受信したメール\n{v['received']}\n\n"
        f"# 返信で伝えたい内容\n{v['intent'] or '相手の意図を汲んで適切に返信してください'}"
        + _common(v["tone"], v["length"])
    )


def summary(v: dict) -> str:
    fmt = {
        "箇条書き": "箇条書きで要点をまとめる",
        "一段落": "一つの段落にまとめる",
        "要点＋結論": "『要点（箇条書き）』と『結論（1〜2文）』に分けてまとめる",
    }[v["format"]]
    return (
        f"以下の文章を要約してください。形式: {fmt}。\n\n# 原文\n{v['text']}"
        + _common(v["tone"], v["length"])
    )


def proofread(v: dict) -> str:
    return (
        "以下の文章を校正・推敲してください。誤字脱字・文法・表現の不自然さを直し、"
        "読みやすく整えます。出力は次の2部構成にしてください。\n"
        "## 修正後の文章\n## 主な修正点（箇条書き）\n\n"
        f"# 原文\n{v['text']}"
        + _common(v["tone"], "標準")
    )


def rewrite(v: dict) -> str:
    return (
        "以下の文章を、意味を変えずに指定の文体・トーンで書き直してください。\n\n"
        f"# 原文\n{v['text']}\n\n# 追加の指示\n{v['note'] or 'なし'}"
        + _common(v["tone"], v["length"])
    )


def translate(v: dict) -> str:
    return (
        f"以下の文章を{v['target']}に翻訳してください。直訳ではなく、"
        f"その言語で自然な表現にしてください。\n\n# 原文\n{v['text']}"
        + _common(v["tone"], "原文と同程度")
    )


def titles(v: dict) -> str:
    return (
        f"以下の内容について、{v['kind']}を10案出してください。"
        "それぞれ番号付きで、切り口が重ならないようにしてください。\n\n"
        f"# 内容\n{v['text']}"
        + _common(v["tone"], "短く")
    )


def sns(v: dict) -> str:
    return (
        f"以下の内容を元に、{v['platform']}向けの投稿文を3パターン作ってください。"
        "各パターンを『案1』『案2』『案3』の見出しで区切ってください。"
        f"ハッシュタグは{v['hashtag']}。\n\n# 内容\n{v['text']}"
        + _common(v["tone"], v["length"])
    )


def text_area(key, label, height=200, ph=""):
    return {"key": key, "label": label, "type": "area", "height": height, "placeholder": ph}


def text_line(key, label, ph=""):
    return {"key": key, "label": label, "type": "line", "placeholder": ph}


def select(key, label, options):
    return {"key": key, "label": label, "type": "select", "options": options}


# 表示名 -> 定義。tone/length を使うものは uses_tone / uses_length で制御。
TOOLS = {
    "📝 ブログ記事": {
        "build": blog, "required": "topic", "tone": True, "length": True,
        "fields": [
            text_line("topic", "テーマ・タイトル案", "例: 在宅ワークで集中力を保つ方法"),
            text_line("audience", "想定読者（任意）", "例: 20代のリモートワーカー"),
            text_area("keywords", "含めたいキーワード・要点（任意）", 120),
        ],
    },
    "✉️ メール返信": {
        "build": email, "required": "received", "tone": True, "length": True,
        "fields": [
            text_area("received", "受信したメール", 200),
            text_area("intent", "返信で伝えたい内容（任意）", 100, "例: 来週火曜なら都合が良いと伝える"),
        ],
    },
    "📄 要約": {
        "build": summary, "required": "text", "tone": True, "length": True,
        "fields": [
            text_area("text", "要約したい文章", 260),
            select("format", "要約形式", ["箇条書き", "一段落", "要点＋結論"]),
        ],
    },
    "🔍 校正・推敲": {
        "build": proofread, "required": "text", "tone": True, "length": False,
        "fields": [text_area("text", "校正したい文章", 260)],
    },
    "🎨 文体変換・リライト": {
        "build": rewrite, "required": "text", "tone": True, "length": True,
        "fields": [
            text_area("text", "書き直したい文章", 220),
            text_line("note", "追加の指示（任意）", "例: 専門用語を減らす"),
        ],
    },
    "🌐 翻訳": {
        "build": translate, "required": "text", "tone": True, "length": False,
        "fields": [
            text_area("text", "翻訳したい文章", 220),
            select("target", "翻訳先の言語", ["英語", "日本語", "中国語（簡体字）", "韓国語", "フランス語", "スペイン語"]),
        ],
    },
    "💡 タイトル・キャッチコピー案": {
        "build": titles, "required": "text", "tone": True, "length": False,
        "fields": [
            text_area("text", "内容の概要・本文", 200),
            select("kind", "案の種類", ["ブログ記事のタイトル", "キャッチコピー", "メールの件名", "動画のタイトル"]),
        ],
    },
    "📱 SNS投稿": {
        "build": sns, "required": "text", "tone": True, "length": True,
        "fields": [
            text_area("text", "投稿したい内容", 180),
            select("platform", "プラットフォーム", ["X（Twitter・140字程度）", "Instagram", "Facebook", "LinkedIn"]),
            select("hashtag", "ハッシュタグ", ["なし", "3個程度つける", "5個程度つける"]),
        ],
    },
}
