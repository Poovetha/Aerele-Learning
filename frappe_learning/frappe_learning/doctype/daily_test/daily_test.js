// Copyright (c) 2026, Poovetha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Test", {
    refresh(frm) {
        frm.set_df_property("question_and_answer", "cannot_add_rows", true)
    },

    add_questions: function(frm) {
        let table_data = []
        let fields = [
            {
                fieldname: "question",
                fieldtype: "Data",
                label: "Question",
                in_list_view: 1,
                read_only: 1
            },
            {
                fieldname: "answer",
                fieldtype: "Data",
                label: "Answer",
                in_list_view: 1,
                read_only: 1
            }
        ]

        let dialog = new frappe.ui.Dialog({
            title: "Select Question",
            fields: [
                {
                    fieldname: "concept",
                    fieldtype: "Link",
                    options: "Concepts",
                    label: "Concept",
                    default: frm.doc.concept,

                    change: function() {
                        let concept = dialog.get_value("concept")
                        if (!concept){
                            return
                        }

                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Question and Answer",
                                fields: ["question", "answer"],
                                filters: { concept: concept }
                            },
                            callback: function(r) {

                                table_data = r.message || []
                                table_data.forEach(row => row.select = 0)

                                dialog.fields_dict.question.df.data = table_data
                                dialog.fields_dict.question.grid.refresh()
                            }
                        })
                    }
                },
                {
                    fieldname: "question",
                    fieldtype: "Table",
                    label: "Question",
                    cannot_add_rows: true,
                    data: table_data,
                    get_data: () => table_data,
                    fields: fields
                }
            ],

            primary_action_label: "Add",
            primary_action() {
                let selected = dialog.fields_dict.question.grid.get_selected_children()
                if (!selected.length) {
                    frappe.msgprint("Please select atleast one question")
                    return
                }
            selected.forEach(q => {
                let already_exists = frm.doc.question_and_answer.some(row =>
                    row.question === q.question,
                )

                if (!already_exists) {
                    let row = frm.add_child("question_and_answer")

                    row.question = q.question,
                    row.answer = q.answer,
                    row.concept = dialog.get_value("concept")
                }
                else{
                    frappe.msgprint("This Question was already added.")
                }

            })

                frm.refresh_field("question_and_answer")
                dialog.hide()
            }
        })
        dialog.show()
    }

});