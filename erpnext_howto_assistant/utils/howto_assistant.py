"""How-To Assistant: a guidance-only chatbot backed by OpenAI (gpt-4o-mini by
default), grounded on the small curated corpus in howto_knowledge.py.

Scope is intentionally narrow - "how do I do X in ERPNext" - and enforced in
two places: the system prompt (SYSTEM_PROMPT) instructs the model to refuse
everything else, and this module never gives the model any tool/function
access or document data to begin with, so there is nothing for it to read or
change even if a user tries to talk it into it.
"""

import re

import requests
import frappe
from frappe import _

from erpnext_howto_assistant.utils.howto_knowledge import search_knowledge

URL_RE = re.compile(r"https?://\S+")
# Same Arabic-script range the client widget uses (HOWTO_ARABIC_RE in
# howto_widget.js) to decide bubble direction - reused here to pick a
# per-entry "source_ar" citation over the default "source" when the
# question itself is in Arabic (see _build_messages).
ARABIC_RE = re.compile("[؀-ۿ]")

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
REQUEST_TIMEOUT = 30
MAX_QUESTION_LENGTH = 800
MAX_HISTORY_TURNS = 4  # user/assistant pairs kept from client-supplied history

SYSTEM_PROMPT = """You are the "How-To Assistant" embedded in this company's ERPNext desk.

Your ONLY job: explain HOW to do something in ERPNext/Frappe - which module, doctype, \
screen, button, or field to use, and in what order. You are a navigation and procedure \
guide, nothing else.

Hard rules:
1. You never read, fetch, calculate, summarize, or estimate this company's actual data \
(sales figures, stock levels, balances, employee records, invoice numbers, report output, \
etc.), even if the user pastes some in and asks you to interpret it. You have no access to \
their data and cannot see it - say so if asked.
2. You never perform, simulate performing, or hand over exact API calls/scripts that would \
create, update, submit, cancel, or delete a real record. Describe the manual steps a human \
takes in the UI instead (e.g. "Go to Stock > Stock Entry > New, set Purpose to Material \
Transfer...").
3. You never generate, run, or design financial/management reports, dashboards, or queries \
- point the user to the relevant built-in Report/Dashboard and how to open and filter it, \
but do not produce the numbers yourself.
4. If a question is not about how to use ERPNext/Frappe (general chit-chat, unrelated \
software, personal advice, etc.), politely decline in the same language as the question and \
steer back to ERPNext how-to topics.
5. If you are not confident about the exact menu path for this version, say so plainly \
instead of guessing with false confidence, and suggest where to look (e.g. the module's \
workspace, or the Awesome Bar search).
6. Keep answers short: one lead-in sentence plus a numbered step list. No filler, no \
repeating the question back.

Language: detect the language the user asked in and answer entirely in that language. If \
they write in Arabic, answer entirely in Arabic (use clear Modern Standard Arabic; you may \
keep ERPNext doctype/field/button names in English since that is what appears on screen). If \
they write in English, answer entirely in English. If a message mixes both, mirror whichever \
language makes up most of it.

You may be given "Reference notes" for topics that matched the question - prefer these over \
your own memory when present, and silently ignore any note that isn't actually relevant to \
the question. When a note includes a "(Source: <url>)", end your answer with a final line \
pointing to it - "Learn more: <url>" in English, "لمزيد من التفاصيل: <url>" in Arabic - so the \
user can read the official ERPNext documentation themselves; never invent a URL that wasn't \
given to you."""


def get_settings():
	return frappe.get_single("AI How-To Assistant Settings")


def is_visible_to_user(settings=None, user: str | None = None) -> bool:
	"""Whether `user` should see/use the assistant, per Settings.visible_to.
	Does NOT check `enabled` - callers that care about the feature being
	fully off should check that separately, since the two produce different
	user-facing messages."""
	settings = settings or get_settings()
	user = user or frappe.session.user

	if user == "Administrator":
		# Always allowed, so an admin can reach the settings/page to manage
		# this feature even if they left themselves off the allow-list.
		return True
	if settings.visible_to != "Only Selected Users":
		return True
	return user in {row.user for row in settings.allowed_users}


def extend_bootinfo(bootinfo):
	"""Lets the client decide whether to mount the floating widget without an
	extra round trip on every page load - computed once at session boot."""
	settings = get_settings()
	bootinfo.howto_assistant_visible = bool(settings.enabled) and is_visible_to_user(settings)


def _rate_limit_key(user: str) -> str:
	return f"erpnext_howto_assistant:howto_count:{user}:{frappe.utils.today()}"


def _check_rate_limit(settings) -> None:
	limit = settings.daily_request_limit or 0
	if not limit:
		return

	key = _rate_limit_key(frappe.session.user)
	count = int(frappe.cache().get_value(key) or 0)
	if count >= limit:
		frappe.throw(
			_("You've reached today's limit of {0} How-To Assistant questions. Try again tomorrow.").format(
				limit
			),
			title=_("Daily Limit Reached"),
		)
	frappe.cache().set_value(key, count + 1, expires_in_sec=86400)


