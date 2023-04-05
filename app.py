import streamlit as st
from llama_index import GPTSimpleVectorIndex, Document, SimpleDirectoryReader, QuestionAnswerPrompt, LLMPredictor, ServiceContext
import os
import openai 
import json

from langchain import OpenAI

import PyPDF2
from pathlib import Path
from llama_index import download_loader



st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="collapsed")
openai.api_key = os.getenv("API_KEY")
st.title("QuickBOM.ai")
st.caption("AI-powered BOM creation made easy")

DATA_DIR = "data"
# Create the data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

def delete_file(DATA_DIR, file_name):
    pdf_path = os.path.join(DATA_DIR, file_name)
    json_path = os.path.join(DATA_DIR, os.path.splitext(file_name)[0] + ".json")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        st.success(f"File {file_name} deleted successfully!")
    else:
        st.error(f"File {file_name} not found!")
    if os.path.exists(json_path):
        os.remove(json_path)

def save_uploaded_file(uploaded_file):
    with open(os.path.join(DATA_DIR, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())


col1, col2, col3, col4 = st.tabs(["Upload pdf", "extract Components", "fetch content", "generate bom"])

uploaded_file = col1.file_uploader("Upload PDF", type="pdf")
if uploaded_file is not None:
    # Save the uploaded file to the data directory
    save_uploaded_file(uploaded_file)
    col1.success("It would take a while to index the books, please wait..!")

# Create a button to create the index
# if col1.button("Create Index"):
    # Get the filename of the uploaded PDF
    pdf_filename = uploaded_file.name
    
    # Load the documents from the data directory
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    
    # Create the index from the documents
    index = GPTSimpleVectorIndex.from_documents(documents)
    
    # Save the index to the data directory with the same name as the PDF
    index.save_to_disk(os.path.join(DATA_DIR, os.path.splitext(pdf_filename)[0] + ".json"))
    col1.success("Index created successfully!")


index_filenames = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

if index_filenames:
    # If there are index files available, create a dropdown to select the index file to load
    index_file = col2.selectbox("Select an index file to load:", index_filenames,label_visibility="collapsed")
    index_path = os.path.join(DATA_DIR, index_file)
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=1024))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

    index = GPTSimpleVectorIndex.load_from_disk(index_path,service_context=service_context)
else:
    # If there are no index files available, prompt the user to upload a PDF file
    col2.warning("No index files found. Please upload a PDF file to create an index.")
    
toc = col2.button("Get Components")
if toc:
    toc_res = index.query(f" list out the electrical components and their quantities with their models used in the document, in a json format ")
    str_toc = str(toc_res)
    print(str_toc)
    json_output = json.loads(str_toc)
    col2.write(json_output)
    table_of_contents = json_output
    if "table_of_contents" not in st.session_state:
        st.session_state.table_of_contents = table_of_contents


    if "selected_items" not in st.session_state:
        st.session_state.selected_items = []

        
    for item in st.session_state.table_of_contents:
        # for title, content in item.items():
        if col2.checkbox(item):
            if title not in st.session_state.selected_items:
                st.session_state.selected_items.append(item)
