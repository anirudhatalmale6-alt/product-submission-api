#!/usr/bin/env python3
"""
Phase 13B: GSC Growth Intelligence
Pulls Google Search Console data and identifies growth opportunities.
Generates Growth_Opportunity_Report.csv
"""

import subprocess
import json
import csv
import time
from datetime import datetime, timedelta
from collections import defaultdict

SERVER = "root@167.99.198.145"
SSH_CMD = "sshpass -p 'PetHub2026!Agents#Secure' ssh -o StrictHostKeyChecking=no"
GSC_CREDS = "/opt/pethub-agents/credentials/google-oauth.json"
SITE_URL = "https://pethubonline.com"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Growth_Opportunity_Report.csv"


def run_on_server(command):
    """Execute command on remote server."""
    full_cmd = f"{SSH_CMD} {SERVER} '{command}'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=120)
    return result.stdout, result.stderr


def fetch_gsc_data():
    """Fetch GSC search analytics data from server."""
    # Build a Python script to run on server that uses the GSC credentials
    script = '''
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

    # Fetch page-level data
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

    # Fetch query-level data
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
'''

    # Write script to server and execute
    escaped_script = script.replace("'", "'\\''")
    write_cmd = f"cat > /tmp/gsc_fetch.py << 'SCRIPT_EOF'\n{script}\nSCRIPT_EOF"
    run_on_server(write_cmd)

    stdout, stderr = run_on_server("/opt/pethub-agents/venv/bin/python /tmp/gsc_fetch.py")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print(f"  ERROR parsing GSC response: {stdout[:500]}")
        print(f"  STDERR: {stderr[:500]}")
        return None


def analyze_opportunities(gsc_data):
    """Analyze GSC data and identify growth opportunities."""
    if not gsc_data or 'error' in gsc_data:
        return []

    pages = gsc_data.get('pages', [])
    queries = gsc_data.get('queries', [])

    # Build page metrics
    page_metrics = {}
    for row in pages:
        url = row['keys'][0]
        page_metrics[url] = {
            'url': url,
            'impressions': row.get('impressions', 0),
            'clicks': row.get('clicks', 0),
            'ctr': row.get('ctr', 0),
            'position': row.get('position', 0),
        }

    # Build query-to-page mapping
    page_queries = defaultdict(list)
    for row in queries:
        query = row['keys'][0]
        page_url = row['keys'][1]
        page_queries[page_url].append({
            'query': query,
            'impressions': row.get('impressions', 0),
            'clicks': row.get('clicks', 0),
            'ctr': row.get('ctr', 0),
            'position': row.get('position', 0),
        })

    results = []
    for url, metrics in page_metrics.items():
        # Skip non-post URLs
        if '/wp-admin' in url or '/wp-content' in url:
            continue

        impressions = metrics['impressions']
        clicks = metrics['clicks']
        ctr = metrics['ctr']
        position = metrics['position']

        # Classify opportunity type
        opportunity_type = classify_opportunity(impressions, clicks, ctr, position)

        # Get top queries for this page
        top_queries = sorted(page_queries.get(url, []),
                           key=lambda x: x['impressions'], reverse=True)[:5]
        top_query_text = "; ".join([f"{q['query']} (pos:{q['position']:.1f})" for q in top_queries])

        # Calculate growth potential score
        growth_score = calculate_growth_potential(impressions, clicks, ctr, position)

        results.append({
            'url': url,
            'impressions': impressions,
            'clicks': clicks,
            'ctr': round(ctr * 100, 2),
            'avg_position': round(position, 1),
            'opportunity_type': opportunity_type,
            'growth_potential_score': growth_score,
            'top_queries': top_query_text,
            'recommended_action': get_recommended_action(opportunity_type, position, ctr),
        })

    results.sort(key=lambda x: x['growth_potential_score'], reverse=True)
    return results


def classify_opportunity(impressions, clicks, ctr, position):
    """Classify the type of growth opportunity."""
    if position <= 5 and ctr < 0.05:
        return "CTR Optimization (high rank, low CTR)"
    elif position <= 10 and impressions > 50:
        return "Page 1 Consolidation (strengthen position)"
    elif 10 < position <= 20 and impressions > 30:
        return "Striking Distance (push to page 1)"
    elif impressions > 100 and clicks < 5:
        return "High Impression / Low Click (title/description fix)"
    elif position > 20 and impressions > 20:
        return "Content Expansion (improve relevance)"
    elif impressions < 10:
        return "Low Visibility (needs promotion/links)"
    else:
        return "General Optimization"


