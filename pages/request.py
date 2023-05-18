import streamlit as st
import requests
import fitz
import os
import base64





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
        return base64.b64encode(img_file.read()).decode('utf-8')


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
            
            st.write(response)



keyword = st.text_input("Input Search Keyword")
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
    response = requests.get('https://api.element14.com/catalog/products', headers=headers, params=params)


try:
    # Check the response status
    if response.status_code == 200:
        # Load the data into a dataframe
        data = response.json()
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
        st.error(f'Request failed with status code {response.status_code}')
except (NameError) as e:
    st.info("Input search keyword and click make request")