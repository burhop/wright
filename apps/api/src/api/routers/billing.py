import json
import os
import sqlite3
import time
import uuid
from html import escape
from typing import Any, Optional
from urllib.parse import urlparse

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from api.routers.mcp import get_mcp_engine
from api.services.hermes_sync import sync_mcp_server_to_hermes
from core.workspace import (
    get_gateway_workspace,
    get_workspace_by_session,
    get_workspace_enabled_tools,
    set_active_gateway_session,
    update_workspace_enabled_tools,
)
from tool_registry import McpEngine, McpServer, get_server, insert_server
from tool_registry.db import update_server

logger = structlog.get_logger(__name__)
router = APIRouter()

PAID_DEMO_SERVER_ID = "premium-ops-intelligence-mcp"
PAID_DEMO_PRICE_CENTS = 1900
PAID_DEMO_CURRENCY = "usd"
PAID_DEMO_INTERVAL = "month"


class CheckoutRequest(BaseModel):
    session_id: Optional[str] = None
    customer_id: str = "demo-builder"


class MockStripeWebhookRequest(BaseModel):
    event_type: str = "checkout.session.completed"
    purchase_id: Optional[str] = None
    stripe_session_id: Optional[str] = None
    server_id: Optional[str] = PAID_DEMO_SERVER_ID


class BillingProductResponse(BaseModel):
    server_id: str
    name: str
    description: str
    price_cents: int
    currency: str
    interval: str
    payment_mode: str
    requires_payment: bool
    purchased: bool
    install_state: str
    latest_purchase_status: Optional[str] = None
    checkout_url: Optional[str] = None


class BillingProductsListResponse(BaseModel):
    products: list[BillingProductResponse]


class BillingSubscriptionResponse(BaseModel):
    subscription_id: str
    server_id: str
    server_name: str
    customer_id: str
    session_id: Optional[str] = None
    amount_cents: int
    currency: str
    interval: str
    payment_date: int
    status: str
    mcp_enabled: bool
    mcp_status: str


class BillingSubscriptionsListResponse(BaseModel):
    subscriptions: list[BillingSubscriptionResponse]


class PurchaseResponse(BaseModel):
    purchase_id: str
    server_id: str
    server_name: str
    session_id: Optional[str]
    customer_id: str
    status: str
    checkout_url: str
    stripe_session_id: str
    amount_cents: int
    currency: str
    provisioned: bool
    message: str
    hermes_stripe_mock: dict[str, Any] = Field(default_factory=dict)


def _repo_dir() -> str:
    configured = os.getenv("WRIGHT_REPO_DIR")
    if configured:
        return configured
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, *[".."] * 5))


def _demo_server(now: Optional[int] = None) -> McpServer:
    timestamp = now or int(time.time())
    repo_dir = _repo_dir()
    return McpServer(
        server_id=PAID_DEMO_SERVER_ID,
        name="Premium Ops Intelligence MCP",
        type="stdio",
        command=[
            "uv",
            "run",
            "--project",
            repo_dir,
            "python",
            "-m",
            "tool_registry.paid_demo_mcp",
        ],
        is_active=False,
        is_installed=False,
        status="inactive",
        category="business",
        created_at=timestamp,
        updated_at=timestamp,
        description=(
            "Premium business-operations intelligence MCP server. Access is "
            "unlocked after Stripe Billing checkout completes."
        ),
        source_url="mock://wright/premium-ops-intelligence-mcp",
        installed_version="demo",
        instructions=(
            "This MCP represents a paid business-operations subscription. In "
            "the purchase flow Hermes receives the checkout URL, uses its Stripe "
            "skill to request approval, and Wright unlocks this server after "
            "checkout.session.completed."
        ),
        verification_state="verified_mcp",
        installability_tier="blocked",
        risk_level="low",
        deployment_mode="local",
        platform_support={
            "linux_x64": {
                "status": "yes",
                "tested": True,
                "notes": "Stdio MCP server runs inside the Wright container.",
            },
            "windows_11_x64": {
                "status": "likely",
                "tested": False,
                "notes": "Pure Python MCP server.",
            },
            "macos_arm64": {
                "status": "likely",
                "tested": False,
                "notes": "Pure Python MCP server.",
            },
        },
        host_software_required=[],
        credentials_required=[],
        default_enabled=False,
        approval_gates=["stripe_link_approval"],
        validation_result={
            "status": "passed",
            "message": "Paid MCP initializes and lists subscription tools.",
            "environment": "wright-hackathon-container",
            "missing_dependencies": [],
        },
        install_blocked_reason=(
            "Subscription required. Start a Hermes Stripe checkout to "
            "unlock Premium Ops Intelligence MCP."
        ),
    )


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    _ensure_billing_schema(conn)
    return conn