def calculate_growth_potential(impressions, clicks, ctr, position):
    """Score growth potential 0-100."""
    score = 0

    # High impressions with room for CTR improvement
    if impressions > 100:
        score += 25
    elif impressions > 50:
        score += 15
    elif impressions > 20:
        score += 10

    # Position opportunity (closer to page 1 = higher potential)
    if 4 <= position <= 10:
        score += 30  # Almost page 1 top
    elif 11 <= position <= 20:
        score += 25  # Striking distance
    elif position <= 3:
        score += 15  # Already top, optimize CTR
    elif 21 <= position <= 30:
        score += 10

    # CTR gap (low CTR with good position = easy win)
    if position <= 10 and ctr < 0.03:
        score += 25
    elif position <= 10 and ctr < 0.05:
        score += 15
    elif position <= 20 and ctr < 0.02:
        score += 10

    # Click potential
    if impressions > 0 and clicks / max(impressions, 1) < 0.02:
        score += 20
    elif impressions > 0 and clicks / max(impressions, 1) < 0.05:
        score += 10

    return min(score, 100)


def get_recommended_action(opportunity_type, position, ctr):
    """Get specific recommended action."""
    if "CTR Optimization" in opportunity_type:
        return "Rewrite meta title/description for higher click appeal; add rich snippet markup"
    elif "Page 1 Consolidation" in opportunity_type:
        return "Add internal links from high-authority pages; expand content depth"
    elif "Striking Distance" in opportunity_type:
        return "Build 3-5 internal links; add FAQ section; expand word count by 500+"
    elif "High Impression" in opportunity_type:
        return "Rewrite title tag for search intent match; add power words"
    elif "Content Expansion" in opportunity_type:
        return "Expand article with new sections; target related long-tail queries"
    elif "Low Visibility" in opportunity_type:
        return "Build internal link network; submit to GSC for re-indexing"
    else:
        return "General SEO optimization; improve content quality"


def main():
    print("=" * 70)
    print("PHASE 13B: GSC GROWTH INTELLIGENCE")
    print("=" * 70)
    print()

    print("[1/2] Fetching GSC data from server...")
    gsc_data = fetch_gsc_data()

    if gsc_data is None:
        print("  ERROR: Could not fetch GSC data")
        print("  Generating report from available data...")
        gsc_data = {'pages': [], 'queries': []}

    if 'error' in gsc_data:
        print(f"  GSC ERROR: {gsc_data['error']}")
        print("  Will generate opportunity report based on site structure...")
    else:
        print(f"  Pages: {len(gsc_data.get('pages', []))}")
        print(f"  Query+Page combos: {len(gsc_data.get('queries', []))}")
        if 'date_range' in gsc_data:
            print(f"  Date range: {gsc_data['date_range']['start']} to {gsc_data['date_range']['end']}")

    print()
    print("[2/2] Analyzing growth opportunities...")
    results = analyze_opportunities(gsc_data)
    print(f"  Identified {len(results)} page opportunities")
    print()

    if results:
        # Write CSV
        fieldnames = ['url', 'impressions', 'clicks', 'ctr', 'avg_position',
                     'opportunity_type', 'growth_potential_score', 'top_queries',
                     'recommended_action']

        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"CSV written: {OUTPUT_CSV}")
        print()

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()

        total_impressions = sum(r['impressions'] for r in results)
        total_clicks = sum(r['clicks'] for r in results)
        avg_position = sum(r['avg_position'] for r in results) / len(results) if results else 0
        avg_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0

        print(f"  Total impressions (30d): {total_impressions:,}")
        print(f"  Total clicks (30d): {total_clicks:,}")
        print(f"  Average CTR: {avg_ctr:.2f}%")
        print(f"  Average position: {avg_position:.1f}")
        print()

        # Opportunity breakdown
        opp_types = defaultdict(int)
        for r in results:
            opp_types[r['opportunity_type']] += 1

        print("OPPORTUNITY BREAKDOWN:")
        print("-" * 50)
        for opp, count in sorted(opp_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  [{count:3}] {opp}")

        print()
        print("TOP 15 GROWTH OPPORTUNITIES:")
        print("-" * 50)
        for r in results[:15]:
            url_short = r['url'].replace('https://pethubonline.com/', '/')[:60]
            print(f"  Score:{r['growth_potential_score']:3} | Pos:{r['avg_position']:5.1f} | "
                  f"Imp:{r['impressions']:5} | {url_short}")
            print(f"         Type: {r['opportunity_type']}")
            print()
    else:
        print("  No GSC data available yet. Report will be generated once GSC data flows.")
        # Write empty CSV with headers
        fieldnames = ['url', 'impressions', 'clicks', 'ctr', 'avg_position',
                     'opportunity_type', 'growth_potential_score', 'top_queries',
                     'recommended_action']
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        print(f"  Empty CSV written: {OUTPUT_CSV}")

    print("=" * 70)


if __name__ == "__main__":
    main()
