#!/usr/bin/env python3
"""GSC data fetch script - runs on server with Google credentials."""
import json
import os
from datetime import datetime, timedelta

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
except ImportError:
    print(json.dumps({"error": "google-api-python-client not installed"}))
    exit(1)

CREDS_FILE = "/opt/pethub-agents/credentials/google-oauth.json"
SITE_URL = "https://pethubonline.com"

try:
    with open(CREDS_FILE, 'r') as f:
        creds_data = json.load(f)

    creds = Credentials(
        token=creds_data.get('token'),
        refresh_token=creds_data.get('refresh_token'),
        token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=creds_data.get('client_id'),
        client_secret=creds_data.get('client_secret'),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        creds_data['token'] = creds.token
        with open(CREDS_FILE, 'w') as f:
            json.dump(creds_data, f)

    service = build('searchconsole', 'v1', credentials=creds)

    end_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    request_body = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['page'],
        'rowLimit': 500,
        'startRow': 0
    }

    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=request_body
    ).execute()

    pages = response.get('rows', [])

    request_body_queries = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query', 'page'],
        'rowLimit': 1000,
        'startRow': 0
    }

    response_queries = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=request_body_queries
    ).execute()

    queries = response_queries.get('rows', [])

    result = {
        'pages': pages,
        'queries': queries,
        'date_range': {'start': start_date, 'end': end_date}
    }

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
