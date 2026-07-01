import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from api.database import migrate
from api.main import app
from core import AgentSyncManager
from tool_registry import McpEngine, McpTool
from tool_registry.db import clear_server_tools, get_server, insert_tools, update_server


@pytest.fixture
def billing_client(tmp_path, monkeypatch):
    db_path = tmp_path / "billing-demo.db"
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))
    migrate.run_migrations()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, session_id, workspace_name, local_path,
                enabled_tools, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "billing-ws",
                "billing-session",
                "Billing Demo Workspace",
                str(workspace_dir),
                json.dumps([]),
                1000,
                1000,
            ),
        )
        conn.commit()

    with TestClient(app) as client:
        engine = McpEngine(str(db_path))

        async def fake_start_server(server_id: str, workspace_dir=None):
            clear_server_tools(str(db_path), server_id)
            now = int(time.time())
            insert_tools(
                str(db_path),
                [
                    McpTool(
                        tool_id=f"{server_id}:subscription_status",
                        server_id=server_id,
                        name="subscription_status",
                        description="Return mocked subscription status.",
                        input_schema={"type": "object", "properties": {}},
                        is_enabled=True,
                        created_at=now,
                    )
                ],
            )
            return update_server(
                str(db_path),
                server_id,
                {
                    "is_active": True,
                    "status": "active",
                    "error_message": None,
                    "updated_at": now,
                },
            )

        engine.start_server = fake_start_server
        client.app.state.mcp_engine = engine
        client.app.state.agent_sync_manager = AgentSyncManager(str(db_path))
        yield client, str(db_path)


def test_mock_stripe_checkout_unlocks_paid_mcp_for_gateway(billing_client):
    client, db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID

    products_response = client.get("/api/billing/mcp-products")

    assert products_response.status_code == 200
    product = products_response.json()["products"][0]
    assert product["server_id"] == server_id
    assert product["requires_payment"] is True
    assert product["install_state"] == "locked"

    subscriptions_before = client.get("/api/billing/subscriptions")
    assert subscriptions_before.status_code == 200
    assert subscriptions_before.json()["subscriptions"] == []

    blocked_install = client.post(f"/api/mcp/servers/{server_id}/install")
    assert blocked_install.status_code == 400
    assert "Subscription required" in blocked_install.json().get("message", "")

    checkout_response = client.post(
        f"/api/billing/mcp-products/{server_id}/checkout",
        json={"session_id": "billing-session", "customer_id": "demo-customer"},
    )

    assert checkout_response.status_code == 201
    checkout = checkout_response.json()
    assert checkout["status"] == "pending"
    assert checkout["checkout_url"].startswith("https://checkout.stripe.test/")

    gateway_before = client.get("/api/gateway/tools").json()["tools"]
    assert all(not tool["name"].startswith("premiumopsintelligencemcp__") for tool in gateway_before)

    complete_response = client.post(
        f"/api/billing/purchases/{checkout['purchase_id']}/mock-complete"
    )

    assert complete_response.status_code == 200
    purchase = complete_response.json()
    assert purchase["status"] == "provisioned"
    assert purchase["provisioned"] is True

    server = get_server(db_path, server_id)
    assert server is not None
    assert server.is_installed is True
    assert server.status == "active"
    assert server.installability_tier == "tested"
    assert server.install_blocked_reason is None

    with sqlite3.connect(db_path) as conn:
        enabled_tools = conn.execute(
            "SELECT enabled_tools FROM engineering_workspaces WHERE session_id = ?",
            ("billing-session",),
        ).fetchone()[0]
    assert server_id in json.loads(enabled_tools)

    gateway_after = client.get("/api/gateway/tools").json()["tools"]
    assert any(
        tool["name"] == "premiumopsintelligencemcp__subscription_status"
        for tool in gateway_after
    )

    subscriptions_after = client.get("/api/billing/subscriptions")
    assert subscriptions_after.status_code == 200
    subscription = subscriptions_after.json()["subscriptions"][0]
    assert subscription["server_id"] == server_id
    assert subscription["server_name"] == "Premium Ops Intelligence MCP"
    assert subscription["amount_cents"] == 1900
    assert subscription["currency"] == "usd"
    assert subscription["payment_date"] > 0
    assert subscription["mcp_enabled"] is True
    assert subscription["mcp_status"] == "enabled"


def test_mock_stripe_webhook_can_complete_pending_checkout(billing_client):
    client, _db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID

    checkout = client.post(
        f"/api/billing/mcp-products/{server_id}/checkout",
        json={"session_id": "billing-session"},
    ).json()

    webhook_response = client.post(
        "/api/billing/webhooks/stripe/mock",
        json={
            "event_type": "checkout.session.completed",
            "stripe_session_id": checkout["stripe_session_id"],
        },
    )

    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "provisioned"


def test_browser_get_checkout_creates_mock_checkout(billing_client):
    client, _db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID

    response = client.get(
        f"/api/billing/mcp-products/{server_id}/checkout",
        params={"session_id": "billing-session"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["checkout_url"].startswith("https://checkout.stripe.test/")
    assert "browser GET" in data["message"]
    assert data["hermes_stripe_mock"]["browser_mock_complete_path"].endswith(
        f"/api/billing/purchases/{data['purchase_id']}/mock-complete"
    )


def test_browser_get_mock_complete_provisions_paid_mcp(billing_client):
    client, _db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID

    checkout = client.get(
        f"/api/billing/mcp-products/{server_id}/checkout",
        params={"session_id": "billing-session"},
    ).json()

    response = client.get(
        f"/api/billing/purchases/{checkout['purchase_id']}/mock-complete"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "provisioned"
    assert "browser GET" in data["message"]


def test_browser_accept_html_checkout_renders_demo_page(billing_client):
    client, _db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID

    response = client.get(
        f"/api/billing/mcp-products/{server_id}/checkout",
        params={"session_id": "billing-session"},
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Stripe Billing Checkout" in response.text
    assert "Approve with Stripe Link" in response.text
    assert "$19.00 / month" in response.text
    assert "/api/billing/purchases/" in response.text
    assert "/complete?format=html" in response.text
    assert "mock" not in response.text.lower()
    assert "demo" not in response.text.lower()


def test_browser_accept_html_mock_complete_renders_success_page(billing_client):
    client, _db_path = billing_client
    server_id = migrate.PAID_DEMO_MCP_SERVER_ID
    checkout = client.get(
        f"/api/billing/mcp-products/{server_id}/checkout",
        params={"session_id": "billing-session"},
    ).json()

    response = client.get(
        f"/api/billing/purchases/{checkout['purchase_id']}/complete",
        headers={
            "Accept": "text/html",
            "Referer": "http://localhost:5188/tool-registry",
        },
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Stripe Payment Complete" in response.text
    assert "Premium Ops Intelligence MCP</strong> has been paid for and installed." in response.text
    assert "Back to Dashboard" in response.text
    assert 'href="http://localhost:5188/"' in response.text
    assert 'href="http://localhost:5188/tool-registry"' not in response.text
    assert "Tool Registry" not in response.text
    assert "mock" not in response.text.lower()
    assert "demo" not in response.text.lower()
