import os
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# Configure the browser page settings
st.set_page_config(page_title="EPA Safer Choice Assistant", page_icon="🌱", layout="centered")


# --- SECURE API KEY INITIALIZATION ---
# First, try to get the key from Streamlit Cloud Secrets (Production)
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
# Second, try to get it from local environment variables (Development)
elif os.getenv("GEMINI_API_KEY"):
    API_KEY = os.getenv("GEMINI_API_KEY")
# Final Fallback: Hardcode your key directly here if the above methods fail
else:
    API_KEY = AQ.Ab8RN6JaCmT9pacxp0vJM4YcYJyWTjPaXMenB0njip8xNRX5Qw

# Initialize the client globally
client = genai.Client(api_key=API_KEY)
        csv_path = "products.csv"
        if not os.path.exists(csv_path):
            return "No local product database available."
        
    try:
        df = pd.read_csv(csv_path)
        filler_words = {
            "i", "need", "a", "an", "the", "want", "find", "look", "looking", 
            "for", "give", "me", "show", "tell", "about", "is", "are", "any", 
            "please", "help", "with", "safer", "choice", "product", "products"
        }
        
        query_words = [w.strip().lower() for w in user_query.split()]
        search_terms = [w for w in query_words if w not in filler_words and len(w) > 1]
        
        # If no specific words found, give the first 10 rows as context
        if not search_terms:
            return df.head(10).to_string(index=False)
            
        search_pattern = '|'.join(search_terms)
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_pattern, na=False)).any(axis=1)
        matched_df = df[mask]
        
        if matched_df.empty:
            return df.head(10).to_string(index=False)
            
        return matched_df.head(10).to_string(index=False)
    except Exception as e:
        return f"Error reading inventory database: {e}"

# --- STREAMLIT UI DESIGN ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("Find verified, safer chemical alternatives for your everyday use.")

# Initialize message history array in browser memory if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to EPA Safer Choice products! How may I help you?"}
    ]

# Render the continuous conversation bubbles on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture live user typing input from the browser chat bar
if user_input := st.chat_input("Ask about safer choice products..."):
    
    # Render user bubble instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Fetch context from spreadsheet matching keywords
    relevant_inventory = search_csv_for_keyword(user_input)

    # Build direct, strict instructions matching your requirements
    strict_rules = (
        "You are an automated customer service assistant specialized in EPA Safer Choice products.\n"
        "Your goal is to answer user questions using the local inventory context provided below.\n\n"
        "CRITICAL OPERATION LAWS:\n"
        "1. If the user message is a simple hello, hi, or generic greeting, reply politely and ask how you can help.\n"
        "2. Answer questions using the data provided below. Do not say 'Information not available' if there are products present in the dataset.\n"
        "3. Keep your answers straight to the point and restricted to 1 or 2 sentences max.\n\n"
        f"CURRENT AVAILABLE INVENTORY DATA:\n{relevant_inventory}"
    )

    # Request response streaming directly into the web layout
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=strict_rules
                )
            )
            solution_text = response.text
            message_placeholder.markdown(solution_text)
            st.session_state.messages.append({"role": "assistant", "content": solution_text})
            
        except Exception as e:
            error_text = "Quota cooldown active. Please wait 15-20 seconds before typing your next request."
            if "429" not in str(e):
                error_text = f"An error occurred: {e}"
            message_placeholder.markdown(f"⚠️ *{error_text}*")
