import streamlit as st
import asyncio
from main import process_query
import tempfile
import os
import time

WELCOME_MESSAGE = """  
### 📌 Hi, VME Members!  
Sam, Jo, and Audrey here! 👋  
This AI chatbot helps you **gather supporting data** for market overview reports.  
If you're new, follow this **quick guide** to get the best results.

### **🔍 How to Use**  
1️⃣ **Open the sidebar** (if not already open).  
2️⃣ **Attach the PDF documents** you want to analyze.  
3️⃣ **Enter your query**: Specify what information you need (include sentiment if relevant).  
4️⃣ **Click "Analyze Document"** to start processing.  
5️⃣ **Understanding Sources**: "Source Page" refers to the **PDF page number**, not the document’s printed page.

### **✅ Best Practices & Tips**  
⚡ **Processing time:** 20-30 seconds on average.  
📄 **Works best on text-heavy PDFs.** The fewer documents & less text, the faster the results.  
🔄 **If the app crashes**, reload the page & follow the best practices below.  
🚫 **Avoid number-heavy PDFs** (e.g., financial statements with lots of tables).  
📊 **Annual Reports:** To improve accuracy, remove appendices or large data tables before uploading.  

Happy analyzing! 🎯  
"""

# Set Streamlit page config
st.set_page_config(
    page_title="📄 Document Analysis Chatbot",
    layout="wide",
)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

# Sidebar for user input
with st.sidebar:
    st.header("🔍 Document Analysis")

    # Upload PDF file
    uploaded_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])

    # User input query using text_area (unchanged)
    query = st.text_area("💬 Enter your query:")

    # Analyze button
    analyze_button = st.button("🚀 Analyze Document")

# Display chat history (includes welcome message)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process query when analyze button is clicked
if analyze_button:
    if uploaded_file is None:
        st.warning("⚠️ Please upload a PDF file first.")
    elif not query.strip():
        st.warning("⚠️ Please enter a query.")
    else:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        # Display user message in chat container
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Display progress bar inside the sidebar
        with st.sidebar:
            total_steps = 5  # Adjust based on LangGraph pipeline

        # Async function for processing query
        async def process_and_display():

            results = await process_query(pdf_path, query)

            # Display assistant response in chat container with original formatting
            with st.chat_message("assistant"):
                response_container = st.empty()
                response_text = ""

                for res in results:
                    for char in res:
                        response_text += char
                        if char in {".", "?", "!", "\n"}:  # Update display after full sentence or newline
                            response_container.markdown(response_text)
                            time.sleep(0.05)

                # Ensure final output is correctly formatted
                response_container.markdown(response_text)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_text})

            # Clean up temporary file
            os.unlink(pdf_path)

        asyncio.run(process_and_display())
