import requests
import streamlit as st
import os

# Define the API endpoint URL with a placeholder for the search term
API_URL = 'https://beta.api.oemsecrets.com/partsearch?searchTerm={}&apiKey={}'

# Get the API key from the environment variable
API_KEY = os.getenv('API_KEY')

# Define a list of items to search for
items = ['2 gang switch', 'single switch', 'three gang switch']


# Define a function to send a request to the API and display the response
def search_item(item):
    url = API_URL.format(item.replace(' ', '%20'), API_KEY)
    response = requests.get(url)
    data = response.json()
    for stock_item in data['stock']:
        for currency, prices in stock_item['prices'].items():
            for price in prices:
                if price['unit_break'] == '1':
                    unit_price = price['unit_price']
                    st.write(f"The unit price for {item} is {unit_price} {currency}.")

# Create a Streamlit app with a loop that displays a button for each item in the list
st.title('Part Search App')
if st.button('Search'):
    for item in items:
        st.write(f'Searching for {item}...')
        
            search_item(item)
    st.stop()
