import os
import time
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# Configure the browser page settings
st.set_page_config(page_title="EPA Safer Choice Assistant", page_icon="🌱", layout="centered")

# --- SECURE API KEY INITIALIZATION ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
elif os.getenv("GEMINI_API_KEY"):
    API_KEY = os.getenv("GEMINI_API_KEY")
else:
    API_KEY = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None

def search_csv_for_keyword(user_query):
    """Dynamically reads the local inventory and prepares text context for the AI."""
    csv_path = "products.csv"
    if not os.path.exists(csv_path):
        return "No local product database available."
    try:
        df = pd.read_csv(csv_path)
        return df.head(45).to_string(index=False)
    except Exception as e:
        return f"Error reading database: {e}"

# --- STREAMLIT UI DESIGN ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("Live AI Agent powered by Gemini—with full multi-turn chat memory tracking.")

# Initialize standard chat timeline arrays
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to the EPA Safer Choice Agent. Ask me anything about our eco-safe products!"}
    ]

# Render interactive bubble historical logs
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask about safer choice products..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    if not client:
        with st.chat_message("assistant"):
            st.markdown("⚠️ **Secrets Missing:** Please confirm your GEMINI_API_KEY is active in your Streamlit panel.")
    else:
        inventory_context = search_csv_for_keyword(user_input)

        # Rigid system configurations enforcing fallback protection patterns
        agent_system_instruction = (
            "SYSTEM IDENTITY & MEMORY REASONING:\n"
            "You are a live, conversational expert AI customer service agent built exclusively for EPA Safer Choice products.\n"
            "You have complete memory retention of previous turns in this specific chat history. Always look back at prior lines to understand what product category the user is discussing.\n\n"
            "CRITICAL SECURITY LAWS:\n"
            "1. You are ONLY allowed to discuss household cleaning, eco-safe chemistry, brands, or verified products listed inside the dataset below.\n"
            "2. If the user asks ANY completely random, conversational, or irrelevant question (e.g., math, history, coding, space, general non-cleaning talk, or things unrelated to the database), you must reply EXACTLY with this phrase and absolutely nothing else:\n"
            "   'Not available.'\n"
            "3. Do not repeat greeting messages or say 'Hello!' if you have already greeted the user earlier in the chat logs.\n"
            "4. When a user asks to 'suggest something good' or follow-up questions, look at the chat history to see what they were looking at before, pull a brand choice matching that category from the dataset, and give a clear recommendation in 2 sentences.\n\n"
            f"AVAILABLE VERIFIED INVENTORY DATA:\n{inventory_context}"
        )

        # --- MEMORY COMPILER FOR LIVE AGENT TRANSCRIPT ---
        # Converts Streamlit logs into formal structure objects Gemini naturally interprets
        gemini_chat_history = []
        for m in st.session_state.messages:
            # Map roles accurately (Streamlit uses 'assistant', Gemini API requires 'model')
            g_role = "user" if m["role"] == "user" else "model"
            gemini_chat_history.append(
                types.Content(
                    role=g_role,
                    parts=[types.Part.from_text(text=m["content"])]
                )
            )

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            success = False
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=gemini_chat_history,  # <-- FIX: Passes the whole live conversation history!
                        config=types.GenerateContentConfig(
                            system_instruction=agent_system_instruction,
                            temperature=0.2  # Low temperature preserves precise guardrails while maintaining natural memory flow
                        )
                    )
                    solution_text = response.text
                    message_placeholder.markdown(solution_text)
                    st.session_state.messages.append({"role": "assistant", "content": solution_text})
                    success = True
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "exhausted" in error_str:
                        message_placeholder.markdown(f"⏳ *Free-tier busy... automatically retrying in {attempt + 2} seconds...*")
                        time.sleep(attempt + 2)
                    else:
                        message_placeholder.markdown(f"⚠️ *System message: {e}*")
                        break
            
            if not success and "429" in error_str:
                message_placeholder.markdown("⚠️ *The free-tier server is heavily loaded right now. Please wait 10 seconds before typing your next request.*")
