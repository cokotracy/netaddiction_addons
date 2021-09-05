# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import logging
import psycopg2
import smtplib
import threading
import re

from collections import defaultdict

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
	""" Model holding RFC2822 email messages to send. This model also provides
		facilities to queue and send new email messages.  """
	_inherit = 'mail.mail'
	_description = 'Outgoing Mails'
	_inherits = {'mail.message': 'mail_message_id'}
	_order = 'id desc'
	_rec_name = 'subject'

	def send(self, auto_commit=False, raise_exception=False):
		""" Sends the selected emails immediately, ignoring their current
			state (mails that have already been sent should not be passed
			unless they should actually be re-sent).
			Emails successfully delivered are marked as 'sent', and those
			that fail to be deliver are marked as 'exception', and the
			corresponding error mail is output in the server logs.

			:param bool auto_commit: whether to force a commit of the mail status
				after sending each mail (meant only for scheduler processing);
				should never be True during normal transactions (default: False)
			:param bool raise_exception: whether to raise an exception if the
				email sending process has failed
			:return: True
		"""
		for server_id, batch_ids in self._split_by_server():
			smtp_session = None
			try:
				smtp_session = self.env['ir.mail_server'].connect(mail_server_id=server_id)
			except Exception as exc:
				batch = self.browse(batch_ids)
				batch.write({'state': 'exception', 'failure_reason': exc})
				batch._postprocess_sent_message(success_pids=[], failure_type="SMTP")
			else:
				self.browse(batch_ids)._send(
					auto_commit=auto_commit,
					raise_exception=raise_exception,
					smtp_session=smtp_session)
				_logger.info(
					'Sent batch %s emails via mail server ID #%s',
					len(batch_ids), server_id)
			finally:
				if smtp_session:
					smtp_session.quit()