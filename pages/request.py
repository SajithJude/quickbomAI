import streamlit as st
import requests

st.title('Product Search')


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
    # 'callinfo.apiKey': 'dp55nxup84tuf2yd7ztb9kay' # please replace it with your own api key
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