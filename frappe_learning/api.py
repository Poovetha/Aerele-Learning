import frappe
from frappe.utils import today

def mentee_login(bootinfo):
    user = frappe.session.user
    # frappe.throw("poovitha")
    print("------------------------------------------------------------------------------------------------------")
    frappe.msgprint("Poovitha")
    print(user)

    
    
   
    if user == "Guest":
        return
    elif user =="Software Developer":
        return



    mentees = frappe.get_all(
        "Has Role",
        filters={"role": "Software Developer Intern"},
        pluck="parent"
    )

    # answered = frappe.get_all(
    #     "Test Answer",
    #     filters={
    #         "attended_by": user,
    #         "date": today()
    #     },
    #     pluck="attended_by"
    # )

    if user in mentees:
    #     if user in answered:
        frappe.msgprint("poovitha")
    else:
        frappe.msgprint("priya")
    # else:
    #     bootinfo["test_status"] = "not_applicable"