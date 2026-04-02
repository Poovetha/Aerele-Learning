# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QuestionandAnswer(Document):
	def before_submit(self):
		mentor = frappe.get_value("Employee", {"name": self.mentor}, ["user_id"])
		if frappe.session.user == mentor:
			frappe.throw("You cant sumbit your own question")
