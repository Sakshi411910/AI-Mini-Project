import streamlit as st
import os
import json
import re
from pyvis.network import Network
from tempfile import NamedTemporaryFile
from PyPDF2 import PdfReader
import google.generativeai as genai
from itertools import cycle
from dotenv import load_dotenv

# -------------------- Streamlit Setup --------------------
st.set_page_config(layout="wide")
st.title("🧩 Mini Mind Mapper (Smart AI Version)")
st.write("Upload PDF, TXT, or paste text to generate a clean, colorful, and well-spaced AI mind map.")

# -------------------- Gemini API Key --------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("API key not found in .env file")
    st.stop()



# -------------------- File or Text Input --------------------
text = ""
uploaded_file = st.file_uploader("Upload TXT or PDF file", type=["txt", "pdf"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    else:
        text = uploaded_file.read().decode("utf-8")
elif user_text := st.text_area("Or paste your text here:"):
    text = user_text


def clean_text(t):
    return re.sub(r"\s+", " ", t.strip())


# -------------------- Button Trigger --------------------
if st.button("✨ Generate Smart Mind Map") and text:
    st.info("Analyzing with Gemini AI... Please wait ⏳")
    text = clean_text(text)

    try:
        # ✅ Correct model name
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = f"""
        You are an expert note visualizer.
        Analyze the following text and return:
        1. 6–8 main topics.
        2. For each topic, 3–5 important subtopics.
        3. A short summary (5–8 sentences).
        Return JSON only with keys: "topics" (list), "subtopics" (dict), "summary" (string).

        Text:
        {text}
        """

        response = model.generate_content(prompt)
        ai_output = response.text.strip()

        # Clean JSON
        if ai_output.startswith("```json"):
            ai_output = ai_output.replace("```json", "").replace("```", "").strip()

        data = json.loads(ai_output)
        topics = data.get("topics", [])
        subtopics = data.get("subtopics", {})
        summary = data.get("summary", "")

    except Exception as e:
        st.error(f"AI processing failed: {e}")
        st.stop()

    # -------------------- Mind Map Visualization --------------------
    st.subheader("🎨 Neat, Non-Overlapping Mind Map")

    # Color palette
    color_palette = [
        "#FFADAD", "#FFD6A5", "#FDFFB6",
        "#CAFFBF", "#9BF6FF", "#A0C4FF",
        "#BDB2FF", "#FFC6FF"
    ]
    color_cycle = cycle(color_palette)

    # Create the network
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#fffdf7",
        font_color="black",
        directed=False
    )

    # Improved physics for neat spacing
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "font": {
          "size": 20,
          "color": "#111",
          "face": "Arial",
          "strokeWidth": 2,
          "strokeColor": "#ffffff"
        },
        "shape": "dot"
      },
      "edges": {
        "smooth": false,
        "color": {"inherit": false},
        "width": 2
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 250,
          "springConstant": 0.05,
          "avoidOverlap": 1
        },
        "minVelocity": 0.75,
        "solver": "barnesHut",
        "stabilization": {"enabled": true, "iterations": 1000}
      },
      "interaction": {
        "dragNodes": true,
        "hover": true,
        "zoomView": true
      }
    }
    """)

    # Add nodes and edges
    for topic in topics:
        topic_color = next(color_cycle)
        net.add_node(
            topic,
            label=topic,
            color=topic_color,
            size=45,
            font={"size": 22, "color": "#111"},
            title=f"<b>Main Topic:</b> {topic}"
        )

        for sub in subtopics.get(topic, []):
            net.add_node(
                sub,
                label=sub,
                color="#E8E8E8",
                size=25,
                font={"size": 16, "color": "#333"},
                title=f"<b>Subtopic of {topic}:</b> {sub}"
            )
            net.add_edge(topic, sub, color=topic_color, width=2)

    # Save to temp file
    with NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.write_html(tmp_file.name)
        html_file = tmp_file.name

    # -------------------- Display Tabs --------------------
    tab1, tab2, tab3 = st.tabs(["🗺️ Mind Map", "📋 Topics Table", "📝 Short Notes"])

    with tab1:
        st.components.v1.html(open(html_file, "r", encoding="utf-8").read(), height=750)

    with tab2:
        st.table([{"Topic": t, "Subtopics": ", ".join(subtopics.get(t, []))} for t in topics])

    with tab3:
        st.write(summary)

    st.success("✅ Clean, well-spaced mind map generated successfully!")

else:
    st.info("Upload a file or paste text, then click **Generate Smart Mind Map** to begin.")
