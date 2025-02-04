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
    print("DEBUG: Uploaded file widget rendered.")

    # User input query using text_area
    query = st.text_area("💬 Enter your query:")
    print("DEBUG: Query text_area rendered.")

    # Analyze button
    analyze_button = st.button("🚀 Analyze Document")
    print("DEBUG: Analyze button rendered.")

# Display chat history (includes welcome message)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
print("DEBUG: Chat history displayed.")

# Process query when analyze button is clicked
if analyze_button:
    print("DEBUG: Analyze button clicked.")
    if uploaded_file is None:
        print("DEBUG: No file uploaded.")
        st.warning("⚠️ Please upload a PDF file first.")
    elif not query.strip():
        print("DEBUG: Query is empty.")
        st.warning("⚠️ Please enter a query.")
    else:
        print("DEBUG: Starting query processing...")
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name
            print(f"DEBUG: Temporary PDF file created at: {pdf_path}")

        # Display user message in chat container
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        print("DEBUG: User message added to chat.")

        # Display progress bar inside the sidebar
        with st.sidebar:
            total_steps = 5  # Adjust based on LangGraph pipeline
            print("DEBUG: Sidebar progress bar section reached.")

        # Async function for processing query
        async def process_and_display():
            print("DEBUG: Starting async process_and_display function.")
            try:
                results = await process_query(pdf_path, query)
                print("DEBUG: process_query completed successfully.")
            except Exception as e:
                print("DEBUG: Exception during process_query:", e)
                st.error("An error occurred while processing the query.")
                return

            # Display assistant response in chat container with original formatting
            with st.chat_message("assistant"):
                response_container = st.empty()
                response_text = ""
                print("DEBUG: Beginning to process results for display.")

                for res in results:
                    print("DEBUG: Processing result:", res)
                    for char in res:
                        response_text += char
                        # Update display after a full sentence or newline
                        if char in {".", "?", "!", "\n"}:
                            response_container.markdown(response_text)
                            time.sleep(0.05)

                # Ensure final output is correctly formatted
                response_container.markdown(response_text)
                print("DEBUG: Final assistant response displayed:", response_text)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            print("DEBUG: Assistant response added to session state.")

            # Clean up temporary file
            try:
                os.unlink(pdf_path)
                print(f"DEBUG: Temporary file {pdf_path} deleted.")
            except Exception as e:
                print(f"DEBUG: Error deleting temporary file {pdf_path}:", e)

        # Run the async function
        print("DEBUG: Running process_and_display coroutine...")
        asyncio.run(process_and_display())
        print("DEBUG: process_and_display coroutine finished.")