def _ensure_billing_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mcp_billing_purchases (
            purchase_id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            session_id TEXT,
            customer_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'paid', 'provisioned', 'failed')),
            checkout_url TEXT NOT NULL,
            stripe_session_id TEXT NOT NULL UNIQUE,
            amount_cents INTEGER NOT NULL,
            currency TEXT NOT NULL,
            payment_provider TEXT NOT NULL DEFAULT 'stripe_mock',
            product_name TEXT NOT NULL,
            metadata TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            provisioned_at INTEGER
        )
        """
    )


def _ensure_demo_server(db_path: str) -> McpServer:
    existing = get_server(db_path, PAID_DEMO_SERVER_ID)
    demo = _demo_server()
    if not existing:
        insert_server(db_path, demo)
        return demo

    locked_updates: dict[str, Any] = {
        "name": demo.name,
        "type": demo.type,
        "command": demo.command,
        "category": demo.category,
        "description": demo.description,
        "source_url": demo.source_url,
        "installed_version": demo.installed_version,
        "instructions": demo.instructions,
        "verification_state": demo.verification_state,
        "risk_level": demo.risk_level,
        "deployment_mode": demo.deployment_mode,
        "platform_support": demo.platform_support,
        "host_software_required": demo.host_software_required,
        "credentials_required": demo.credentials_required,
        "default_enabled": demo.default_enabled,
        "approval_gates": demo.approval_gates,
        "validation_result": demo.validation_result,
        "updated_at": int(time.time()),
    }
    if not existing.is_installed:
        locked_updates.update(
            {
                "installability_tier": "blocked",
                "install_blocked_reason": demo.install_blocked_reason,
                "is_active": False,
                "status": "inactive",
                "error_message": None,
            }
        )
    return update_server(db_path, PAID_DEMO_SERVER_ID, locked_updates) or existing


def _row_to_purchase(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _latest_purchase(db_path: str, server_id: str) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM mcp_billing_purchases
            WHERE server_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (server_id,),
        )
        row = cursor.fetchone()
        return _row_to_purchase(row) if row else None


def _subscription_rows(db_path: str) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM mcp_billing_purchases
            WHERE status = 'provisioned'
            ORDER BY COALESCE(provisioned_at, updated_at) DESC
            """
        )
        return [_row_to_purchase(row) for row in cursor.fetchall()]


