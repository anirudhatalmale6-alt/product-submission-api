#!/bin/bash
set -e

GITHUB_RAW="https://raw.githubusercontent.com/anirudhatalmale6-alt/product-submission-api/main"
SHARED="/opt/pethub-agents/shared"
MANAGER="/opt/pethub-agents/manager-agent"

echo "=== Deploying Mission Control ==="

echo "[1/5] Downloading mission_control.py..."
curl -sL "$GITHUB_RAW/mission_control.py" -o "$SHARED/mission_control.py"

echo "[2/5] Downloading mission_control_routes.py..."
curl -sL "$GITHUB_RAW/mission_control_routes.py" -o "$SHARED/mission_control_routes.py"

echo "[3/5] Downloading mission_control_dashboard.html..."
curl -sL "$GITHUB_RAW/mission_control_dashboard.html" -o "$MANAGER/mission_control_dashboard.html"

echo "[4/5] Adding Mission Control routes to main.py..."
if ! grep -q "mission_control_routes" "$MANAGER/main.py"; then
    cat >> "$MANAGER/main.py" << 'PYEOF'

# ── Mission Control Integration ─────────────────────────────
from mission_control_routes import router as mission_control_router
app.include_router(mission_control_router)

@app.get("/mission-control", response_class=HTMLResponse)
def mission_control_page():
    p = os.path.join(os.path.dirname(__file__), "mission_control_dashboard.html")
    with open(p) as f:
        return HTMLResponse(content=f.read())
PYEOF
    echo "  -> Routes added to main.py"
else
    echo "  -> Routes already present in main.py"
fi

echo "[5/5] Adding Mission Control tab to Operations Centre..."
if ! grep -q "mission-control" "$MANAGER/operations_centre.html"; then
    sed -i 's|<!-- TAB_INSERT_POINT -->|<button class="ops-tab" data-view="mission-control">Mission Control</button>\n<!-- TAB_INSERT_POINT -->|' "$MANAGER/operations_centre.html" 2>/dev/null
    sed -i "s|// VIEW_MAP_INSERT_POINT|'mission-control': '/agents/manager/mission-control',\n// VIEW_MAP_INSERT_POINT|" "$MANAGER/operations_centre.html" 2>/dev/null
    echo "  -> Tab added to Operations Centre"
else
    echo "  -> Tab already present in Operations Centre"
fi

echo "=== Restarting pethub-manager ==="
systemctl restart pethub-manager
sleep 3
systemctl status pethub-manager --no-pager | head -5

echo "=== Deployment Complete ==="
echo "Mission Control is now available at /agents/manager/mission-control"
echo "Operations Centre tab has been added"
