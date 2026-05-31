#!/bin/bash
# Phase 16 Dashboard Deployment Script
# Deploys 10 growth/visibility dashboards to PetHub Operations Centre

set -e

SERVER="root@167.99.198.145"
SSHCMD="sshpass -p 'PetHub2026!Agents#Secure' ssh -o StrictHostKeyChecking=no"
SCPCMD="sshpass -p 'PetHub2026!Agents#Secure' scp -o StrictHostKeyChecking=no"
LOCAL_DIR="/var/lib/freelancer/projects/40416335"
REMOTE_DIR="/opt/pethub-agents/manager-agent/static"

DASHBOARDS=(
  "gsc_growth_dashboard.html"
  "standards_validator_dashboard.html"
  "social_readiness_dashboard.html"
  "ai_citation_dashboard.html"
  "backlink_dashboard.html"
  "competitor_dashboard.html"
  "revenue_opportunity_dashboard.html"
  "visibility_agent_dashboard.html"
  "authority_agent_dashboard.html"
  "qa_regression_dashboard.html"
  "subscriber_dashboard.html"
)

echo "=== Phase 16 Dashboard Deployment ==="
echo ""

# Step 1: Copy all dashboard files
echo "[1/3] Copying dashboard files to server..."
for f in "${DASHBOARDS[@]}"; do
  if [ -f "${LOCAL_DIR}/${f}" ]; then
    echo "  Copying ${f}..."
    $SCPCMD "${LOCAL_DIR}/${f}" "${SERVER}:${REMOTE_DIR}/${f}"
  else
    echo "  SKIP: ${f} not found locally"
  fi
done

# Step 2: Add routes to main.py
echo ""
echo "[2/3] Adding routes to manager main.py..."

$SSHCMD $SERVER 'cat >> /opt/pethub-agents/manager-agent/main.py << '"'"'ROUTES_EOF'"'"'

# ── Phase 16 Growth & Visibility Dashboards ──

@app.get("/gsc-growth", response_class=HTMLResponse)
def gsc_growth_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "gsc_growth_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/standards-validator", response_class=HTMLResponse)
def standards_validator_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "standards_validator_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/social-readiness", response_class=HTMLResponse)
def social_readiness_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "social_readiness_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/ai-citation", response_class=HTMLResponse)
def ai_citation_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "ai_citation_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/backlinks", response_class=HTMLResponse)
def backlink_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "backlink_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/competitors", response_class=HTMLResponse)
def competitor_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "competitor_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/revenue", response_class=HTMLResponse)
def revenue_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "revenue_opportunity_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/visibility", response_class=HTMLResponse)
def visibility_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "visibility_agent_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/authority", response_class=HTMLResponse)
def authority_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "authority_agent_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/qa-regression", response_class=HTMLResponse)
def qa_regression_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "qa_regression_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())

@app.get("/subscribers", response_class=HTMLResponse)
def subscriber_dashboard_page():
    path = os.path.join(os.path.dirname(__file__), "static", "subscriber_dashboard.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())
ROUTES_EOF'

# Step 3: Restart manager
echo ""
echo "[3/3] Restarting manager agent..."
$SSHCMD $SERVER 'systemctl restart pethub-manager'
sleep 5
$SSHCMD $SERVER 'systemctl is-active pethub-manager'

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Dashboard URLs (port 8100):"
echo "  /gsc-growth           - GSC Growth Intelligence"
echo "  /standards-validator   - Standards Validator Status"
echo "  /social-readiness      - Social Distribution Engine"
echo "  /ai-citation           - AI Citation Monitor"
echo "  /backlinks             - Backlink Acquisition"
echo "  /competitors           - Competitor Displacement"
echo "  /revenue               - Revenue Opportunity Engine"
echo "  /visibility            - Visibility Agent Status"
echo "  /authority             - Authority Agent Status"
echo "  /qa-regression         - QA Regression Engine"
echo "  /subscribers           - Subscriber/MailerLite Dashboard"
