import re
import frappe
import requests
from frappe_learning.frappe_learning.report.test_performance.test_performance import get_data
from frappe.utils import add_days, get_time, now_datetime, today,now_datetime,add_to_date

@frappe.whitelist()
def get_daily_test():
	employee_data = frappe.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		["name"]
	)
	print(employee_data)

	if not employee_data:
		return {}

	mentor = frappe.get_value("Employee",
						   {"name":employee_data},
						   ["reports_to"])

	settings = frappe.get_single("FL Settings")
	start_time = get_time(settings.start_time)
	end_time = get_time(settings.end_time)
	duration = settings.duration  

	now = now_datetime()
	current_time = now.time()

	if current_time < start_time:
		return {"status": "not_started"}

	if current_time > end_time:
		return {"status": "ended"}

	test_name = frappe.db.get_value(
		"Daily Test",
		{
			"mentor": mentor,
			"test_date": today(),
			"workflow_state": "Approved"
		},
		["name"]
	)

	if not test_name:
		return {"status": "no_test"}
	
	doc = frappe.get_doc({
			"doctype": "Test Answer",
			"name_of_mentee": employee_data,
			"start_time": now
		})
	doc.insert(ignore_permissions=True)

	questions = frappe.get_all(
		"Concept Questions",
		filters={"parent": test_name},
		fields=["question", "concept"]
	)

	personal_end_time = add_to_date(now, minutes=duration)

	return {
		"status": "not_started_test",
		"test": test_name,
		"questions": questions,
		"personal_end_time": str(personal_end_time)
	}

@frappe.whitelist()
def duplicate():
	employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, "name")

	doc = frappe.db.exists(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["like", f"{today()}%"],
		},
	)

	print("Fghjk",doc)

	if doc:
		return {"duplicate": "No"}
	else:
		return {"duplicate": "Yes"}

@frappe.whitelist()
def save_test_answer(answers):

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		"name"
	)

	if not employee:
		frappe.throw("Employee not found")

	test_name = frappe.db.exists(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["like", f"{today()}%"],
		}
	)

	if not test_name:
		frappe.throw("Test not started properly")

	answers = frappe.parse_json(answers)
	
	questions = []

	for ans in answers:
		question = ans.get("question")
		if question:
			questions.append(question)

	mentor_data = frappe.get_all(
		"Testing",
		filters={
			"question": ["in", questions],
			"is_group": 0
		},
		fields=["question", "answer"]
	)

	mentor_map = {}

	for d in mentor_data:
		mentor_map[d.question] = d.answer

	doc = frappe.get_doc("Test Answer", test_name)
	doc.question_and_answer = []

	result = []

	for ans in answers:
		question = ans.get("question")
		user_answer = ans.get("answer") or "Not Answered"

		mentor_answer = mentor_map.get(question, "")

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

	doc.save()

	frappe.enqueue(
		method="frappe_learning.api.ai_report",
		queue="default",
		timeout=300,
		answers=answers,
		mentee=frappe.session.user
	)

	return result

def ai_report(answers, mentee):

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": mentee},
		"name"
	)

	doc_name = frappe.db.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["like", f"{today()}%"],
		},
		"name",
	)

	if not doc_name:
		return

	answers = frappe.parse_json(answers)

	questions = []
	for ans in answers:
		if ans.get("question"):
			questions.append(ans.get("question"))

	mentor_data = frappe.get_all(
		"Testing",
		filters={
			"question": ["in", questions],
			"is_group": 0
		},
		fields=["question", "answer"]
	)

	mentor_ans = {}
	for d in mentor_data:
		mentor_ans[d.question] = d.answer

	qa_list = []

	for ans in answers:
		question = ans.get("question")
		concept = ans.get("concept")
		mentee_answer = ans.get("answer")

		mentor_answer = mentor_ans.get(question, "")

		qa_list.append({
			"concepts": concept,
			"mentor": mentor_answer,
			"mentee": mentee_answer
		})

	print("TEST")	

	overall_result = evaluate_overall(qa_list)

	doc = frappe.get_doc("Test Answer", doc_name)
	doc.score = extract_score(overall_result)
	doc.feedback = overall_result

	doc.save(ignore_permissions=True)

def evaluate_overall(qa_list):

	url = "http://localhost:11434/api/generate"

	text = ""

	print("Answer")

	for i, qa in enumerate(qa_list, 1):
		text += (
			f"\nQ{i}:\n"
			f"Concept: {qa.get('concepts')}\n"
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
	print("test")

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

	emp = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		["name", "reports_to"],
		as_dict=True
	)

	if not emp:
		frappe.throw("Employee not found")

	mentee = emp.name
	mentor = emp.reports_to

	if not mentor:
		frappe.throw("Mentor not assigned")

	if frappe.db.exists(
		"Test Time",
		{
			"mentee": mentee,
			"status": "Pending",
			"creation": ["like", f"{today()}%"],
		},
	):
		frappe.throw("Already requested extra time")

	test_name = frappe.db.get_value(
		"Daily Test",
		{
			"mentor": mentor,
			"test_date": today(),
			"workflow_state": "Approved"
		},
		"name"
	)

	if not test_name:
		frappe.throw("No test found")

	doc = frappe.new_doc("Test Time")
	doc.mentee = mentee
	doc.test = test_name
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

	docs = frappe.get_all(
		"Report Scheduler",
		filters={
			"enabled": 1,
			"next_run": ["<=", now_datetime()]
		},
		fields=["name", "schedule_type", "next_run"]
	)

	day_count = {
		"Daily": 1,
		"Weekly": 7,
		"3 Weeks": 21
	}

	for d in docs:
		get_data({})

		days = day_count.get(d.schedule_type, 1)
		next_run = add_days(d.next_run, days)

		frappe.db.set_value(
			"Report Scheduler",
			d.name,
			"next_run",
			next_run
		)

@frappe.whitelist()
def get_extra_time():
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		"name"
	)

	test = frappe.db.get_value(
		"Test Answer",
		{
			"name_of_mentee": employee,
			"creation": ["like", f"{today()}%"],
		},
		["extra_time"]
	)

	return test.extra_time


@frappe.whitelist()
def get_dashboard_data():
	return get_data({})