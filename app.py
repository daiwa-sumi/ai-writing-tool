"""AIライティングツール（個人用 / Streamlit + Gemini API）"""
import os
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from tools import LENGTHS, SYSTEM_PROMPT, TONES, TOOLS

load_dotenv()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []


def stream_gemini(api_key: str, model: str, prompt: str, temperature: float, retries: int = 3):
    """ストリーミング生成。出力開始前の 429/503 は待って自動再試行する。"""
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=temperature)
    for attempt in range(retries + 1):
        started = False
        try:
            for chunk in client.models.generate_content_stream(model=model, contents=prompt, config=config):
                if chunk.text:
                    started = True
                    yield chunk.text
            return
        except errors.APIError as e:
            if started or e.code not in (429, 503) or attempt == retries:
                raise
            time.sleep(2 ** (attempt + 1))  # 2, 4, 8秒


# ---------- サイドバー ----------
with st.sidebar:
    st.title("✍️ AIライティング")
    tool_name = st.radio("機能を選ぶ", list(TOOLS.keys()))

    st.divider()
    st.subheader("設定")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Gemini APIキー", value="", type="password",
        placeholder="設定済み（.env）" if env_key else "AIza...",
        help=".env の GEMINI_API_KEY を使う場合は空欄でOKです。",
    ) or env_key
    model = st.text_input("モデル", value=DEFAULT_MODEL, help="利用できなくなった場合はここで別のモデル名に変更できます。").strip() or DEFAULT_MODEL
    temperature = st.slider("創造性（temperature）", 0.0, 2.0, 0.8, 0.1)

    st.divider()
    st.subheader("履歴")
    if st.session_state.history:
        if st.button("履歴をクリア", use_container_width=True):
            st.session_state.history = []
            st.rerun()
        for item in reversed(st.session_state.history):
            with st.expander(f"{item['time']} {item['tool']}"):
                st.markdown(item["output"])
    else:
        st.caption("生成結果がここに残ります（再起動で消えます）。")

# ---------- メイン ----------
tool = TOOLS[tool_name]
st.header(tool_name)

values = {}
for f in tool["fields"]:
    k, label = f["key"], f["label"]
    wid = f"{tool_name}-{k}"
    if f["type"] == "area":
        values[k] = st.text_area(label, height=f["height"], placeholder=f["placeholder"], key=wid)
    elif f["type"] == "line":
        values[k] = st.text_input(label, placeholder=f["placeholder"], key=wid)
    else:
        values[k] = st.selectbox(label, f["options"], key=wid)

cols = st.columns(2)
values["tone"] = cols[0].selectbox("文体・トーン", TONES, key=f"{tool_name}-tone") if tool["tone"] else "標準"
values["length"] = cols[1].selectbox("分量", LENGTHS, index=1, key=f"{tool_name}-length") if tool["length"] else "標準"

if st.button("生成する", type="primary", use_container_width=True):
    if not api_key:
        st.error("Gemini APIキーが未設定です。サイドバーに入力するか、.env に GEMINI_API_KEY を設定してください。")
    elif not values[tool["required"]].strip():
        st.warning("必須項目（先頭の入力欄）を入力してください。")
    else:
        prompt = tool["build"](values)
        try:
            with st.container(border=True):
                output = st.write_stream(stream_gemini(api_key, model, prompt, temperature))
        except Exception as e:  # APIキー不正・通信・クォータ等
            st.error(f"生成に失敗しました: {e}")
        else:
            st.session_state.history.append(
                {"time": datetime.now().strftime("%H:%M"), "tool": tool_name, "output": output}
            )
            with st.expander("コピー用テキスト"):
                st.code(output, language=None, wrap_lines=True)
            st.download_button("テキストとして保存", output, file_name="output.txt")
