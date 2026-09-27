frappe.pages["ai-how-to-assistant"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("AI How-To Assistant"),
		single_column: true,
	});

	// Mirrors the server-side check in howto_assistant.ask() - hiding the
	// floating button/workspace shortcut isn't enough on its own since a
	// user could still navigate straight to this page's URL.
	if (frappe.boot && frappe.boot.howto_assistant_visible === false) {
		$(`<div class="text-muted" style="padding: 40px; text-align: center;">
			${__("The How-To Assistant is not available for your account.")}
		</div>`).appendTo(page.main);
		return;
	}

	new erpnext_howto_assistant.HowToChat(page.main);
};
