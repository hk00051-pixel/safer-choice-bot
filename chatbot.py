import os
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# Configure the browser page settings
st.set_page_config(page_title="EPA Safer Choice Assistant", page_icon="🌱", layout="centered")

# --- SIMPLEST API KEY SEARCH ---
API_KEY = None

# Look for key in secrets.txt file first
if os.path.exists("secrets.txt"):
    with open("secrets.txt", "r") as f:
        API_KEY = f.read().strip()

# Fallback to Streamlit Cloud memory
if not API_KEY and "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]

# Fallback to local machine memory
if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the client if key is found
if API_KEY and not API_KEY.startswith("PASTE"):
    client = genai.Client(api_key=API_KEY)
else:
    client = None

def search_csv_for_keyword(user_query):
    """Filters conversational words and searches CSV data."""
    csv_path = "products.csv"
    if not os.path.exists(csv_path):
        return "No local product database available."
    try:
        df = pd.read_csv(csv_path)
        filler_words = {"i", "need", "a", "an", "the", "want", "find", "looking", "for", "please", "help"}
        query_words = [w.strip().lower() for w in user_query.split()]
        search_terms = [w for w in query_words if w not in filler_words and len(w) > 1]
        if not search_terms:
            return df.head(5).to_string(index=False)
        search_pattern = '|'.join(search_terms)
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_pattern, na=False)).any(axis=1)
        matched_df = df[mask]
        return matched_df.head(5).to_string(index=False) if not matched_df.empty else df.head(5).to_string(index=False)
    except Exception as e:
        return f"Error reading database: {e}"

# --- STREAMLIT UI DESIGN ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("Find verified, safer chemical alternatives for your everyday use.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome to EPA Safer Choice products! How may I help you?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask about safer choice products..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    if not client:
        with st.chat_message("assistant"):
            st.markdown("⚠️ **API Key Error:** The application does not have a valid Gemini API Key string. Please complete Step 2.")
    else:
        relevant_inventory = search_csv_for_keyword(user_input)
        strict_rules = (
            "You are an automated customer service assistant specialized in EPA Safer Choice products.\n"
            f"Answer user questions dynamically using this inventory context:\n{relevant_inventory}"
        )
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_input,
                    config=types.GenerateContentConfig(system_instruction=strict_rules)
                )
                solution_text = response.text
                message_placeholder.markdown(solution_text)
                st.session_state.messages.append({"role": "assistant", "content": solution_text})
            except Exception as e:
                message_placeholder.markdown(f"⚠️ *Connection error or invalid key layout: {e}*")
