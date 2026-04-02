/* global frappe_learning */
frappe.provide("frappe_learning.daily_assessment");

frappe.pages["daily-assessment"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Daily Test",
		single_column: true,
	});

	frappe_learning.daily_assessment.page = page;
	frappe_learning.daily_assessment.load(page);
};

frappe_learning.daily_assessment.load = function (page) {
	this.page = page;
	this.container = $('<div class="daily-test-container"></div>').appendTo(page.body);

	this.is_submitted = false;

	this.container.append(`<b>Mentee</b> = ${frappe.session.user}<br><br>`);

	if (localStorage.getItem("test_active")) {
		this.container.html(
			`<p style="color:red; text-align:center;">Test already open in another tab</p>`
		);
		return;
	}
	localStorage.setItem("test_active", "true");

	window.onbeforeunload = () => {
		localStorage.removeItem("test_active");
	};

	frappe.call({
		method: "frappe_learning.api.duplicate",
		callback: (r) => {
			if (r.message.duplicate === "Yes") {
				this.container.append(`
					<p style="text-align:center; font-weight:bold; margin-top:20px;">
						Test already completed!
					</p>
				`);
				return;
			}

			this.get_questions();

			// ✅ SUBMIT BUTTON
			page.set_primary_action("Submit", () => {
				if (this.is_submitted) return;
				this.submit_test();
			});

			// ✅ RAISE ISSUE BUTTON
			page.set_secondary_action("Raise Issue", () => {
				if (this.is_submitted) return;
				this.raise_issue();
			});
		},
	});
};

frappe_learning.daily_assessment.get_questions = function () {
	frappe.call({
		method: "frappe_learning.api.get_daily_test",
		callback: (r) => {
			let data = r.message;

			if (data.status === "no_test") {
				this.container.html(
					`<p style="text-align:center; font-weight:bold; margin-top:20px;">No test assigned today</p>`
				);
				return;
			}

			if (data.status === "not_started") {
				this.container.html(
					`<p style="text-align:center;"><b>Test not started yet</b></p>`
				);
				return;
			}

			if (data.status === "ended") {
				this.container.html(
					`<p style="color:red; text-align:center;">Test time is over</p>`
				);
				return;
			}

			if (data.status === "not_started_test") {
				this.show_dashboard(data);
			}
		},
	});
};

frappe_learning.daily_assessment.show_dashboard = function (data) {
	this.container.html(`
		<div style="text-align:center; padding:20px;">
			<h2>Daily Test</h2>
			<p>Questions: ${data.questions.length}</p>
			<p>⏱ Duration: 45 Minutes</p>
			<button id="startTestBtn" class="btn btn-primary">Start Test</button>
		</div>
	`);

	$(document)
		.off("click", "#startTestBtn")
		.on("click", "#startTestBtn", () => {
			this.start_test(data);
		});
};

frappe_learning.daily_assessment.start_test = function (data) {
	this.container.empty();

	// ⏱ TIMER UI
	this.container.append(`
		<div style="margin-bottom:15px;">
			⏱ Time Remaining: <span class="dashboard-timer"></span>
		</div>
	`);

	this.render_questions(data.questions);
	this.start_timer(data.personal_end_time);
};

frappe_learning.daily_assessment.render_questions = function (questions) {
	questions.forEach((q, index) => {
		this.container.append(`
			<div style="margin-bottom:20px;">
				<p><b>Q${index + 1}:</b> ${q.question}</p>
				<input type="text"
					class="answer form-control"
					data-question="${q.question}"
					data-concept="${q.concept}"
					placeholder="Type your answer..." />
			</div>
		`);
	});
};

frappe_learning.daily_assessment.start_timer = function (end_time) {
	let endTime = new Date(end_time).getTime();
	let timer = $(".dashboard-timer");

	this.timer_interval = setInterval(() => {
		let remaining = Math.floor((endTime - Date.now()) / 1000);

		if (remaining <= 0) {
			clearInterval(this.timer_interval);

			if (!this.is_submitted) {
				frappe.msgprint("Time up! Auto submitting...");
				this.submit_test(true);
			}
			return;
		}

		let mins = Math.floor(remaining / 60);
		let secs = remaining % 60;

		timer.text(`${mins}:${secs < 10 ? "0" : ""}${secs}`);

		if (remaining <= 300) {
			timer.css("color", "red");
		}
	}, 1000);
};

frappe_learning.daily_assessment.submit_test = function (auto = false) {
	if (this.is_submitted) return;

	this.is_submitted = true;

	let answers = [];
	let has_error = false;

	this.container.find(".answer").each(function () {
		let val = $(this).val().trim();

		if (!val && !auto) {
			has_error = true;
			$(this).css("border", "2px solid red");
		} else {
			answers.push({
				question: $(this).data("question"),
				concept: $(this).data("concept"),
				answer: val || "Not Answered",
			});
		}
	});

	if (has_error) {
		frappe.msgprint("Answer all questions!");
		this.is_submitted = false;
		return;
	}

	// 🔒 LOCK UI
	this.lock_ui();

	frappe.call({
		method: "frappe_learning.api.save_test_answer",
		args: { answers: answers },
		callback: (r) => {
			frappe.msgprint("Test Submitted Successfully");
			this.show_results(r.message);
		},
	});
};

frappe_learning.daily_assessment.lock_ui = function () {
	// ❌ Disable inputs
	this.container.find("input").prop("disabled", true);

	// ❌ Disable buttons
	this.page.btn_primary.prop("disabled", true);
	this.page.btn_secondary.prop("disabled", true);

	// ❌ Remove tab flag
	localStorage.removeItem("test_active");
};

frappe_learning.daily_assessment.show_results = function (results) {
	this.container.empty();

	this.container.append(`<h3 style="text-align:center;">Results</h3>`);

	results.forEach((res, index) => {
		this.container.append(`
			<div>
				<p><b>Q${index + 1}:</b> ${res.question}</p>
				<p><b>Your Answer:</b> ${res.user_answer}</p>
				<p><b>Mentor Answer:</b> ${res.mentor_answer}</p>
			</div>
		`);
	});
};

frappe_learning.daily_assessment.raise_issue = function () {
	if (this.is_submitted) return;

	let d = new frappe.ui.Dialog({
		title: "Request Extra Time",
		fields: [
			{ label: "Time Needed", fieldname: "time", fieldtype: "Int", reqd: 1 },
			{ label: "Reason", fieldname: "reason", fieldtype: "Small Text", reqd: 1 },
		],
		primary_action_label: "Request",
		primary_action(values) {
			frappe.call({
				method: "frappe_learning.api.create_issue_request",
				args: values,
				callback: () => {
					frappe.msgprint("Request sent to your mentor/CTO");
					d.hide();
				},
			});
		},
	});

	d.show();
};
