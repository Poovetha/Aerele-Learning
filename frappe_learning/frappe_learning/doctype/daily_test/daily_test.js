// Copyright (c) 2026, Poovetha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Test", {
    // refresh(frm) {
        
    // },
    concept(frm){
        frm.set_query("question", function() {
            return {
                filters: {
                    concept: frm.doc.concept
                }
            };
        });
    }
});
