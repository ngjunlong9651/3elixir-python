import requests
import os
import logging
from dotenv import load_dotenv
# Load environment variables
load_dotenv()


def get_orders():
    prod_url = os.getenv("PROD_URL")
    endpoint = f"{prod_url}/api/orders"
    
    # Define the parameters
    params = {
        'sort[0]': 'fulfilmentEnd:asc'
    }
    
    # Optionally, add headers if required by the API
    headers = {
        'Authorization': 'Bearer 7f810b1f34e559630935c742aafe7c23c3ade7f8789cdbffd4b06236585d09dfe5107e63243cc22d27a1e2d98b2536d2150058a4969bc684bfafefd234053c374c4bb8562f421e5bb83b4f1367abe1566ae61eed0f0c822a08180ce35aa03211a7eb32be926cf7dd6fa7a4fcb34830850b5af12faf1c9200179031014a1b9214',  # Replace with your actual token if required
        'Content-Type': 'application/json'
    }
    
    try:
        # Make the GET request
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()  # Parse the JSON response
        print(data)  # Process the data as needed
    except requests.exceptions.RequestException as e:
        print(f"Error during API call: {e}")

# Call the function to test it
get_orders()
