"""Small curated reference corpus for the How-To Assistant.

The step-by-step "notes" text in each entry is NOT scraped from docs.frappe.io
- that site (checked 2026-09-26) is written as conceptual/marketing overview
per module ("what this module does and why"), not as click-by-click how-to
instructions, so there is nothing there to lift verbatim. The notes instead
reflect how the ERPNext desk UI actually works.

What each entry DOES carry from docs.frappe.io/erpnext is its "source" URL -
the real module-overview page for that topic on the site the user asked us to
treat as the reference "data store". search_knowledge() surfaces that link
alongside the notes so the assistant can point the user at it for further
reading, without pretending the procedural text was copied from there.

This is deliberately not a live scrape or a vector index on every request -
the assistant only ever answers "how do I use feature X" questions, so a
short list of keyword-tagged step summaries is enough to ground gpt-4o-mini
and keep every request small (and cheap).

search_knowledge() does plain keyword overlap scoring, not embeddings - there
is no ranking subtlety worth paying for at this scope, and it needs no extra
service or index to keep in sync.

This app (erpnext_howto_assistant) is a standalone dependency of, but
separate from, erpnext_ai_dashboards and zatca_integration - a site can have
either, both, or neither installed alongside it. An entry describing a
feature owned by one of those apps carries "requires_app" so search_knowledge()
can drop it on a site where that app isn't installed, instead of confidently
describing a screen the user doesn't have.
"""

