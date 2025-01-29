import requests
from django.conf import settings

def validate_email_with_abstract_api(email):
    """
    Validate email using Abstract API.
    """
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={settings.ABSTRACT_API_KEY}&email={email}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("is_valid_format", {}).get("value") and data.get("deliverability") == "DELIVERABLE":
            return True
    return False
