import requests

def fetch_company_details(company_data):
    """Fetch and format company details using FMCSA API."""
    try:
        company_name = company_data.get('carrier', {}).get('legalName', 'Unknown Company')
        safety_rating = company_data.get('safetyRating', 'No safety rating available')
        address = company_data.get('address', 'No address available')

        details = f"Company: {company_name}\nSafety Rating: {safety_rating}\nAddress: {address}"
        return details
    except Exception as e:
        return f"An error occurred while fetching company details: {e}"
