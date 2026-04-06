import re
import frappe
import requests
from frappe.utils import add_days, add_to_date, get_time, now_datetime, today


@frappe.whitelist()
def get_daily_test():
	user = frappe.session.user

	employee = frappe.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return {}

	mentor = frappe.get_value("Employee", employee, "reports_to")

	settings = frappe.get_single("FL Settings")
	duration = settings.duration
	start_time = get_time(settings.start_time)
	end_time = get_time(settings.end_time)

	now = now_datetime()

	if now.time() < start_time:
		return {"status": "not_started"}

	if now.time() > end_time:
		return {"status": "ended"}

	test = frappe.get_all(
		"Daily Test",
		filters={
			"mentor": mentor,
			"test_date": today(),
			"workflow_state": "Approved"
		},
		fields=["name"],
		limit_page_length=1,
	)

	if not test:
		return {"status": "no_test"}

	test_doc = frappe.get_doc("Daily Test", test[0].name)

	questions = [
		{"question": q.question, "concept": q.concept}
		for q in test_doc.question_and_answer
	]

	test_answer = frappe.db.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["between", [today(), add_days(today(), 1)]],
		},
		["name", "start_time", "extra_time"],
		as_dict=True,
	)

	if not test_answer:
		doc = frappe.get_doc({
			"doctype": "Test Answer",
			"name_of_mentee": employee,
			"start_time": now
		})
		doc.insert(ignore_permissions=True)

		start_time_user = now
		extra_time = 0
	else:
		start_time_user = test_answer.start_time
		extra_time = test_answer.extra_time or 0

	personal_end_time = add_to_date(
		start_time_user,
		minutes=(duration + extra_time)
	)

	return {
		"status": "not_started_test",
		"questions": questions,
		"personal_end_time": personal_end_time
	}


@frappe.whitelist()
def duplicate():
	employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, "name")

	doc = frappe.db.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["between", [today(), add_days(today(), 1)]],
		},
		["name"],
		as_dict=True
	)

	if not doc:
		return {"duplicate": "No"}

	has_answers = frappe.db.exists(
		"Answers",
		{"parent": doc.name}
	)

	return {"duplicate": "Yes" if has_answers else "No"}


@frappe.whitelist()
def save_test_answer(answers):
	user = frappe.session.user
	employee = frappe.get_value("Employee", {"user_id": user}, "name")

	settings = frappe.get_single("FL Settings")
	duration = settings.duration

	now = now_datetime()

	test_data = frappe.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["between", [today(), add_days(today(), 1)]],
		},
		["name", "start_time", "extra_time"],
		as_dict=True,
	)

	if not test_data:
		frappe.throw("Test not started properly")

	start_time = test_data.start_time
	extra_time = test_data.extra_time or 0

	personal_end = add_to_date(start_time, minutes=(duration + extra_time))

	answers = frappe.parse_json(answers)

	doc = frappe.get_doc("Test Answer", test_data.name)
	doc.question_and_answer = []

	result = []

	for ans in answers:
		question = ans.get("question")
		user_answer = ans.get("answer") or "Not Answered"

		q_data = frappe.get_all(
			"Testing",
			filters={"question": question, "is_group": 0},
			fields=["answer"],
			limit_page_length=1
		)

		mentor_answer = q_data[0].answer if q_data else ""

		doc.append(
			"question_and_answer",
			{
				"question": question,
				"answer": user_answer,
				"mentor_answer": mentor_answer,
			},
		)

		result.append({
			"question": question,
			"user_answer": user_answer,
			"mentor_answer": mentor_answer
		})

	doc.save(ignore_permissions=True)

	frappe.enqueue(
		method="frappe_learning.api.ai_report",
		queue="default",
		timeout=300,
		answers=answers,
		mentee=user
	)

	return result


def ai_report(answers, mentee):
	employee = frappe.get_value("Employee", {"user_id": mentee}, "name")

	doc_name = frappe.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["between", [today(), add_days(today(), 1)]],
		},
		"name",
	)

	if not doc_name:
		return

	doc = frappe.get_doc("Test Answer", doc_name)

	qa_list = []

	for ans in answers:
		question = ans.get("question")
		concept = ans.get("concept")
		mentee_answer = ans.get("answer")

		mentor_answer = frappe.db.get_value(
			"Testing",
			{"question": question, "is_group": 0},
			"answer"
		)

		qa_list.append({"concepts": concept, "mentor": mentor_answer, "mentee": mentee_answer})

	overall_result = evaluate_overall(qa_list)

	doc.score = extract_score(overall_result)
	doc.feedback = overall_result

	doc.save(ignore_permissions=True)


