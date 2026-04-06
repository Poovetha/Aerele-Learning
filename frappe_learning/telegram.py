import requests
import frappe

def send_telegram_message(chat_id, message):

    url = f"https://api.telegram.org/bot8771876885:AAEOMgp9qdoZlcRYgd7Z6IXwP-Cr7q5vrIo/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    frappe.log_error("Success")

# import requests
# import frappe


# def send_telegram_message(chat_id, message):
#     frappe.log_error("Start")

#     url = f"https://api.telegram.org/bot8771876885:AAEOMgp9qdoZlcRYgd7Z6IXwP-Cr7q5vrIo/sendMessage"


#     payload = {
#         "chat_id": chat_id,
#         "text": message,
#         "parse_mode": "Markdown"
#     }
#     frappe.log_error("start")

#     try:
#         response = requests.post(url, json=payload)

#         frappe.logger().info(f"Telegram Response: {response.text}")

#     except Exception as e:
#         frappe.log_error(str(e), "Telegram Error")


# def send_feedback_message(doc, method):

#     employee = doc.name_of_mentee

#     frappe.log_error(f"Employee: {employee}")

#     user = frappe.get_value(
#         "Employee",
#         employee,
#         "user_id"
#     )

#     frappe.log_error(f"User: {user}")

#     if not user:
#         frappe.log_error("No user")
#         return

#     chat_id = frappe.db.get_value(
#         "User",
#         user,
#         "telegram_chat_id"
#     )

#     frappe.log_error(f"Chat ID: {chat_id}")

#     if not chat_id:
#         frappe.log_error(f"No Telegram ID for {user}")
#         return

#     message = f"""
# *Performance Report*

# *{employee}*
# ━━━━━━━━━━━━━━
# *Score:* `{doc.score}`

#  *CTO/Mentor Feedback:*
# _{doc.mentor_feedback}_

# Keep improving!
# """

#     send_telegram_message(chat_id, message)



# def notify_test_ready(doc,method):

#     employees = frappe.get_all(
#         "Employee",
#         filters={"reports_to": doc.mentor},
#         fields=["user_id"]
#     )

#     for emp in employees:

#         if not emp.user_id:
#             continue

#         chat_id = frappe.db.get_value("User", emp.user_id, "telegram_chat_id")
#         time = frappe.get_single_value("FL Settings","duration")

#         if not chat_id:
#             continue

#         message = f"""
#         *New Test Available!*

#         *{doc.name}*

#         Complete it on time!!.

#         Test Timing : 10 Am to 6 pm
#         Test Duration : {time}

#         All the best!
#         """

#         send_telegram_message(chat_id, message)


# def time_request(doc,method):
#     mentor = frappe.get_value(
#         "Employee",
#         doc.mentee,
#         "reports_to"
#     )

#     mentor_user = frappe.get_value(
#         "Employee",
#         mentor,
#         "user_id"
#     )

#     mentor_chat_id = frappe.db.get_value(
#         "User",
#         mentor_user,
#         "telegram_chat_id"
#     )

#     cto_users = frappe.get_all(
#         "Has Role",
#         filters={"role": "Chief Technical Officer"},
#         pluck="parent"
#     )

#     message = f"""
#  *New Time Request*

# Mentee: {doc.mentee}
# Time Requested: {doc.extra_min} mins
# Reason: {doc.reason}
# """

#     if mentor_chat_id:
#         send_telegram_message(mentor_chat_id, message)

#     for user in cto_users:
#         chat_id = frappe.db.get_value("User", user, "telegram_chat_id")

#         if chat_id:
#             send_telegram_message(chat_id, message)