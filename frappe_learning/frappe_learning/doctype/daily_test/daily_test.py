# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DailyTest(Document):
	def before_insert(self):
		frappe.msgprint("You shouldn't approve your own test questions")

	def on_submit(self):
		emails = frappe.get_all(
			"Employee",
			filters={"reports_to": self.mentor},
			pluck="personal_email"
		)
		print(emails)

		for e in emails :
			print (e)
			if not e :
				pass
			
			
		print("dfghjk")
		subject = f"Daily Test Created: {self.name}"

		message = f"""
		<p>Hello,</p>

		<p>A new <b>Daily Test</b> "<b>{self.name}</b>" has been created by your mentor.</p>

		<p>Please log in and attend the test.</p>

		<p>
		Test Link: 
		<a href="http://127.0.0.1:8011/desk/daily-assessment">
		http://127.0.0.1:8011/desk/daily-assessment
		</a>
		</p>

		<p>Regards,
		<br>Your Team</p>
		"""
		frappe.sendmail(
			recipients=emails,
			subject=subject,
			message=message
		)