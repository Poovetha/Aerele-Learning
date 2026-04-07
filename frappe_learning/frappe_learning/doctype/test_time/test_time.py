# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today

class TestTime(Document):
    def on_update(self):
        if self.status == "Approved":
            apply_extra_time(self)


def apply_extra_time(doc):

    test_answer = frappe.db.get_value(
        "Test Answer",
        {
            "name_of_mentee": doc.mentee,
            "creation": ["like", f"{today()}%"],
        },
        ["name", "extra_time"]
    )

    if not test_answer:
        frappe.log_error("No")
        return

    new_extra_time = (test_answer.extra_time or 0) + doc.approved_time

    frappe.db.set_value(
        "Test Answer",
        test_answer.name,
        "extra_time",
        new_extra_time
    )

