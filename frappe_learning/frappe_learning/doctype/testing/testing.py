# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
from frappe.model.naming import make_autoname

class Testing(NestedSet):


	def autoname(self):
		if self.is_group:
			if not self.title:
				frappe.throw("Concept name is required")

			self.name = self.title

			if frappe.db.exists(self.doctype, self.name):
				frappe.throw(f"Concept '{self.name}' already exists")

		else:
			self.name = make_autoname("QUESTION-.#####")
