import frappe
from frappe.email.doctype.notification.notification import Notification
from frappe_learning.telegram import send_telegram_message


class CustomNotification(Notification):

    def send(self, doc):

        print("Im in custom  Pooooooooooooooooooooooooooooooooooooooooooo")
        
        if self.channel != "Telegram":
            print("Im channnel Pooooooooooooooooooooooooooooooooooooooooooo")
            return super().send(doc)

        message = frappe.render_template(self.message, {"doc": doc})

        chat_ids = []

        if doc.doctype == "Daily Test":

            employees = frappe.get_all(
                "Employee",
                filters={"reports_to": doc.mentor},
                fields=["user_id"]
            )

            for emp in employees:
                if emp.user_id:
                    chat_id = frappe.db.get_value("User", emp.user_id, "telegram_chat_id")
                    if chat_id:
                        chat_ids.append(chat_id)

        elif doc.doctype == "Test Time":
            mentor = frappe.get_value("Employee", doc.mentee, "reports_to")
            mentor_user = frappe.get_value("Employee", mentor, "user_id")

            if mentor_user:
                chat_id = frappe.db.get_value("User", mentor_user, "telegram_chat_id")
                if chat_id:
                    chat_ids.append(chat_id)

            cto_users = frappe.get_all(
                "Has Role",
                filters={"role": "Chief Technical Officer"},
                pluck="parent"
            )

            for user in cto_users:
                chat_id = frappe.db.get_value("User", user, "telegram_chat_id")
                if chat_id:
                    chat_ids.append(chat_id)

        elif doc.doctype == "Test Answer":

            employee = doc.name_of_mentee

            user = frappe.get_value("Employee", employee, "user_id")

            if user:
                chat_id = frappe.db.get_value("User", user, "telegram_chat_id")
                if chat_id:
                    chat_ids.append(chat_id)

        for chat_id in set(chat_ids):
            send_telegram_message(chat_id, message)