// Copyright (c) 2026, Poovetha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Concept Questions", {
    concept(frm, cdt, cdn) {

        let row = locals[cdt][cdn];
        row.question = "";
        frm.refresh_field("concept_questions");

        frappe.model.set_query(cdt, cdn, "question", function() {
            return {
                filters: {
                    concept: row.concept
                }
            };
        });
    }
});