def _get_purchase(
    db_path: str,
    purchase_id: Optional[str] = None,
    stripe_session_id: Optional[str] = None,
    server_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    with _connect(db_path) as conn:
        cursor = conn.cursor()
        if purchase_id:
            cursor.execute(
                "SELECT * FROM mcp_billing_purchases WHERE purchase_id = ?",
                (purchase_id,),
            )
        elif stripe_session_id:
            cursor.execute(
                "SELECT * FROM mcp_billing_purchases WHERE stripe_session_id = ?",
                (stripe_session_id,),
            )
        elif server_id:
            cursor.execute(
                """
                SELECT * FROM mcp_billing_purchases
                WHERE server_id = ? AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (server_id,),
            )
        else:
            return None
        row = cursor.fetchone()
        return _row_to_purchase(row) if row else None


def _create_pending_purchase(
    db_path: str, server: McpServer, body: CheckoutRequest
) -> dict[str, Any]:
    now = int(time.time())
    purchase_id = f"mp_{uuid.uuid4().hex[:16]}"
    stripe_session_id = f"cs_test_wright_{uuid.uuid4().hex[:18]}"
    checkout_url = f"https://checkout.stripe.test/wright/{purchase_id}"
    metadata = {
        "demo": True,
        "stripe_event": "checkout.session.completed",
        "hermes_flow": "stripe-link-cli",
    }
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO mcp_billing_purchases (
                purchase_id, server_id, session_id, customer_id, status,
                checkout_url, stripe_session_id, amount_cents, currency,
                payment_provider, product_name, metadata, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, 'stripe_mock', ?, ?, ?, ?)
            """,
            (
                purchase_id,
                server.server_id,
                body.session_id,
                body.customer_id,
                checkout_url,
                stripe_session_id,
                PAID_DEMO_PRICE_CENTS,
                PAID_DEMO_CURRENCY,
                server.name,
                json.dumps(metadata),
                now,
                now,
            ),
        )
        conn.commit()
    return _get_purchase(db_path, purchase_id=purchase_id) or {}


def _set_purchase_status(
    db_path: str, purchase_id: str, status_value: str, provisioned: bool = False
) -> dict[str, Any]:
    now = int(time.time())
    provisioned_at = now if provisioned else None
    with _connect(db_path) as conn:
        conn.execute(
            """
            UPDATE mcp_billing_purchases
            SET status = ?,
                updated_at = ?,
                provisioned_at = COALESCE(?, provisioned_at)
            WHERE purchase_id = ?
            """,
            (status_value, now, provisioned_at, purchase_id),
        )
        conn.commit()
    purchase = _get_purchase(db_path, purchase_id=purchase_id)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase '{purchase_id}' not found.",
        )
    return purchase


def _enabled_with_server(
    db_path: str, session_id: str, server: McpServer
) -> list[str]:
    current = get_workspace_enabled_tools(db_path, session_id)
    enabled = list(current or [])
    if server.server_id not in enabled and server.name not in enabled:
        enabled.append(server.server_id)
    return enabled


async def _provision_purchase(
    request: Request, engine: McpEngine, purchase: dict[str, Any]
) -> dict[str, Any]:
    db_path = engine.db_path
    server = _ensure_demo_server(db_path)
    if purchase["server_id"] != server.server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This demo checkout can only provision the paid MCP demo server.",
        )

    session_id = purchase.get("session_id")
    workspace = get_workspace_by_session(db_path, session_id) if session_id else None
    if not workspace:
        workspace = get_gateway_workspace(db_path)
        if workspace:
            session_id = workspace["session_id"]

    update_server(
        db_path,
        server.server_id,
        {
            "is_installed": True,
            "installability_tier": "tested",
            "install_blocked_reason": None,
            "error_message": None,
            "updated_at": int(time.time()),
        },
    )

    if session_id:
        update_workspace_enabled_tools(
            db_path,
            session_id,
            _enabled_with_server(db_path, session_id, server),
        )
        set_active_gateway_session(db_path, session_id)

    workspace_dir = workspace["local_path"] if workspace else None
    updated = await engine.start_server(server.server_id, workspace_dir=workspace_dir)
    updated = update_server(
        db_path,
        server.server_id,
        {
            "is_installed": True,
            "installability_tier": "tested",
            "install_blocked_reason": None,
            "error_message": updated.error_message,
            "updated_at": int(time.time()),
        },
    ) or updated

    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager and session_id:
        sync_manager.sync_workspace_tools(session_id)
    sync_mcp_server_to_hermes(updated)

    from api.routers.gateway import notify_gateway_tool_change

    notify_gateway_tool_change()
    return _set_purchase_status(
        db_path, purchase["purchase_id"], "provisioned", provisioned=True
    )


