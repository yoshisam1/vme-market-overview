import streamlit as st
import asyncio
import logging
import tempfile
import os
import time
from main import process_query

# Setup logging: write debug messages to a file and also print to console.
LOG_FILENAME = "debug.log"
logging.basicConfig(
    filename=LOG_FILENAME,
    filemode="w",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger()

# Optionally, also add a StreamHandler to output logs to stdout.
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(console_handler)

logger.info("Starting the Streamlit app.")

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
    uploaded_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])
    logger.debug("File uploader rendered.")
    
    query = st.text_area("💬 Enter your query:")
    logger.debug("Query text area rendered.")
    
    analyze_button = st.button("🚀 Analyze Document")
    logger.debug("Analyze button rendered.")

# Display chat history (includes welcome message)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
logger.debug("Chat history displayed.")

# Optionally, add a button to download the debug log (for troubleshooting)
if st.sidebar.button("Download Debug Log"):
    if os.path.exists(LOG_FILENAME):
        with open(LOG_FILENAME, "r") as f:
            st.download_button("Download Log", f.read(), file_name=LOG_FILENAME)
    else:
        st.write("No debug log available.")

# Process query when analyze button is clicked
if analyze_button:
    logger.info("Analyze button clicked.")
    if uploaded_file is None:
        logger.warning("No file uploaded.")
        st.warning("⚠️ Please upload a PDF file first.")
    elif not query.strip():
        logger.warning("Query is empty.")
        st.warning("⚠️ Please enter a query.")
    else:
        logger.info("Starting query processing.")
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name
            logger.debug(f"Temporary PDF file created at: {pdf_path}")

        # Display user message in chat container
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        logger.debug("User message added to chat.")

        # Async function for processing query
        async def process_and_display():
            logger.info("Starting async process_and_display function.")
            try:
                results = await process_query(pdf_path, query)
                logger.info("process_query completed successfully.")
            except Exception as e:
                logger.error("Exception during process_query", exc_info=True)
                st.error("An error occurred while processing the query.")
                return

            # Display assistant response in chat container
            with st.chat_message("assistant"):
                response_container = st.empty()
                response_text = ""
                logger.debug("Beginning to process results for display.")

                for res in results:
                    logger.debug(f"Processing result: {res}")
                    for char in res:
                        response_text += char
                        # Update display after a full sentence or newline
                        if char in {".", "?", "!", "\n"}:
                            response_container.markdown(response_text)
                            time.sleep(0.05)

                response_container.markdown(response_text)
                logger.debug(f"Final assistant response displayed: {response_text}")

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            logger.info("Assistant response added to session state.")

            # Clean up temporary file
            try:
                os.unlink(pdf_path)
                logger.debug(f"Temporary file {pdf_path} deleted.")
            except Exception as e:
                logger.error(f"Error deleting temporary file {pdf_path}:", exc_info=True)

        logger.info("Running process_and_display coroutine...")
        asyncio.run(process_and_display())
        logger.info("process_and_display coroutine finished.")
