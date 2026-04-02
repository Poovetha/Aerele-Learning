import frappe
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

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    conditions = ""
    values = []

    if from_date and to_date:
        conditions += " AND ta.creation BETWEEN %s AND %s"
        values.extend([from_date, to_date])

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

    if "Chief Technical Officer" in roles or "System Manager" in roles:
        mentees = frappe.db.sql("""
            SELECT name FROM `tabEmployee`
            WHERE reports_to IS NOT NULL
        """, as_dict=True)

    elif employee:
        mentees = frappe.db.sql("""
            SELECT name FROM `tabEmployee`
            WHERE reports_to = %s
        """, (employee,), as_dict=True)

    else:
        mentees = []

    report = []

    for m in mentees:

        scores = frappe.db.sql(f"""
            SELECT 
                ta.score,
                ta.creation,
                ta.feedback,
                child.concept
            FROM `tabTest Answer` ta
            LEFT JOIN `tabAnswers` child
                ON child.parent = ta.name
            WHERE ta.name_of_mentee = %s {conditions}
        """, [m.name] + values, as_dict=True)

        if not scores:
            continue

        total_score = 0
        concept_map = {}

        ai_strong = set()
        ai_weak = set()

        for s in scores:
            total_score += s.score

            concept = s.concept or "General"

            if concept not in concept_map:
                concept_map[concept] = []

            concept_map[concept].append(s.score)

            feedback = (s.feedback or "").lower()

            if "good" in feedback or "strong" in feedback:
                ai_strong.add(concept)

            if "weak" in feedback or "poor" in feedback:
                ai_weak.add(concept)

        avg_score = total_score / len(scores)

        strong = []
        weak = []

        for concept, vals in concept_map.items():
            avg = sum(vals) / len(vals)

            if avg >= 70 or concept in ai_strong:
                strong.append(concept)

            elif avg < 50 or concept in ai_weak:
                weak.append(concept)

        last_score = sorted(scores, key=lambda x: x.creation, reverse=True)[0].score

        report.append({
            "mentee": m.name,
            "avg_score": round(avg_score, 2),
            "strong": ", ".join(set(strong)) or "-",
            "weak": ", ".join(set(weak)) or "-",
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
                {"name": "Avg Score", "values": [d["avg_score"] for d in data]}
            ],
        },
        "type": "bar",
    }


def get_summary(data):
    if not data:
        return []

    avg = sum(d["avg_score"] for d in data) / len(data)
    top = sorted(data, key=lambda x: x["avg_score"], reverse=True)[0]
    weak_count = sum(1 for d in data if d["avg_score"] < 50)

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
        WHERE creation >= %s
        GROUP BY name_of_mentee
        ORDER BY avg_score DESC, test_count DESC
        LIMIT 5
    """, (last_week,), as_dict=True)