def _purchase_response(
    purchase: dict[str, Any],
    server: McpServer,
    message: str,
) -> PurchaseResponse:
    provisioned = purchase["status"] == "provisioned"
    return PurchaseResponse(
        purchase_id=purchase["purchase_id"],
        server_id=server.server_id,
        server_name=server.name,
        session_id=purchase.get("session_id"),
        customer_id=purchase["customer_id"],
        status=purchase["status"],
        checkout_url=purchase["checkout_url"],
        stripe_session_id=purchase["stripe_session_id"],
        amount_cents=purchase["amount_cents"],
        currency=purchase["currency"],
        provisioned=provisioned,
        message=message,
        hermes_stripe_mock={
            "checkout_url": purchase["checkout_url"],
            "approval_amount": f"{purchase['currency'].upper()} {purchase['amount_cents'] / 100:.2f}",
            "expected_hermes_step": (
                "Hermes reads the checkout URL and would invoke its Stripe "
                "Link flow. For the demo, complete the mocked webhook instead."
            ),
            "mock_webhook": {
                "event_type": "checkout.session.completed",
                "purchase_id": purchase["purchase_id"],
                "stripe_session_id": purchase["stripe_session_id"],
            },
            "browser_mock_complete_path": (
                f"/api/billing/purchases/{purchase['purchase_id']}/mock-complete"
            ),
        },
    )


def _wants_html(request: Request) -> bool:
    if request.query_params.get("format") == "html":
        return True
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept


def _format_money(amount_cents: int, currency: str) -> str:
    if currency.lower() == "usd":
        return f"${amount_cents / 100:.2f}"
    return f"{currency.upper()} {amount_cents / 100:.2f}"


