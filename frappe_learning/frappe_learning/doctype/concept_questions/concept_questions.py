# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ConceptQuestions(Document):
	def autoname(self):
		if self.concept:
			self.name = make_autoname("QUESTION-.#####")
