import streamlit as st
import requests

st.title('Product Search')

# Define parameters
params = {
    'versionNumber': '1.2',
    'term': 'any:fuse',
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
response = requests.get('https://api.element14.com/catalog/products', headers=headers, params=params)

# Check the response status
if response.status_code == 200:
    # Load the data into a dataframe
    data = response.json()
    products = data['keywordSearchReturn']['products']

    # Display each product
    for product in products:
        st.subheader(product['displayName'])
        st.text(f'SKU: {product["sku"]}')
        st.text(f'Product Status: {product["productStatus"]}')
        st.text(f'ROHS Status Code: {product["rohsStatusCode"]}')
        st.text(f'Pack Size: {product["packSize"]}')
        st.text(f'Unit of Measure: {product["unitOfMeasure"]}')
        st.image(f'https://uk.farnell.com{product["image"]["baseName"]}')

        st.subheader('Datasheets:')
        for datasheet in product['datasheets']:
            st.text(f'Description: {datasheet["description"]}')
            st.text(f'URL: {datasheet["url"]}')

        st.subheader('Prices:')
        for price in product['prices']:
            st.text(f'From: {price["from"]}, To: {price["to"]}, Cost: {price["cost"]}')

else:
    st.error(f'Request failed with status code {response.status_code}')