def _render_checkout_page(purchase_response: PurchaseResponse) -> HTMLResponse:
    complete_href = (
        f"/api/billing/purchases/{purchase_response.purchase_id}/complete"
        "?format=html"
    )
    amount = _format_money(
        purchase_response.amount_cents, purchase_response.currency
    )
    page = f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Stripe Billing Checkout</title>
    <style>
      :root {{
        color-scheme: dark;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #07111f;
        color: #eef7ff;
      }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at top left, rgba(99, 91, 255, 0.28), transparent 34%),
          radial-gradient(circle at bottom right, rgba(0, 212, 255, 0.12), transparent 30%),
          #07111f;
      }}
      main {{
        width: min(720px, calc(100vw - 32px));
        border: 1px solid rgba(99, 91, 255, 0.35);
        border-radius: 10px;
        background: rgba(10, 20, 36, 0.92);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
        overflow: hidden;
      }}
      .brandbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding: 14px 28px;
        background: linear-gradient(90deg, #635bff, #00d4ff);
        color: #ffffff;
      }}
      .stripe {{
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.01em;
      }}
      .trust-pill {{
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
      }}
      header {{
        padding: 24px 28px;
        border-bottom: 1px solid rgba(117, 190, 255, 0.2);
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: 24px;
        letter-spacing: 0;
      }}
      p {{
        margin: 0;
        color: #9fb7cc;
        line-height: 1.5;
      }}
      section {{
        padding: 24px 28px;
        display: grid;
        gap: 18px;
      }}
      .row {{
        display: flex;
        justify-content: space-between;
        gap: 20px;
        border-bottom: 1px solid rgba(117, 190, 255, 0.12);
        padding-bottom: 12px;
      }}
      .label {{
        color: #9fb7cc;
        font-size: 13px;
        text-transform: uppercase;
        font-weight: 800;
      }}
      .value {{
        font-weight: 800;
        text-align: right;
      }}
      .price {{
        font-size: 32px;
        color: #a9a5ff;
      }}
      .notice {{
        border: 1px solid rgba(99, 91, 255, 0.36);
        background: rgba(99, 91, 255, 0.1);
        border-radius: 8px;
        padding: 14px 16px;
      }}
      .actions {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: center;
      }}
      a.button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        padding: 0 18px;
        border-radius: 8px;
        background: #635bff;
        color: #ffffff;
        font-weight: 900;
        text-decoration: none;
      }}
      a.secondary {{
        color: #9fdcff;
        text-decoration: none;
        font-weight: 700;
      }}
      code {{
        color: #67d2ff;
        word-break: break-all;
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="brandbar">
        <div class="stripe">stripe</div>
        <div class="trust-pill">Secure checkout</div>
      </div>
      <header>
        <h1>Stripe Billing Checkout</h1>
        <p>Hermes sends this checkout to Stripe Link for human approval before Wright provisions the MCP subscription.</p>
      </header>
      <section>
        <div class="row">
          <div>
            <div class="label">Product</div>
            <div>{escape(purchase_response.server_name)}</div>
          </div>
          <div class="value">Business Ops MCP</div>
        </div>
        <div class="row">
          <div>
            <div class="label">Subscription</div>
            <div class="price">{escape(amount)} / month</div>
          </div>
          <div class="value">{escape(purchase_response.status)}</div>
        </div>
        <div class="notice">
          <p><strong>Stripe Link approval:</strong> approve exactly {escape(amount)}. After approval, Wright receives payment confirmation and enables the MCP server.</p>
        </div>
        <div>
          <div class="label">Checkout session</div>
          <code>{escape(purchase_response.stripe_session_id)}</code>
        </div>
        <div class="actions">
          <a class="button" href="{escape(complete_href)}">Approve with Stripe Link</a>
          <a class="secondary" href="http://localhost:5188/">Back to Dashboard</a>
        </div>
      </section>
    </main>
  </body>
</html>
"""
    return HTMLResponse(page)


def _frontend_dashboard_href(request: Request) -> str:
    configured_url = os.environ.get("WRIGHT_FRONTEND_URL")
    if configured_url:
        return configured_url.rstrip("/") + "/"

    referrer = request.headers.get("referer") or request.headers.get("referrer")
    if referrer:
        parsed = urlparse(referrer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"

    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/") + "/"

    parsed = urlparse(str(request.base_url))
    if parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 8088:
        return f"{parsed.scheme}://{parsed.hostname}:5188/"

    return "/"


def _render_completion_page(request: Request, purchase_response: PurchaseResponse) -> HTMLResponse:
    dashboard_href = _frontend_dashboard_href(request)
    page = f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Stripe Payment Complete</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at top left, rgba(99, 91, 255, 0.28), transparent 34%),
          #07111f;
        color: #eef7ff;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      main {{
        width: min(680px, calc(100vw - 32px));
        border: 1px solid rgba(99, 91, 255, 0.35);
        border-radius: 10px;
        background: rgba(10, 20, 36, 0.94);
        padding: 28px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: 26px;
        letter-spacing: 0;
      }}
      p {{
        color: #a9bdce;
        line-height: 1.5;
      }}
      a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        padding: 0 18px;
        border-radius: 8px;
        background: #635bff;
        color: #ffffff;
        font-weight: 900;
        text-decoration: none;
      }}
      code {{
        color: #67d2ff;
        word-break: break-all;
      }}
      .actions {{
        margin-top: 24px;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>Stripe Payment Complete</h1>
      <p><strong>{escape(purchase_response.server_name)}</strong> has been paid for and installed.</p>
      <p>Purchase id: <code>{escape(purchase_response.purchase_id)}</code></p>
      <p>Hermes and the Wright gateway have been updated so the new MCP tools are available.</p>
      <div class="actions">
        <a href="{escape(dashboard_href)}">Back to Dashboard</a>
      </div>
    </main>
  </body>
</html>
"""
    return HTMLResponse(page)


@router.get("/mcp-products", response_model=BillingProductsListResponse)
async def list_mcp_billing_products(
    engine: McpEngine = Depends(get_mcp_engine),
):
    server = _ensure_demo_server(engine.db_path)
    latest = _latest_purchase(engine.db_path, server.server_id)
    purchased = server.is_installed or (
        latest is not None and latest["status"] in {"paid", "provisioned"}
    )
    install_state = "active" if server.status == "active" else "locked"
    if latest and latest["status"] == "pending":
        install_state = "checkout_pending"
    if purchased and server.status != "active":
        install_state = "purchased"

    return BillingProductsListResponse(
        products=[
            BillingProductResponse(
                server_id=server.server_id,
                name=server.name,
                description=server.description or "",
                price_cents=PAID_DEMO_PRICE_CENTS,
                currency=PAID_DEMO_CURRENCY,
                interval=PAID_DEMO_INTERVAL,
                payment_mode="stripe_billing_subscription_mock",
                requires_payment=not purchased,
                purchased=purchased,
                install_state=install_state,
                latest_purchase_status=latest["status"] if latest else None,
                checkout_url=latest["checkout_url"] if latest else None,
            )
        ]
    )


@router.get("/subscriptions", response_model=BillingSubscriptionsListResponse)
async def list_mcp_subscriptions(
    engine: McpEngine = Depends(get_mcp_engine),
):
    subscriptions: list[BillingSubscriptionResponse] = []
    for purchase in _subscription_rows(engine.db_path):
        if purchase["server_id"] == PAID_DEMO_SERVER_ID:
            server = _ensure_demo_server(engine.db_path)
        else:
            server = get_server(engine.db_path, purchase["server_id"])

        mcp_enabled = bool(
            server and server.is_installed and server.status == "active"
        )
        subscriptions.append(
            BillingSubscriptionResponse(
                subscription_id=purchase["purchase_id"],
                server_id=purchase["server_id"],
                server_name=server.name if server else purchase["product_name"],
                customer_id=purchase["customer_id"],
                session_id=purchase.get("session_id"),
                amount_cents=purchase["amount_cents"],
                currency=purchase["currency"],
                interval=PAID_DEMO_INTERVAL,
                payment_date=purchase["provisioned_at"] or purchase["updated_at"],
                status="active",
                mcp_enabled=mcp_enabled,
                mcp_status="enabled" if mcp_enabled else "provisioning",
            )
        )
    return BillingSubscriptionsListResponse(subscriptions=subscriptions)


@router.post(
    "/mcp-products/{server_id}/checkout",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mcp_checkout(
    server_id: str,
    body: CheckoutRequest,
    engine: McpEngine = Depends(get_mcp_engine),
):
    server = _ensure_demo_server(engine.db_path)
    if server_id != server.server_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paid MCP product '{server_id}' not found.",
        )
    if server.is_installed:
        latest = _latest_purchase(engine.db_path, server.server_id)
        if latest:
            return _purchase_response(
                latest, server, "Subscription already provisioned for this MCP server."
            )

    purchase = _create_pending_purchase(engine.db_path, server, body)
    return _purchase_response(
        purchase,
        server,
        "Mock Stripe checkout created. Hermes can now request Stripe Link approval.",
    )


@router.get("/mcp-products/{server_id}/checkout")
async def create_mcp_checkout_from_browser(
    server_id: str,
    request: Request,
    session_id: Optional[str] = None,
    customer_id: str = "demo-builder",
    engine: McpEngine = Depends(get_mcp_engine),
):
    """Browser-friendly demo helper for the mock checkout flow.

    Real clients should use POST. This GET route exists so a presenter can paste
    the mock checkout URL into a browser and still see the fake Stripe payload.
    """
    server = _ensure_demo_server(engine.db_path)
    if server_id != server.server_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paid MCP product '{server_id}' not found.",
        )
    if server.is_installed:
        latest = _latest_purchase(engine.db_path, server.server_id)
        if latest:
            response = _purchase_response(
                latest, server, "Subscription already provisioned for this MCP server."
            )
            return _render_completion_page(request, response) if _wants_html(request) else response

    purchase = _create_pending_purchase(
        engine.db_path,
        server,
        CheckoutRequest(session_id=session_id, customer_id=customer_id),
    )
    response = _purchase_response(
        purchase,
        server,
        "Mock Stripe checkout created from browser GET. Use POST for agent flows.",
    )
    return _render_checkout_page(response) if _wants_html(request) else response


@router.post("/purchases/{purchase_id}/mock-complete", response_model=PurchaseResponse)
async def complete_mock_purchase(
    purchase_id: str,
    request: Request,
    engine: McpEngine = Depends(get_mcp_engine),
):
    server = _ensure_demo_server(engine.db_path)
    purchase = _get_purchase(engine.db_path, purchase_id=purchase_id)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase '{purchase_id}' not found.",
        )
    if purchase["status"] == "provisioned":
        return _purchase_response(
            purchase, server, "Mock payment was already provisioned."
        )
    _set_purchase_status(engine.db_path, purchase_id, "paid")
    provisioned = await _provision_purchase(request, engine, purchase)
    return _purchase_response(
        provisioned,
        server,
        "Mock checkout.session.completed received; paid MCP server is active.",
    )