def _build_messages(question: str, history: list[dict] | None) -> tuple[list[dict], set[str], list[dict]]:
	messages = [{"role": "system", "content": SYSTEM_PROMPT}]

	matches = search_knowledge(question, installed_apps=set(frappe.get_installed_apps()))
	is_arabic = bool(ARABIC_RE.search(question))

	allowed_sources = set()
	if matches:
		lines = []
		for m in matches:
			source = (m.get("source_ar") if is_arabic else None) or m.get("source")
			line = f"- {m['title']}: {m['notes']}"
			if source:
				allowed_sources.add(source)
				line += f" (Source: {source})"
			lines.append(line)
		notes = "\n".join(lines)
		messages.append({"role": "system", "content": f"Reference notes:\n{notes}"})

	for turn in (history or [])[-(MAX_HISTORY_TURNS * 2) :]:
		role = turn.get("role")
		content = turn.get("content")
		if role in ("user", "assistant") and isinstance(content, str) and content.strip():
			messages.append({"role": role, "content": content[:MAX_QUESTION_LENGTH]})

	messages.append({"role": "user", "content": question})
	return messages, allowed_sources, matches


MAX_ACTIONS = 4


def _collect_actions(matches: list[dict]) -> list[dict]:
	"""Deterministic "clickable steps": pulled straight from the matched
	knowledge entries' own `actions`, never parsed out of the LLM's freeform
	answer text - the model's wording isn't reliable enough (language-dependent
	phrasing, no guarantee it mentions a step at all) to regex a route out of."""
	seen_routes = set()
	actions = []
	for m in matches:
		for action in m.get("actions", []):
			if action["route"] in seen_routes:
				continue
			seen_routes.add(action["route"])
			actions.append(action)
	return actions[:MAX_ACTIONS]


def _strip_unverified_links(answer: str, allowed_sources: set[str]) -> str:
	"""The system prompt tells the model to only cite a Source URL we actually
	handed it in the reference notes, and to never invent one - but that
	instruction isn't reliably followed (observed gpt-4o-mini fabricating a
	plausible-looking docs.frappe.io URL that 404s). Enforce it deterministically
	instead of trusting compliance: drop any line containing a URL we didn't
	supply this turn."""
	if not allowed_sources:
		allowed_sources = set()

	kept_lines = []
	for line in answer.splitlines():
		urls = [u.rstrip(").,;:!?\"'") for u in URL_RE.findall(line)]
		if urls and not all(u in allowed_sources for u in urls):
			continue
		kept_lines.append(line)
	return "\n".join(kept_lines).rstrip()


def _call_openai(settings, messages: list[dict]) -> str:
	api_key = settings.get_api_key()
	if not api_key:
		frappe.throw(_("No OpenAI API Key set on AI How-To Assistant Settings."))

	payload = {
		"model": settings.model or "gpt-4o-mini",
		"messages": messages,
		"max_tokens": settings.max_tokens or 500,
		"temperature": settings.temperature if settings.temperature is not None else 0.2,
	}
	headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

	try:
		response = requests.post(
			OPENAI_CHAT_COMPLETIONS_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
		)
	except requests.RequestException as e:
		frappe.throw(_("Could not reach OpenAI: {0}").format(e))

	if not response.ok:
		try:
			detail = response.json().get("error", {}).get("message")
		except ValueError:
			detail = response.text
		frappe.throw(_("OpenAI request failed ({0}): {1}").format(response.status_code, detail))

	body = response.json()
	choices = body.get("choices") or []
	if not choices:
		frappe.throw(_("OpenAI returned no answer."))

	return choices[0]["message"]["content"].strip()


@frappe.whitelist()
def ask(question: str, history: str | list[dict] | None = None) -> dict:
	# frappe.call() JSON-stringifies list/dict args before sending, so `history`
	# arrives here as a raw string, not a list - Frappe's whitelist type
	# checker validates against the *declared* type via pydantic, which will
	# not itself parse a JSON string into a list[dict], so the annotation
	# above has to accept str too and we decode it ourselves.
	history = frappe.parse_json(history) if isinstance(history, str) else history

	question = (question or "").strip()
	if not question:
		frappe.throw(_("Ask a question first."))
	if len(question) > MAX_QUESTION_LENGTH:
		frappe.throw(_("Please keep questions under {0} characters.").format(MAX_QUESTION_LENGTH))

	settings = get_settings()
	if not settings.enabled:
		frappe.throw(_("The How-To Assistant is currently disabled. Ask a System Manager to enable it."))
	if not is_visible_to_user(settings):
		frappe.throw(
			_("The How-To Assistant is not available for your account."), exc=frappe.PermissionError
		)

	_check_rate_limit(settings)

	messages, allowed_sources, matches = _build_messages(question, history)
	answer = _call_openai(settings, messages)
	answer = _strip_unverified_links(answer, allowed_sources)
	return {"answer": answer, "actions": _collect_actions(matches)}


@frappe.whitelist()
def test_connection() -> dict:
	"""Used by the settings form's 'Test Connection' button - a cheap,
	single-turn round trip to confirm the API key and model are valid before
	relying on it in the chat page."""
	settings = get_settings()
	settings.check_permission("write")
	if not settings.get_api_key():
		frappe.throw(_("Set an OpenAI API Key first."))

	messages = [
		{"role": "system", "content": SYSTEM_PROMPT},
		{"role": "user", "content": "Say 'Connection OK' and nothing else."},
	]
	answer = _call_openai(settings, messages)
	return {"answer": answer}