ENTRIES = [
	{
		"title": "Set up ZATCA e-invoicing (onboarding)",
		"keywords": [
			"zatca",
			"zatca setup",
			"zatca onboarding",
			"fatoora",
			"csid",
			"egs unit",
			"e-invoicing setup",
			"zatca settings",
		],
		"notes": (
			"ZATCA Integration > ZATCA Settings: fill in your company's legal name (English and "
			"Arabic), CR Number, address, and Environment (Sandbox/Simulation/Production), Save, "
			"then click 'Sign Up' to register with the ZATCA onboarding engine (this issues the "
			"API Key) and 'Sync Cities' to pull the City list. Next, ZATCA Integration > ZATCA EGS "
			"Unit > New: link that ZATCA Settings and Company, set Environment and Transaction "
			"Type, optionally a POS Profile/Branch, Save, then click 'Start Onboarding' (issues a "
			"compliance CSID), 'Run Compliance Checks', and 'Request Production CSID' - once that "
			"succeeds the unit is Active and ready to sign invoices. Use 'Renew Production CSID' "
			"before it expires and 'Sync Credentials' if signing keys are rotated."
		),
		"actions": [
			{"label": "Open ZATCA Settings", "route": "/app/zatca-settings"},
			{"label": "Open New ZATCA EGS Unit", "route": "/app/zatca-egs-unit/new"},
		],
		"source": "https://zatca.gov.sa/en/E-Invoicing/Pages/default.aspx",
		"source_ar": "https://zatca.gov.sa/ar/E-Invoicing/Pages/default.aspx",
		"requires_app": "zatca_integration",
	},
	{
		"title": "Issue a ZATCA-compliant Sales Invoice",
		"keywords": [
			"zatca invoice",
			"compliant invoice",
			"issue invoice zatca",
			"fatoora invoice",
			"e-invoice",
			"zatca invoice log",
		],
		"notes": (
			"Once ZATCA Settings and an Active ZATCA EGS Unit are configured (see 'Set up ZATCA "
			"e-invoicing'), issuing a ZATCA-compliant invoice needs no extra steps: create the "
			"invoice the normal ERPNext way - Accounts > Sales Invoice > New (or the POS screen for "
			"point-of-sale) - fill Customer and Items, then Submit. The ZATCA Integration app "
			"automatically generates the invoice's XML/QR/UUID and reports it to ZATCA on submit. "
			"Check ZATCA Integration > ZATCA Invoice Log afterwards to confirm it was "
			"Cleared/Reported, or to see the validation error if it wasn't."
		),
		"actions": [
			{"label": "Open New Sales Invoice", "route": "/app/sales-invoice/new"},
			{"label": "Open ZATCA Invoice Log", "route": "/app/zatca-invoice-log"},
		],
		"source": "https://zatca.gov.sa/en/E-Invoicing/Pages/default.aspx",
		"source_ar": "https://zatca.gov.sa/ar/E-Invoicing/Pages/default.aspx",
		"requires_app": "zatca_integration",
	},
	{
		"title": "Create a Sales Order / Quotation",
		"keywords": ["sales order", "quotation", "sell", "customer order", "so"],
		"notes": (
			"Selling > Quotation > New to draft a quote for a Customer and Items, then Save "
			"and Submit. Use 'Create > Sales Order' from an accepted Quotation to convert it, "
			"or go to Selling > Sales Order > New to start one directly. Fill Customer, add rows "
			"under Items (Item Code, Qty, Rate), set Delivery Date, then Save and Submit."
		),
		"source": "https://docs.frappe.io/erpnext/selling",
		"actions": [
			{"label": "Open New Quotation", "route": "/app/quotation/new"},
			{"label": "Open New Sales Order", "route": "/app/sales-order/new"},
		],
	},
	{
		"title": "Create a Sales Invoice and record payment",
		"keywords": ["sales invoice", "invoice customer", "bill customer", "record payment", "receive payment"],
		"notes": (
			"From a submitted Sales Order or Delivery Note, use 'Create > Sales Invoice' so items "
			"and rates carry over, or open Accounts > Sales Invoice > New directly. Save and Submit "
			"the invoice. To record the customer's payment, open the submitted invoice and click "
			"'Create > Payment', or go to Accounts > Payment Entry > New with Payment Type 'Receive'."
		),
		"source": "https://docs.frappe.io/erpnext/accounting",
		"actions": [{"label": "Open New Sales Invoice", "route": "/app/sales-invoice/new"}],
	},
	{
		"title": "Create a Purchase Order and Purchase Invoice",
		"keywords": ["purchase order", "po", "purchase invoice", "buy", "supplier order", "pay supplier"],
		"notes": (
			"Buying > Purchase Order > New: set Supplier, add Items with Qty and Rate, Save and "
			"Submit. When goods arrive, use 'Create > Purchase Receipt' from the PO. When the bill "
			"comes in, use 'Create > Purchase Invoice' from the PO or Purchase Receipt so quantities "
			"and rates carry over. To pay it, open the submitted Purchase Invoice and click "
			"'Create > Payment Entry', or go to Accounts > Payment Entry > New with Payment Type 'Pay'."
		),
		"source": "https://docs.frappe.io/erpnext/buying",
		"actions": [{"label": "Open New Purchase Order", "route": "/app/purchase-order/new"}],
	},
	{
		"title": "Add or edit an Item",
		"keywords": ["item", "product", "add item", "new item", "sku", "item code"],
		"notes": (
			"Stock (or Selling/Buying) > Item > New. Set Item Code, Item Name, and Item Group. "
			"Under 'Inventory', tick 'Maintain Stock' if it should be tracked in warehouses, and set "
			"Default Unit of Measure. Under 'Sales'/'Purchasing' tabs you can set default price lists, "
			"tax templates, and whether it can be sold/purchased."
		),
		"source": "https://docs.frappe.io/erpnext/stock",
		"actions": [{"label": "Open New Item", "route": "/app/item/new"}],
	},
	{
		"title": "Move or adjust stock (Stock Entry)",
		"keywords": [
			"stock entry",
			"transfer stock",
			"material transfer",
			"stock adjustment",
			"opening stock",
			"issue material",
		],
		"notes": (
			"Stock > Stock Entry > New. Choose a Stock Entry Type: 'Material Transfer' to move items "
			"between warehouses, 'Material Issue' to consume/write off stock, 'Material Receipt' to "
			"bring stock in without a Purchase Receipt (e.g. opening stock), or 'Repack'/'Manufacture' "
			"for production use cases. Add item rows with source/target warehouse as required by the "
			"type, then Save and Submit."
		),
		"source": "https://docs.frappe.io/erpnext/stock",
		"actions": [{"label": "Open New Stock Entry", "route": "/app/stock-entry/new"}],
	},
	{
		"title": "Raise a Material Request",
		"keywords": ["material request", "request stock", "request purchase", "indent"],
		"notes": (
			"Stock > Material Request > New. Set Purpose (Purchase, Material Transfer, Material "
			"Issue, or Manufacture), add the Items and quantities needed, and a Required By date. "
			"Save and Submit. A Purchase or Stock Entry can then be created from it via the "
			"'Create' button so the request is linked and tracked."
		),
		"source": "https://docs.frappe.io/erpnext/stock",
	},
	{
		"title": "Set up a Bill of Materials (BOM) and Work Order",
		"keywords": ["bom", "bill of materials", "work order", "manufacture", "production"],
		"notes": (
			"Manufacturing > BOM > New: pick the Item to be manufactured, set quantity, and add raw "
			"material rows with their quantities, then Save and Submit. To produce it, go to "
			"Manufacturing > Work Order > New, select the Item and its BOM, set the quantity to "
			"manufacture and the source/target warehouses, Save and Submit, then use 'Start' and "
			"'Finish' (or the linked Stock Entries) to record the actual production."
		),
		"source": "https://docs.frappe.io/erpnext/manufacturing",
	},
	{
		"title": "Record a Journal Entry or reconcile the bank",
		"keywords": ["journal entry", "bank reconciliation", "gl entry", "manual accounting entry"],
		"notes": (
			"Accounts > Journal Entry > New for manual double-entry postings: choose an Entry Type, "
			"add Accounts rows with Debit/Credit amounts that balance to zero, then Save and Submit. "
			"For matching bank statement lines to entries, use Accounts > Bank Reconciliation Tool, "
			"pick the Bank Account and date range, and match or create entries against the imported "
			"statement lines."
		),
		"source": "https://docs.frappe.io/erpnext/accounting",
	},
	{
		"title": "Add an Employee, apply for Leave, or mark Attendance",
		"keywords": ["employee", "leave application", "attendance", "hr", "onboard employee"],
		"notes": (
			"HR > Employee > New to add a person (Employee Name, Date of Joining, Department, "
			"Reports To). To request time off: HR > Leave Application > New, pick Leave Type and "
			"date range, Save and Submit for approval. Attendance can be marked manually at "
			"HR > Attendance > New, or via HR > Shift/Attendance tools if check-in devices are set up."
		),
		"source": "https://docs.frappe.io/erpnext/human-resources",
	},
	{
		"title": "Run Payroll",
		"keywords": ["payroll", "salary slip", "pay employees", "payroll entry"],
		"notes": (
			"HR > Payroll Entry > New: set the Company, Payroll date range/month, and Department "
			"filters, then click 'Get Employees' to pull eligible employees. Save and Submit to "
			"generate draft Salary Slips, which you then Submit individually (or in bulk) to post "
			"them; use 'Make Bank Entry' from the Payroll Entry once slips are submitted."
		),
		"source": "https://docs.frappe.io/erpnext/human-resources",
	},
	{
		"title": "Track a Lead or Opportunity (CRM)",
		"keywords": ["lead", "opportunity", "crm", "prospect"],
		"notes": (
			"CRM > Lead > New to capture a prospect's details. Convert a qualified Lead to a "
			"Customer/Opportunity using the 'Create' button on the Lead form. CRM > Opportunity > New "
			"tracks a specific deal - set the Party (Lead or Customer), expected items/value, and "
			"move it through its Sales Stage; convert it to a Quotation with 'Create > Quotation'. "
			"Note: docs.frappe.io flags this module as being phased out in ERPNext v17 in favor of "
			"the standalone Frappe CRM app - mention that if the user is on/upgrading to v17+."
		),
		"source": "https://docs.frappe.io/erpnext/crm",
	},
	{
		"title": "Log a support ticket (Issue)",
		"keywords": ["issue", "support ticket", "helpdesk", "customer complaint"],
		"notes": (
			"Support > Issue > New. Set the Customer/Contact, Subject, and Description, and a "
			"Priority. Assign it to a user with the Assign-To sidebar, and update its Status as it "
			"progresses (Open, Replied, Resolved, Closed)."
		),
		"source": "https://docs.frappe.io/erpnext/support",
	},
	{
		"title": "Create a Project and Task",
		"keywords": ["project", "task", "project management"],
		"notes": (
			"Projects > Project > New: set Project Name, dates, and optionally a Costing/Billing "
			"tab if you're tracking budget. Add Tasks either from the Project's Tasks tab or via "
			"Projects > Task > New, linking each Task back to the Project and (optionally) to each "
			"other via 'Depends On'."
		),
		"source": "https://docs.frappe.io/erpnext/projects",
	},
	{
		"title": "Register and depreciate a Fixed Asset",
		"keywords": ["asset", "fixed asset", "depreciation"],
		"notes": (
			"Assets > Asset > New: link the Item (must have 'Is Fixed Asset' checked), set Available "
			"For Use Date, Gross Purchase Amount, and a Finance Books row with the Depreciation "
			"Method and useful life, then Save and Submit. Depreciation entries post automatically "
			"via the scheduled job, or can be triggered from Assets > Asset Depreciation Schedule."
		),
		"source": "https://docs.frappe.io/erpnext/assets",
	},
	{
		"title": "Set up Users, Roles, and Permissions",
		"keywords": ["user", "role", "permission", "access", "add user"],
		"notes": (
			"Settings > User > New to invite/create a user and assign Roles under the Roles tab. "
			"Role-level access to a Doctype is controlled at Settings > Role Permissions Manager. "
			"For record-level restriction (e.g. only see documents for your own Warehouse/Company), "
			"use Settings > User Permission > New to restrict a user to specific values."
		),
		"actions": [
			{"label": "Open New User", "route": "/app/user/new"},
			{"label": "Open New Role", "route": "/app/role/new"},
		],
	},
	{
		"title": "Customize a Print Format or set up an approval Workflow",
		"keywords": ["print format", "workflow", "approval", "custom field", "customize form"],
		"notes": (
			"Settings > Print Format > New (or 'Customize' from a document's print preview) to design "
			"how a document prints. Settings > Customize Form to add/hide fields on a standard "
			"Doctype without coding. Settings > Workflow > New to define states and transitions "
			"(e.g. Draft -> Approved) that route a document through approvers instead of a plain "
			"Submit."
		),
	},
	{
		"title": "Find a screen, report, or setting quickly",
		"keywords": ["find", "where is", "search", "navigate", "awesome bar", "cannot find"],
		"notes": (
			"Use the search bar at the top of the desk (the 'Awesome Bar') and type the Doctype or "
			"report name - it jumps straight to it, or offers to create a new one ('new sales "
			"invoice'). Module workspaces in the left sidebar (Selling, Buying, Stock, Accounts, HR, "
			"...) group every related list, report, and setting for that area."
		),
		"source": "https://docs.frappe.io/erpnext/introduction",
	},
	{
		"title": "Read the Dead Stock dashboard and offer suggestions",
		"keywords": [
			"dead stock",
			"stagnant inventory",
			"slow moving",
			"dead stock dashboard",
			"offer suggestions",
			"tied up capital",
		],
		"notes": (
			"AI Dashboards > Dead Stock Dashboard shows flagged SKUs, capital tied up, and a "
			"tier/aging/category breakdown of stagnant inventory, computed by the AI service - click "
			"'Refresh' to re-run the analysis. For ready-to-send clearance ideas per flagged item, "
			"open the 'Dead Stock Offer Suggestions' report from the same workspace card."
		),
		"actions": [
			{"label": "Open Dead Stock Dashboard", "route": "/app/dead-stock-dashboard"},
			{"label": "Open Dead Stock Offer Suggestions", "route": "/app/query-report/Dead Stock Offer Suggestions"},
		],
		"requires_app": "erpnext_ai_dashboards",
	},
	{
		"title": "Read the AI Forecasting dashboard for an item",
		"keywords": ["forecast", "forecasting", "ai forecast", "predict demand", "expected quantity"],
		"notes": (
			"AI Dashboards > AI Forecastings, then pick an Item in the 'Item' filter at the top - it "
			"shows the AI-generated expected quantity per sale date plus its expected minimum/maximum "
			"range, and an overall sum row. If it says there's no trained model yet, that item wasn't "
			"part of the last training run."
		),
		"actions": [{"label": "Open AI Forecastings", "route": "/app/ai-forecastings"}],
		"requires_app": "erpnext_ai_dashboards",
	},
	{
		"title": "Configure the AI Dashboards subscription (API keys)",
		"keywords": ["ai dashboard settings", "subscriber id", "ai services api key", "plan tier", "product scope"],
		"notes": (
			"AI Dashboards > AI Dashboard Settings: set the Company, Subscriber ID and API Key for "
			"the AI service, and choose the Plan Tier and Product Scope (which dashboards/forecasts "
			"this company is entitled to). This is separate from the How-To Assistant's own settings."
		),
		"actions": [{"label": "Open AI Dashboard Settings", "route": "/app/ai-dashboard-settings"}],
		"requires_app": "erpnext_ai_dashboards",
	},
	{
		"title": "Configure the AI How-To Assistant itself",
		"keywords": [
			"how-to assistant settings",
			"enable assistant",
			"openai api key",
			"allowed users",
			"configure assistant",
			"daily limit",
		],
		"notes": (
			"Search 'AI How-To Assistant Settings' in the Awesome Bar (top search) to open it directly "
			"- tick 'Enabled' to turn this widget on, set the OpenAI API Key, Model, and an optional "
			"daily request limit per user. Under 'Visible To', choose 'Only Selected Users' and add "
			"rows to the 'Allowed Users' table to restrict "
			"it instead of showing it to everyone."
		),
		"actions": [{"label": "Open AI How-To Assistant Settings", "route": "/app/ai-how-to-assistant-settings"}],
	},
]


