frappe.ui.form.on("AI How-To Assistant Settings", {
	refresh(frm) {
		if (frm.doc.openai_api_key) {
			frm.add_custom_button(__("Test Connection"), () => test_connection(frm));
		}
	},
});

function test_connection(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Save your changes before testing the connection."));
		return;
	}

	frappe.call({
		method: "erpnext_howto_assistant.utils.howto_assistant.test_connection",
		freeze: true,
		freeze_message: __("Calling OpenAI..."),
		callback: (r) => {
			frappe.msgprint({
				title: __("Connection OK"),
				indicator: "green",
				message: r.message ? r.message.answer : __("Connected."),
			});
		},
	});
}
