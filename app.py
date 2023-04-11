import streamlit as st
from llama_index import GPTSimpleVectorIndex, Document, SimpleDirectoryReader, QuestionAnswerPrompt, LLMPredictor, ServiceContext
import os
import openai 
import json

from langchain import OpenAI
from collections import Counter
import PyPDF2
from pathlib import Path
from llama_index import download_loader
# import os
os.system("playwright install")

# AudioTranscriber = download_loader("AudioTranscriber")
BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")

loader = BeautifulSoupWebReader()


st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="collapsed")
openai.api_key = os.getenv("API_KEY")
st.title("QuickBOM.ai")
st.caption("AI-powered BOM creation made easy")

if "table_of_contents" not in st.session_state:
    st.session_state.table_of_contents = []


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


col1, col2, col3, col4 = st.tabs(["__Upload pdf__", "__Extract Components__", "__Fetch Pricing__", "__Generate BOM__"])

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
    # col2.write(json_output)
    table_of_contents = json_output
    # if "table_of_contents" not in st.session_state:
    st.session_state.table_of_contents = table_of_contents


if "selected_items" not in st.session_state:
    st.session_state.selected_items = []

    
for item in st.session_state.table_of_contents:
    # for title, content in item.items():
    if col2.checkbox(item):
        # if title not in st.session_state.selected_items:
        st.session_state.selected_items.append(item)

# col3.write(st.session_state.selected_items)

counted_list = Counter(st.session_state.selected_items)

url_input = col3.text_input("Pricing source")
scrape_url = col3.button("Fetch Pricing")


if scrape_url:
    
    # documents = loader.load_data(urls=["https://us.rs-online.com/connectors/","https://us.rs-online.com/electronic-components/","https://us.rs-online.com/enclosures-racks-cabinets/","https://us.rs-online.com/facilities-cleaning-maintenance/","https://us.rs-online.com/fans-thermal-management/","https://us.rs-online.com/industrial-controls/","https://us.rs-online.com/industrial-data-communications/","https://us.rs-online.com/lighting-indication/","https://us.rs-online.com/motors-motor-controls/","https://us.rs-online.com/plcs-hmis/","https://us.rs-online.com/pneumatics-fluid-control/","https://us.rs-online.com/power-products/","https://us.rs-online.com/relays/","https://us.rs-online.com/sensors/","https://us.rs-online.com/test-measurement/","https://us.rs-online.com/tools-hardware/","https://us.rs-online.com/wire-cable/"])
    # st.success(f"URL content scraped successfully!")
    documents = loader.load_data(urls=[url_input])
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=1024))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    scrapeIndex = GPTSimpleVectorIndex.from_documents(documents, service_context=service_context)
    st.session_state.scrapeIndex = scrapeIndex

    pric = st.session_state.scrapeIndex.query("Fetch the prices only of the following items, " +str(counted_list.keys()) + ", dont include anything else in the output, output should be in json format, where key and values should e enclosed in double quotes  ")
    # st.write(pric.response)
    jso = json.loads(str(pric.response))
#     st.write(jso)


# # url_input = col3.text_input("Pricing source")
# # bat = st.button("Query")

# # if bat:
# #     rep = st.session_state.scrapeIndex.query(url_input)
# #     st.write(rep.response)
# st.write(counted_list.keys())
# st.write(jso.values())


# Create a table with two columns, one for the item name and the other for the number of times it appears
    col3.table({"Item": list(counted_list.keys()), "Price": list(jso.values()), "Count": list(counted_list.values())})