import frappe


def execute():
	"""Fix the ai-how-to-assistant Page record left pointing at the old
	ERPNext AI Dashboards module after the How-To Assistant was extracted
	into its own app. Without this, opening the page raises FileNotFoundError
	because Frappe looks for the controller under erpnext_ai_dashboards,
	where it no longer lives.
	"""
	if not frappe.db.exists("Page", "ai-how-to-assistant"):
		return

	current_module = frappe.db.get_value("Page", "ai-how-to-assistant", "module")
	if current_module != "ERPNext HowTo Assistant":
		frappe.db.set_value("Page", "ai-how-to-assistant", "module", "ERPNext HowTo Assistant")
