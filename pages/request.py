import streamlit as st
import requests
import fitz
import os
import base64
import openai 
import json

openai.api_key = os.getenv("OPENAI_API_KEY")




def callAPI(image):
    vision_url = 'https://vision.googleapis.com/v1/images:annotate?key='

    # Your Google Cloud Platform (GCP) API KEY. Generate one on cloud.google.com
    api_key = os.environ["GCP_KEY"] 
    # Load your image as a base64 encoded string

    # Generate a post request for GCP vision Annotation
    json_data= {
        'requests': [
            {
                'image':{
                    'content': image.decode('utf-8')
                },
                'features':[
                    {
                        'type':'TEXT_DETECTION',
                        'maxResults':5
                    }
                ]
            }
        ]
    }

    # Handle the API request
    responses = requests.post(vision_url+api_key, json=json_data)

    # Read the response in json format

    return responses.json()


def encode_image(image):
    with open(image, "rb") as img_file:
        return base64.b64encode(img_file.read())



def generate_persona(source):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=source,
        temperature=0.56,
        max_tokens=2066,
        top_p=1,
        frequency_penalty=0.35,
        presence_penalty=0
    )
    return response.choices[0].text

st.title('Product Search')

uploaded_file = st.file_uploader("Upload a Diagram as a PDF file", type="pdf")


if uploaded_file is not None:
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    with fitz.open(uploaded_file.name) as doc:
        for page in doc:  # iterate through the pages
            pix = page.get_pixmap()  # render page to an image
            img_path = f"pages/page-{page.number}.png"
            pix.save(img_path)  # save image
            
            b64_image = encode_image(img_path)
            response = callAPI(b64_image)
            info = response['responses'][0]['textAnnotations'][0]['description']
            if "info" not in st.session_state:
                st.session_state.info = info

if st.button("Get List"):   
    with st.spinner("Please wait till the AI engine extracts the part list"):
        propt = f"Extract the list of purchaseable electrical product parts from the following description into a valid JSON string: {st.session_state.info}\n (list key of the JSON string should be named electrical_products, and the list of electrical_products should contain only valid electrical parts/products)"
        liststr = generate_persona(propt)
        st.write(liststr)
    try:
        json_str = json.loads(liststr)
        if "json_str" not in st.session_state:
            st.session_state.json_str = json_str
    except json.JSONDecodeError as e:
        st.info("Network error Please retry once more")

    # st.write(json_str)
try:
    lis = st.session_state.json_str["electrical_products"]

    prod = st.selectbox("Select a Part", lis)


    keyword = str(prod)
    # Define parameters
    params = {
        'versionNumber': '1.2',
        'term': f"any:{keyword}",
        'storeInfo.id': 'uk.farnell.com',
        'resultsSettings.offset': '0',
        'resultsSettings.numberOfResults': '1',
        'resultsSettings.refinements.filters': 'rohsCompliant,inStock',
        'resultsSettings.responseGroup': 'large',
        'callInfo.omitXmlSchema': 'false',
        'callInfo.responseDataFormat': 'json',
        'callinfo.apiKey': 'dp55nxup84tuf2yd7ztb9kay' # please replace it with your own api key
    }

    headers = {
        'X-Originating-IP': '175.157.190.21' # replace it with your own IP
    }

    # Make the API request
    if st.button("make request"):
        respons = requests.get('https://api.element14.com/catalog/products', headers=headers, params=params)

except (AttributeError) as e:
    st.info("Step 1: Upload an Electrical Diagram and click Get List")

try:
    # Check the respons status
    if respons.status_code == 200:
        # Load the data into a dataframe
        data = respons.json()
        products = data['keywordSearchReturn']['products']

        # Display each product
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

    else:
        st.error(f'Request failed with status code {respons.status_code}')
except (NameError) as e:
    st.info("Step 2: Select a part Number and click make request")