frappe.pages['daily-assessment'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Daily Test',
		single_column: true
	});
	frappe.call({
		method : "frappe_learning.doctype.daily_test.timer"
		})

}