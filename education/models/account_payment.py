
from odoo import api, models
from odoo.exceptions import UserError


class Payment(models.Model):
	_inherit = "account.payment"

	def post(self):
		#raise UserError('test')
		res = super(Payment, self).post()
		code = 'account.payment'
		ref = False
		name = False
		if(self.payment_type=='inbound'):
			ref = 'RC-'

		elif(self.payment_type=='outbound'):
			ref = 'RF-'

		company_sequence = False
		parent_sequence = False

		if(not self.company_id.document_sequence):
			company_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.id),('code','=',code),('prefix','=','RC')],limit=1)
			name = ref + self.company_id.code+'-'+str(company_sequence.number)
			company_sequence.write({'number': company_sequence.number + 1})

		else:
			parent_sequence = self.env['ir.sequence'].search([('company_id','=',self.company_id.parent_id.id),('code','=',code),('prefix','=','RC')],limit=1)
			if(parent_sequence):
				name = ref+self.company_id.parent_id.code+'-'+str(parent_sequence.number)
				parent_sequence.write({'number': parent_sequence.number + 1})

		self.write({'name': name})

		move_id = self.env['account.move.line'].search([('payment_id','=',self.id)],limit=1).move_id
		move_id.write({'name': name, 'company_id': self.company_id.id})

		return res

	@api.onchange('amount', 'currency_id')
	def _onchange_amount(self):
		journal = self.env['account.journal'].search([('company_id','=',self.company_id.id),('type','=','bank')],limit=1)
		if journal:
			self.journal_id = journal.id

	@api.onchange('payment_type')
	def _onchange_payment_type(self):
		if not self.invoice_ids and not self.partner_type:
			if self.payment_type == 'inbound':
				self.partner_type = 'customer'

			elif self.payment_type == 'outbound':
				self.partner_type = 'supplier'

		elif self.payment_type not in ('inbound', 'outbound'):
			self.partner_type = False

		res = self._onchange_journal()
		if not res.get('domain', {}):
			res['domain'] = {}

		jrnl_filters = self._compute_journal_domain_and_types()
		journal_types = jrnl_filters['journal_types']
		journal_types.update(['bank'])
		return res

		