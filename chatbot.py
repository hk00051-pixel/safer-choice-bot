import os
import pandas as pd
import streamlit as st

# Configure the browser page settings
st.set_page_config(page_title="EPA Safer Choice Assistant", page_icon="🌱", layout="centered")

def process_chat_bot_response(user_query):
    """Processes natural language phrases and returns a tailored chatbot response without an API Key."""
    csv_path = "products.csv"
    query_clean = user_query.strip().lower()
    
    # 1. CONVERSATIONAL DIALOGUE MATRIX (Chatbot Greetings & Small Talk)
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "yo", "hi there"]
    bot_identity = ["who are you", "what is your name", "what do you do", "what are you"]
    gratitude = ["thank you", "thanks", "awesome", "perfect", "great", "ok", "okay"]
    
    # Handle pure casual entries
    if query_clean in greetings:
        return "Hello! I am your EPA Safer Choice Assistant. 🌱 I can help you find verified, safer chemical products. What category or brand are you looking for?"
        
    if any(phrase in query_clean for phrase in bot_identity):
        return "I am an automated EPA Safer Choice customer service assistant! My job is to instantly filter and match verified, eco-safe household cleaners from our local database."
        
    if any(phrase in query_clean for phrase in gratitude):
        return "You're very welcome! Let me know if you need to search for any other products, brands, or manufacturers."

    # 2. DATABASE KEYWORD EXTRACTION MATCHING
    if not os.path.exists(csv_path):
        return "⚠️ Database error: The inventory file `products.csv` was not found in your repository. Please upload it to GitHub."
        
    try:
        df = pd.read_csv(csv_path)
        
        # Strip away common speech filler words to find structural keywords
        filler_words = {
            "i", "need", "a", "an", "the", "want", "find", "look", "looking", 
            "for", "give", "me", "show", "tell", "about", "is", "are", "any", 
            "please", "help", "with", "safer", "choice", "product", "products", "search"
        }
        query_words = query_clean.split()
        search_terms = [w for w in query_words if w not in filler_words and len(w) > 1]
        
        if not search_terms:
            return "I'm ready to search! Please provide a search term like 'soap', 'laundry detergent', 'glass cleaner', or a specific brand name."

        # Search rows matching any keywords
        search_pattern = '|'.join(search_terms)
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_pattern, na=False)).any(axis=1)
        matched_df = df[mask]
        
        # If no strict dataset match found, fallback conversational prompt
        if matched_df.empty:
            return f"I searched the dataset for '{', '.join(search_terms)}' but couldn't find an exact match. Try checking your spelling or looking for a general class like 'floor', 'dish', or 'cleaner'!"
            
        # 3. CHAT COMPOSITION BUILDER (Translates rows into chat dialogue sentences)
        total_found = len(matched_df)
        response = f"I found **{total_found} verified product(s)** matching your request! Here are the recommended choices:\n\n"
        
        # Print top 4 matching data lines cleanly
        for idx, row in matched_df.head(4).iterrows():
            brand = str(row.get('Brand', row.get('brand', ''))).strip()
            product = str(row.get('Product', row.get('product_name', row.get('Product Name', '')))).strip()
            company = str(row.get('Company', row.get('company', ''))).strip()
            
            response += f"🔹 **{brand}** — *{product}*\n"
            if company and company != 'nan':
                response += f"   *(Manufactured by: {company})*\n"
            response += "\n"
            
        if total_found > 4:
            response += f"*Note: There are {total_found - 4} more alternatives matching this criteria in our full inventory ledger.*"
            
        return response

    except Exception as e:
        return f"⚠️ System Error scanning data files: {e}"

# --- STREAMLIT USER INTERFACE FRAMEWORK ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("Chat directly with your product database—instantly validated, no keys required.")

# Initialize or retain chat memory threads
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to EPA Safer Choice products! How can I assist you with your cleaning lookup today?"}
    ]

# Render interactive bubble historical timeline
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture real-time user keystroke entry
if user_input := st.chat_input("Ask about safer choice products..."):
    
    # Print user bubble immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate reply
    bot_reply = process_chat_bot_response(user_input)

    # Print chatbot answer bubble immediately
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
