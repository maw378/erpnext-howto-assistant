import frappe
from frappe.model.document import Document


class AIHowToAssistantSettings(Document):
	def get_api_key(self) -> str | None:
		return self.get_password("openai_api_key", raise_exception=False)

	def validate(self):
		if self.enabled and not self.get_api_key():
			frappe.throw(
				"Set an OpenAI API Key before enabling the How-To Assistant.",
				title="Missing OpenAI API Key",
			)
