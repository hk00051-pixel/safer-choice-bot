import os
import pandas as pd
import streamlit as st

# Configure the browser page settings
st.set_page_config(page_title="EPA Safer Choice Assistant", page_icon="🌱", layout="centered")

def search_csv_for_keyword(user_query):
    """Searches the CSV data directly and returns matching products or general guidance."""
    csv_path = "products.csv"
    
    if not os.path.exists(csv_path):
        return "⚠️ Database file (products.csv) not found in the GitHub repository. Please upload it."
        
    try:
        df = pd.read_csv(csv_path)
        
        # Clean up user query into search keywords
        filler_words = {
            "i", "need", "a", "an", "the", "want", "find", "look", "looking", 
            "for", "give", "me", "show", "tell", "about", "is", "are", "any", 
            "please", "help", "with", "safer", "choice", "product", "products"
        }
        query_words = [w.strip().lower() for w in user_query.split()]
        search_terms = [w for w in query_words if w not in filler_words and len(w) > 1]
        
        # Greeting handler
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon"}
        if any(g in query_words for g in greetings) and not search_terms:
            return "Hello! I am your EPA Safer Choice product locator. Type a product type like 'glass cleaner', 'laundry', or a brand name to search our database!"

        if not search_terms:
            return "Please type a specific keyword or product type (e.g., 'soap', 'cleaner', 'detergent') so I can search the inventory for you."
            
        # Match search terms across all columns in the spreadsheet
        search_pattern = '|'.join(search_terms)
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_pattern, na=False)).any(axis=1)
        matched_df = df[mask]
        
        if matched_df.empty:
            return f"I couldn't find any products specifically matching '{user_query}' in our verified dataset. Try using simpler terms like 'floor', 'glass', or 'dish'."
            
        # Format matching rows nicely for the chat interface
        response_text = f"### Found {len(matched_df)} matching verified product(s):\n\n"
        for idx, row in matched_df.head(5).iterrows():
            # Looks for common column names. Adjust if your CSV columns are named differently!
            brand = row.get('Brand', row.get('brand', ''))
            product_name = row.get('Product', row.get('product_name', row.get('Product Name', '')))
            company = row.get('Company', row.get('company', ''))
            
            response_text += f"**{idx+1}. {brand} - {product_name}**\n"
            if str(company) != 'nan':
                response_text += f"   *Manufacturer:* {company}\n"
            response_text += "\n"
            
        if len(matched_df) > 5:
            response_text += f"*Showing the top 5 results out of {len(matched_df)} items found.*"
            
        return response_text
        
    except Exception as e:
        return f"⚠️ Error scanning the product inventory file: {e}"

# --- STREAMLIT UI DESIGN ---
st.title("🌱 EPA Safer Choice Assistant")
st.caption("Instantly locate verified, safer chemical alternatives from your database.")

# Initialize message history array in browser memory if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to EPA Safer Choice products! What type of product or brand are you looking for today?"}
    ]

# Render continuous conversation bubbles on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture live user typing input from the browser chat bar
if user_input := st.chat_input("Search safer choice products..."):
    
    # Render user bubble instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Perform keyless direct database lookup
    search_result = search_csv_for_keyword(user_input)

    # Render results bubble instantly
    with st.chat_message("assistant"):
        st.markdown(search_result)
    st.session_state.messages.append({"role": "assistant", "content": search_result})