def search_knowledge(query: str, limit: int = 3, installed_apps: set[str] | None = None) -> list[dict]:
	"""Keyword-overlap search over ENTRIES. Returns up to `limit` entries, most
	relevant first; empty list if nothing scores above zero.

	`installed_apps`, when given, drops any entry whose "requires_app" isn't
	in it - this app can be installed standalone (current-erp) or alongside
	erpnext_ai_dashboards/zatca_integration (ai-enhanced), and an entry about
	a screen the site doesn't have would otherwise still get surfaced to the
	model as if it applied everywhere. Left as None (no filtering) so this
	function stays testable without a Frappe site."""
	words = {w for w in _tokenize(query) if len(w) > 2}
	if not words:
		return []

	candidates = ENTRIES
	if installed_apps is not None:
		candidates = [e for e in ENTRIES if not e.get("requires_app") or e["requires_app"] in installed_apps]

	scored = []
	for entry in candidates:
		haystack = {t for t in _tokenize(entry["title"]) if len(t) > 2} | {
			t for kw in entry["keywords"] for t in _tokenize(kw) if len(t) > 2
		}
		score = sum(1 for w in words if any(w in h or h in w for h in haystack))
		if score:
			scored.append((score, entry))

	scored.sort(key=lambda pair: pair[0], reverse=True)
	return [entry for _score, entry in scored[:limit]]


def _tokenize(text: str) -> set[str]:
	return set(text.lower().replace("/", " ").replace("-", " ").split())
