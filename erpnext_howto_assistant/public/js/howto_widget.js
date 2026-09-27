frappe.provide("erpnext_howto_assistant");

// Any Arabic-script character in the text - used to pick per-bubble text
// direction/alignment (and, for the assistant's own reply, the language it
// should answer in) since users may switch between English and Arabic from
// one question to the next.
const HOWTO_ARABIC_RE = /[؀-ۿ]/;

// Shown in the empty-state panel before the first question - picked to cover
// the custom apps this assistant is commonly deployed alongside (ZATCA
// integration, AI Dashboards) plus a couple of stock ERPNext basics, since
// those are exactly what a user's own ERPNext memory doesn't cover "for
// free". howto_knowledge.py gates the app-specific entries on
// installed_apps, so a starter question about a feature this particular
// site doesn't have just falls back to a generic answer instead of a wrong one.
const HOWTO_STARTER_QUESTIONS = [
	{ ar: "كيف أصدر فاتورة متوافقة مع ZATCA؟", en: "How do I issue a ZATCA-compliant invoice?" },
	{ ar: "كيف أضيف صنف؟", en: "How do I add an item?" },
	{ ar: "كيف أضيف مستخدم؟", en: "How do I add a user?" },
	{ ar: "كيف أقرأ لوحة المخزون الراكد؟", en: "How do I read the dead-stock dashboard?" },
];

// Turns a knowledge-entry "route" (an /app/... desk URL, as written by hand
// in howto_knowledge.py) into a client-side frappe.set_route() call instead
// of a full page reload. Doesn't need URL-decoding: route parts are plain
// segments (doctype names, "new", or a report title with spaces) exactly as
// frappe.set_route() itself expects them.
function howto_goto_route(route) {
	const parts = (route || "")
		.replace(/^\/app\/?/, "")
		.split("/")
		.filter(Boolean);
	if (!parts.length) return;
	frappe.set_route(...parts);
}

