import frappe

from healthcare.healthcare.doctype.patient_encounter.patient_encounter import PatientEncounter

class HealthcarePatientEncounter(PatientEncounter):
	def make_service_request(self):
		if self.lab_test_prescription:
			for lab_test in self.lab_test_prescription:
				if lab_test.observation_template:
					template_doc = "Observation Template"
					template = "observation_template"
				elif lab_test.lab_test_code:
					template_doc = "Lab Test Template"
					template = "lab_test_code"
				else:
					continue
				if not lab_test.service_request:
					lab_template = frappe.get_doc(template_doc, lab_test.get(template))
					order = super().get_order_details(lab_template, lab_test)
					order.insert(ignore_permissions=True, ignore_mandatory=True)
					order.submit()
					lab_test.service_request = order.name

		if self.procedure_prescription:
			for procedure in self.procedure_prescription:
				if not procedure.service_request:
					procedure_template = frappe.get_doc("Clinical Procedure Template", procedure.procedure)
					order = super().get_order_details(procedure_template, procedure)
					order.insert(ignore_permissions=True, ignore_mandatory=True)
					order.submit()
					procedure.service_request = order.name

					clinical_procedure = self.make_clinical_procedure(procedure_template, procedure)
					procedure.clinical_procedure = clinical_procedure.name

		if self.therapies:
			for therapy in self.therapies:
				if not therapy.service_request:
					therapy_type = frappe.get_doc("Therapy Type", therapy.therapy_type)
					order = super().get_order_details(therapy_type, therapy)
					order.insert(ignore_permissions=True, ignore_mandatory=True)
					order.submit()
					therapy.service_request = order.name

	def make_clinical_procedure(self, procedure_template, procedure):
		service_unit = None
		medical_department = None
		
		if self.appointment:
			appointment = frappe.get_doc("Patient Appointment", self.appointment)
			service_unit = appointment.service_unit
			medical_department = appointment.department

		if not medical_department:
			practitioner = frappe.get_doc("Healthcare Practitioner", self.practitioner)
			medical_department = practitioner.department

		clinical_procedure = frappe.get_doc({
			"doctype": "Clinical Procedure",
			"procedure_template": procedure_template.name,
			"patient": self.patient,
			"appointment": self.appointment,
			"practitioner": self.practitioner,
			"medical_department": medical_department,
			"service_unit": service_unit,
			"service_request": procedure.service_request,
		})

		clinical_procedure.insert(ignore_permissions=True)
		return clinical_procedure