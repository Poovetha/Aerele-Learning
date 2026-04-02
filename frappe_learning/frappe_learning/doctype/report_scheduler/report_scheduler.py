# Copyright (c) 2026, Poovetha and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, get_datetime


class ReportScheduler(Document):
    def validate(self):

        now = now_datetime()
        base = now

        if self.run_time:
            time_obj = get_datetime(str(self.run_time)).time()
            base = now.replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=time_obj.second,
                microsecond=0
            )

        if base <= now:

            if self.schedule_type == "Daily":
                base = add_days(base, 1)

            elif self.schedule_type == "Weekly":
                base = add_days(base, 7)

            elif self.schedule_type == "3 Weeks":
                base = add_days(base, 21)

        self.next_run = base