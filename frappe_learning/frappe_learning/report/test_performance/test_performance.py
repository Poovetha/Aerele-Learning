# Copyright (c) 2026, Poovetha and contributors
import frappe
import json
from frappe.utils import nowdate, add_days


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    chart = get_chart_data(data)
    summary = get_summary(data)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": "Employee (Mentee)",
            "fieldname": "mentee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180,
        },
        {
            "label": "Avg Score",
            "fieldname": "avg_score",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "Strong Areas",
            "fieldname": "strong",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Weak Areas",
            "fieldname": "weak",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Last Score",
            "fieldname": "last_score",
            "fieldtype": "Float",
            "width": 100,
        },
    ]


def get_data(filters):
    user = frappe.session.user
    roles = frappe.get_roles(user)

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

    if "Chief Technical Officer" in roles or "System Manager" in roles:
        mentees = frappe.db.sql("""
            SELECT name, employee_name
            FROM `tabEmployee`
            WHERE reports_to IS NOT NULL
        """, as_dict=True)

    elif employee:
        mentees = frappe.db.sql("""
            SELECT name, employee_name
            FROM `tabEmployee`
            WHERE reports_to = %s
        """, (employee,), as_dict=True)

    else:
        mentees = []

    report = []

    for m in mentees:

        records = frappe.get_all(
            "Test Answer",
            filters={"name_of_mentee": m.name},
            fields=["score", "feedback", "creation"]
        )

        if not records:
            continue

        total_score = 0
        strong_all = []
        weak_all = []

        for r in records:
            total_score += r.score or 0

            if r.feedback:
                try:
                    ai = json.loads(r.feedback)
                    strong_all += ai.get("strong_concepts", [])
                    weak_all += ai.get("weak_concepts", [])
                except:
                    pass

        avg_score = total_score / len(records)

        if avg_score >= 7:
            strong_all.append("Overall Performance")
        elif avg_score < 4:
            weak_all.append("Overall Performance")

        strong = list(set(strong_all))
        weak = list(set(weak_all))

        # 🔹 Last test score
        last_record = sorted(records, key=lambda x: x.creation, reverse=True)[0]
        last_score = last_record.score

        report.append({
            "mentee": m.name, 
            "avg_score": round(avg_score, 2),
            "strong": ", ".join(strong) or "-",
            "weak": ", ".join(weak) or "-",
            "last_score": last_score,
        })

    return report


def get_chart_data(data):
    if not data:
        return None

    return {
        "data": {
            "labels": [d["mentee"] for d in data],
            "datasets": [
                {
                    "name": "Avg Score",
                    "values": [d["avg_score"] for d in data],
                }
            ],
        },
        "type": "bar",
    }


def get_summary(data):
    if not data:
        return []

    avg = sum(d["avg_score"] for d in data) / len(data)
    top = sorted(data, key=lambda x: x["avg_score"], reverse=True)[0]

    weak_count = sum(1 for d in data if d["avg_score"] < 5)

    return [
        {"label": "Overall Avg Score", "value": round(avg, 2), "indicator": "Green"},
        {"label": "Top Performer", "value": top["mentee"], "indicator": "Blue"},
        {"label": "Low Performers", "value": weak_count, "indicator": "Red"},
    ]

@frappe.whitelist()
def get_top_mentees():
    last_week = add_days(nowdate(), -7)

    return frappe.db.sql("""
        SELECT 
            name_of_mentee as mentee,
            ROUND(AVG(score), 2) as avg_score,
            COUNT(score) as test_count
        FROM `tabTest Answer`
        WHERE creation BETWEEN %s AND NOW()
        GROUP BY name_of_mentee
        ORDER BY avg_score DESC, test_count DESC
        LIMIT 5
    """, (last_week,), as_dict=True)