// Shared chat UI, mounted into whatever container is given - the dedicated
// "AI How-To Assistant" page (full width) and the floating drawer (narrow)
// both use this same class so behaviour (history, language detection,
// error surfacing) only lives in one place.
erpnext_howto_assistant.HowToChat = class HowToChat {
	constructor($parent, opts = {}) {
		this.$parent = $parent;
		this.compact = !!opts.compact;
		this.history = []; // [{role, content}], kept client-side only
		this.busy = false;
		this.make_layout();
	}

	make_layout() {
		this.$container = $(`
			<div class="howto-assistant ${this.compact ? "howto-assistant--compact" : ""}">
				<div class="howto-banner text-muted">
					${__(
						"This assistant only explains how to use ERPNext features - it does not view, generate, or change your company's data or reports."
					)}
					<br>
					<span dir="rtl">${__(
						"هذا المساعد يشرح فقط طريقة استخدام شاشات ERPNext، ولا يطّلع على بيانات شركتك أو تقاريرها ولا يعدّلها."
					)}</span>
				</div>
				<div class="howto-messages"></div>
				<div class="howto-input-row">
					<textarea
						class="form-control howto-input"
						rows="1"
						placeholder="${__("Ask how to do something in ERPNext... / اسأل كيف تنفّذ أمرًا في ERPNext")}"
					></textarea>
					<button class="btn btn-primary howto-send">${__("Send")}</button>
				</div>
			</div>
		`).appendTo(this.$parent);

		this.$messages = this.$container.find(".howto-messages");
		this.$input = this.$container.find(".howto-input");
		this.$send = this.$container.find(".howto-send");

		this.show_empty_state();

		this.$send.on("click", () => this.send());
		this.$input.on("keydown", (e) => {
			if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				this.send();
			}
		});
	}

	show_empty_state() {
		const $wrap = $(`<div class="howto-suggestions"></div>`);
		$wrap.append(
			`<div class="howto-empty">${__('Ask a "how to" question to get started, or try one of these:')}</div>`
		);
		HOWTO_STARTER_QUESTIONS.forEach((q) => {
			const $chip = $(`
				<div class="howto-suggestion-chip">
					<div dir="rtl">${q.ar}</div>
					<div class="text-muted howto-suggestion-en">${q.en}</div>
				</div>
			`);
			$chip.on("click", () => {
				this.$input.val(q.ar);
				this.send();
			});
			$wrap.append($chip);
		});
		this.$messages.html($wrap);
	}

	send() {
		if (this.busy) return;

		const text = (this.$input.val() || "").trim();
		if (!text) return;

		this.$input.val("");
		this.render_message("user", text);
		this.history.push({ role: "user", content: text });
		this.set_busy(true);

		frappe.call({
			method: "erpnext_howto_assistant.utils.howto_assistant.ask",
			args: { question: text, history: this.history.slice(0, -1) },
			callback: (r) => {
				const answer = r.message && r.message.answer;
				if (answer) {
					this.render_message("assistant", answer, r.message.actions);
					this.history.push({ role: "assistant", content: answer });
				}
			},
			error: (r) => {
				// frappe.call's error callback gets either the parsed server
				// response body, or (for status codes it doesn't specially
				// handle, e.g. a network failure) the raw jqXHR as-is - tell
				// them apart by duck-typing on `status` and surface whichever
				// we got so this isn't a silent dead end.
				const xhr = r && typeof r.status === "number" ? r : null;
				const detail = xhr
					? `HTTP ${xhr.status} ${xhr.statusText || ""}: ${(xhr.responseText || "").slice(0, 300)}`
					: (r && (r._server_messages || r.exception)) || JSON.stringify(r || {});
				console.error("How-To Assistant call failed:", r);
				this.render_message("system", `${__("Could not get an answer. Please try again.")} (${detail})`);
			},
			always: () => this.set_busy(false),
		});
	}

	set_busy(busy) {
		this.busy = busy;
		this.$send.prop("disabled", busy).text(busy ? __("Thinking...") : __("Send"));
	}

	render_message(role, content, actions) {
		this.$messages.find(".howto-suggestions").remove();

		const is_arabic = HOWTO_ARABIC_RE.test(content);
		const dir = is_arabic ? "rtl" : "ltr";
		const align = is_arabic ? "right" : "left";

		const $msg = $(`
			<div class="howto-msg ${role}">
				<div class="howto-bubble" dir="${dir}" style="text-align: ${align};"></div>
			</div>
		`);
		$msg.find(".howto-bubble").text(content);
		this.$messages.append($msg);

		// "Clickable steps": buttons computed server-side from the matched
		// knowledge entries (see howto_assistant._collect_actions), not parsed
		// out of the model's own prose - so they always land on a real route.
		if (actions && actions.length) {
			const $actions = $(`<div class="howto-actions"></div>`);
			actions.forEach((action) => {
				const $btn = $(`<button class="howto-action-btn" type="button"></button>`).text(action.label);
				$btn.on("click", () => howto_goto_route(action.route));
				$actions.append($btn);
			});
			this.$messages.append($actions);
		}

		this.$messages.scrollTop(this.$messages[0].scrollHeight);
	}
};

// Floating button + slide-in drawer, mounted once at desk boot on every
// page when the signed-in user is allowed to see it (frappe.boot.howto_assistant_visible,
// computed server-side in howto_assistant.extend_bootinfo so this never has
// to guess at permissions client-side).
erpnext_howto_assistant.mount_howto_widget = function () {
	if (document.getElementById("howto-fab")) return; // already mounted

	const $fab = $(`
		<div id="howto-fab" title="${__("How-To Assistant")}">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path d="M4 4h16v12H7l-3 3V4z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
				<circle cx="9" cy="10" r="1" fill="currentColor"/>
				<circle cx="12" cy="10" r="1" fill="currentColor"/>
				<circle cx="15" cy="10" r="1" fill="currentColor"/>
			</svg>
		</div>
	`).appendTo("body");

	const $drawer = $(`
		<div id="howto-drawer" class="howto-drawer">
			<div class="howto-drawer-header">
				<span>${__("AI How-To Assistant")}</span>
				<span class="howto-drawer-close">&times;</span>
			</div>
			<div class="howto-drawer-body"></div>
		</div>
	`).appendTo("body");

	let chat = null;

	function toggle_drawer(open) {
		$drawer.toggleClass("open", open);
		$fab.toggleClass("open", open);
		if (open && !chat) {
			chat = new erpnext_howto_assistant.HowToChat($drawer.find(".howto-drawer-body"), { compact: true });
		}
	}

	$fab.on("click", () => toggle_drawer(!$drawer.hasClass("open")));
	$drawer.find(".howto-drawer-close").on("click", () => toggle_drawer(false));
};

$(document).ready(function () {
	if (frappe.session.user === "Guest") return;
	if (!frappe.boot || !frappe.boot.howto_assistant_visible) return;
	erpnext_howto_assistant.mount_howto_widget();
});