def evaluate_overall(qa_list):

	url = "http://localhost:11434/api/generate"

	text = ""

	for i, qa in enumerate(qa_list, 1):
		text += (
			f"\nQ{i}:\n"
			f"Concept: {qa.get('concept') or qa.get('concepts')}\n"
			f"Mentor Answer: {qa.get('mentor', '')}\n"
			f"Mentee Answer: {qa.get('mentee', '')}\n"
		)

	prompt = f"""
MASTER PROMPT — AI ANALYSER (Ultra-Strict | Zero-Teaching | Python • MySQL • Frappe)

ROLE: AI Analyser (Expert Evaluator | Concept Scorer | Ultra-Strict)

DOMAIN: Concept Evaluation (Python, MySQL, Frappe — infer exact concept from Mentor Answer)

TASK: Compare Mentor vs Mentee Answer and score ONLY based on conceptual understanding (not wording). Give concise diagnostic feedback. NO teaching, NO corrections.

---

EVALUATION LOGIC:

1) Identify exact concept from Mentor Answer  
2) Judge mentee understanding:
   - Deep / Good / Partial / Weak / None  
3) Validate:
   - Captures WHAT + WHY?  
   - Logic aligned?  
   - Different correct explanation = valid  
   - Superficial/keyword match = invalid  

4) Classify:
   - Strong Concept (Deep/Good)  
   - Concept to Concentrate (Partial/Weak/None)  
   → MUST name concept  

5) Score:
   9–10 Deep | 7–8 Good | 5–6 Partial | 3–4 Weak | 0–2 None  
   ✔ Understanding > wording/syntax  
   ✔ If unsure → lower score  

---

RULES:
- Use ONLY Mentor & Mentee answers  
- No teaching / suggestions / corrections / rewrites  
- No assumptions beyond mentor context  

---

OUTPUT (STRICT):

overall score : ?/10 
Feedback: <1–3 lines on understanding + correctness>  
Concept to concentrate: <concept OR "None">

---

FINAL: Reward true understanding. Penalize superficial or wrong reasoning. Focus ONLY on concept.
{text}
"""

	payload = {
			"model": "llama3.1:8b",
			"prompt": prompt,
			"stream": False
		}

	response = requests.post(url, json=payload)

	result = response.json()
	frappe.log_error(result)

	full_response = result.get("response", "")

	print("FAHHHH",full_response)

	return full_response

def extract_score(text):
	match = re.search(r"score\s*:\s*(\d+)/10", text, re.IGNORECASE)
	return int(match.group(1)) if match else 0


@frappe.whitelist()
def create_issue_request(reason, time):
	user = frappe.session.user
	mentee = frappe.get_value("Employee", {"user_id": user}, "name")
	mentor = frappe.get_value("Employee", mentee, "reports_to")

	if frappe.db.exists(
		"Test Time",
		{
			"mentee": mentee,
			"status": "Pending",
			"creation": ["between", [today(), add_days(today(), 1)]],
		},
	):
		frappe.throw("Already requested extra time")

	test = frappe.get_all(
		"Daily Test",
		filters={
			"mentor": mentor,
			"test_date": today(),
			"workflow_state": "Approved"
		},
		fields=["name"],
		limit_page_length=1,
	)

	if not test:
		frappe.throw("No test found")

	doc = frappe.new_doc("Test Time")
	doc.mentee = mentee
	doc.test = test[0].name
	doc.extra_min = time
	doc.reason = reason
	doc.status = "Pending"

	doc.insert(ignore_permissions=True)

	send_notification(mentor, doc.name)

	return True


def send_notification(mentor, docname):
	mentor_user = frappe.get_value("Employee", mentor, "user_id")

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": "New Time Request",
		"email_content": "Mentee requested extra time.",
		"for_user": mentor_user,
		"type": "Alert",
		"document_type": "Test Time",
		"document_name": docname,
	}).insert(ignore_permissions=True)

	frappe.publish_realtime(event="notification", user=mentor_user)

def run_scheduled_reports():
	now = now_datetime()

	docs = frappe.get_all(
		"Report Scheduler",
		filters={
			"enabled": 1,
			"next_run": ["<=", now]
		},
		fields=["name"]
	)

	for d in docs:
		doc = frappe.get_doc("Report Scheduler", d.name)

		from frappe_learning.frappe_learning.report.test_performance.test_performance import get_data
		data = get_data({})

		frappe.logger().info(f"Report executed for {doc.name}")

		if doc.schedule_type == "Daily":
			doc.next_run = add_days(doc.next_run, 1)

		elif doc.schedule_type == "Weekly":
			doc.next_run = add_days(doc.next_run, 7)

		elif doc.schedule_type == "3 Weeks":
			doc.next_run = add_days(doc.next_run, 21)

		doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_dashboard_data():
	from frappe_learning.frappe_learning.report.test_performance.test_performance import get_data
	return get_data({})