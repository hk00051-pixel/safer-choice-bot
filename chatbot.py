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
        # Pass the top 35 rows to stay inside free-tier token limits safely
        return df.head(35).to_string(index=False)
    except Exception as e:
        return f"Error reading database: {e}"

# --- STREAMLIT UI DESIGN ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("AI Agent powered by Gemini—focused exclusively on eco-safe verified items.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to the EPA Safer Choice Agent. Ask me anything about our eco-safe products!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask about safer choice products..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    if not client:
        with st.chat_message("assistant"):
            st.markdown("⚠️ **Configuration Setup:** Please insert your API key into your Streamlit Secrets panel.")
    else:
        inventory_context = search_csv_for_keyword(user_input)

        # Rigid guardrail configuration matching your direct specifications
        agent_system_instruction = (
            "SYSTEM IDENTITY & ROLE:\n"
            "You are a strict, expert AI customer service agent built exclusively for EPA Safer Choice products.\n\n"
            "CRITICAL SECURITY LAWS:\n"
            "1. You are ONLY allowed to answer questions related to household cleaning, eco-safe solutions, brands, or items present in the inventory dataset below.\n"
            "2. If the user asks ANY random or irrelevant question (e.g., math, history, coding, space, general life, recipe cooking, sports, chatting about other things, etc.), you must ignore it entirely and reply EXACTLY with this line: \n"
            "   'I am only here to help you about safer choice product or not available.'\n"
            "3. If they greet you (hi, hello), welcome them warmly and ask what cleaner or product they are looking for.\n"
            "4. When talking about relevant products, be concise, expert, helpful, and restrict answers to 2-3 sentences max.\n\n"
            f"AVAILABLE VERIFIED INVENTORY DATA:\n{inventory_context}"
        )

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_input,
                    config=types.GenerateContentConfig(
                        system_instruction=agent_system_instruction,
                        temperature=0.1  # Set ultra-low for extreme strictness on guardrails
                    )
                )
                solution_text = response.text
                message_placeholder.markdown(solution_text)
                st.session_state.messages.append({"role": "assistant", "content": solution_text})
                
            except Exception as e:
                # --- AUTOMATED FREE VERSION CIRCUIT BREAKER ---
                error_str = str(e).lower()
                if "429" in error_str or "exhausted" in error_str:
                    # Clear the error look and replace with a professional countdown
                    message_placeholder.markdown("⏳ *Google Free-Tier limit reached. Taking a brief 10-second cool-down to reset...*")
                    time.sleep(10)
                    message_placeholder.markdown("🔄 *Cool-down complete! Please type your question one more time.*")
                else:
                    message_placeholder.markdown(f"⚠️ *System message: {e}*")