async def _complete_purchase_from_browser_response(
    purchase_id: str,
    request: Request,
    engine: McpEngine,
):
    server = _ensure_demo_server(engine.db_path)
    purchase = _get_purchase(engine.db_path, purchase_id=purchase_id)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase '{purchase_id}' not found.",
        )
    if purchase["status"] == "provisioned":
        response = _purchase_response(
            purchase, server, "Mock payment was already provisioned."
        )
        return _render_completion_page(request, response) if _wants_html(request) else response
    _set_purchase_status(engine.db_path, purchase_id, "paid")
    provisioned = await _provision_purchase(request, engine, purchase)
    response = _purchase_response(
        provisioned,
        server,
        "Mock checkout.session.completed received from browser GET; paid MCP server is active.",
    )
    return _render_completion_page(request, response) if _wants_html(request) else response


@router.get("/purchases/{purchase_id}/complete")
async def complete_purchase_from_browser(
    purchase_id: str,
    request: Request,
    engine: McpEngine = Depends(get_mcp_engine),
):
    """Browser-friendly checkout completion path."""
    return await _complete_purchase_from_browser_response(
        purchase_id, request, engine
    )


@router.get("/purchases/{purchase_id}/mock-complete")
async def complete_mock_purchase_from_browser(
    purchase_id: str,
    request: Request,
    engine: McpEngine = Depends(get_mcp_engine),
):
    """Browser-friendly demo helper for completing a mock Stripe checkout."""
    return await _complete_purchase_from_browser_response(
        purchase_id, request, engine
    )


@router.post("/webhooks/stripe/mock", response_model=PurchaseResponse)
async def receive_mock_stripe_webhook(
    body: MockStripeWebhookRequest,
    request: Request,
    engine: McpEngine = Depends(get_mcp_engine),
):
    if body.event_type != "checkout.session.completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only checkout.session.completed is supported by this mock webhook.",
        )

    server = _ensure_demo_server(engine.db_path)
    purchase = _get_purchase(
        engine.db_path,
        purchase_id=body.purchase_id,
        stripe_session_id=body.stripe_session_id,
        server_id=body.server_id,
    )
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending mock Stripe purchase found.",
        )
    if purchase["status"] == "provisioned":
        return _purchase_response(
            purchase, server, "Mock payment was already provisioned."
        )
    _set_purchase_status(engine.db_path, purchase["purchase_id"], "paid")
    provisioned = await _provision_purchase(request, engine, purchase)
    return _purchase_response(
        provisioned,
        server,
        "Mock Stripe webhook completed; MCP subscription is unlocked.",
    )
