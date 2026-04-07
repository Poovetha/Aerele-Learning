# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DailyTest(Document):
	def before_submit(self):
		mentor_user = frappe.get_value("Employee", self.mentor, "user_id")

		if frappe.session.user == mentor_user:
			frappe.throw("You can't submit your own test")

	def on_submit(self):
		emails = frappe.get_all("Employee", filters={"reports_to": self.mentor}, pluck="personal_email")
		print(emails)

		for e in emails:
			print(e)
			if not e:
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
		frappe.sendmail(recipients=emails, subject=subject, message=message)
		frappe.publish_realtime(event="notification", user=emails, message="New Daily Test is Live!")
