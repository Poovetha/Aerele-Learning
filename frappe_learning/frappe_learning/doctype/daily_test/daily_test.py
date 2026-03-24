# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DailyTest(Document):
	pass

@frappe.whitelist()
def timer():
	dur = frappe.get_single("FL Settings")
	duration = dur.duration
	start_time = dur.start_time
	end_time = dur.end_time
	
