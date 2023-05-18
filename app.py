import streamlit as st
import requests
from llama_index import GPTSimpleVectorIndex, Document, SimpleDirectoryReader, QuestionAnswerPrompt, LLMPredictor, ServiceContext
import os
import openai 
import json
from langchain import OpenAI
from collections import Counter
import PyPDF2
from pathlib import Path
from llama_index import download_loader

# os.system("playwright install")
# BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
# loader = BeautifulSoupWebReader()

st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="collapsed")
openai.api_key = os.getenv("API_KEY")
st.title("QuickBOM.ai")
st.caption("AI-powered BOM creation made easy")

if "table_of_contents" not in st.session_state:
    st.session_state.table_of_contents = []

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

# define your own api key and IP
headers = {
    'X-Originating-IP': '175.157.190.21',
    'callinfo.apiKey': 'dp55nxup84tuf2yd7ztb9kay'
}

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

def make_request(keyword):
    params = {
        'versionNumber': '1.2',
        'term': f"any:{keyword}",
        'storeInfo.id': 'uk.farnell.com',
        'resultsSettings.offset': '0',
        'resultsSettings.numberOfResults': '1',
        'resultsSettings.refinements.filters': 'rohsCompliant,inStock',
        'resultsSettings.responseGroup': 'large',
        'callInfo.omitXmlSchema': 'false',
        'callInfo.responseDataFormat': 'json'
    }
    response = requests.get('https://api.element14.com/catalog/products', headers=headers, params=params)
    return response

def display_product_info(response):
    data = response.json()
    products = data['keywordSearchReturn']['products']
    for product in products:
        st.subheader(product['displayName'])
        st.write(f'SKU: {product["sku"]}')
        st.write(f'Product Status: {product["productStatus"]}')
        st.write(f'ROHS Status Code: {product["rohsStatusCode"]}')
        st.write(f'Pack Size: {product["packSize"]}')
        st.write(f'Unit of Measure: {product["unitOfMeasure"]}')
        st.image(f'https://uk.farnell.com{product["image"]["baseName"]}')
        st.subheader('Datasheets:')
        for datasheet in product['datasheets']:
            st.write(f'Description: {datasheet["description"]}')
            st.write(f'URL: {datasheet["url"]}')
        st.subheader('Prices:')
        for price in product['prices']:
            st.write(f'From: {price["from"]}, To: {price["to"]}, Cost: {price["cost"]}')


col1, col2, col3, col4 = st.tabs(["__Upload pdf__", "__Extract Components__", "__Fetch Pricing__", "__Generate BOM__"])

uploaded_file = col1.file_uploader("Upload PDF", type="pdf")
if uploaded_file is not None:
    save_uploaded_file(uploaded_file)
    col1.success("It would take a while to index the books, please wait..!")
    pdf_filename = uploaded_file.name
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    index = GPTSimpleVectorIndex.from_documents(documents)
    index.save_to_disk(os.path.join(DATA_DIR, os.path.splitext(pdf_filename)[0] + ".json"))
    col1.success("Index created successfully!")

index_filenames = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

if index_filenames:
    index_file = col2.selectbox("Select an index file to load:", index_filenames,label_visibility="collapsed")
    index_path = os.path.join(DATA_DIR, index_file)
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=3000))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    index = GPTSimpleVectorIndex.load_from_disk(index_path,service_context=service_context)
else:
    col2.warning("No index files found. Please upload a PDF file to create an index.")

toc = col2.button("Get Components")
if toc:
    toc_res = index.query(f" list out the electrical components and their quantities with their models used in the document, in a json format (Response output should be valid JSON string) ")
    str_toc = str(toc_res)
    json_output = json.loads(str_toc)
    table_of_contents = json_output
    st.session_state.table_of_contents = table_of_contents

if "selected_items" not in st.session_state:
    st.session_state.selected_items = []

for item in st.session_state.table_of_contents:
    if col2.checkbox(item):
        st.session_state.selected_items.append(item)

counted_list = Counter(st.session_state.selected_items)

for component in counted_list.keys():
    response = make_request(component)
    if response.status_code == 200:
        display_product_info(response)
    else:
        st.error(f'Request for {component} failed with status code {response.status_code}')