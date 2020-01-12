# -*- coding: utf-8 -*-
"""
    indico_payment_stripe.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers used by the plugin.

"""
from __future__ import unicode_literals

from flask import flash, redirect, request, Markup
from flask_pluginengine import current_plugin
from stripe import error as err
from werkzeug.exceptions import BadRequest

from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration.models.registrations import Registration
from indico.web.flask.util import url_for
from indico.web.rh import RH

from .utils import _, conv_to_stripe_amount, conv_from_stripe_amount


__all__ = ['RHStripeSuccess', 'RHStripeCancel']


class RHStripeSuccess(RH):
    """ Validate transaction and mark as paid """

    CSRF_ENABLED = False

    def _process_args(self):
        self.token = request.args['token']
        self.registration = Registration.find_first(uuid=self.token)
        if not self.registration:
            raise BadRequest

    def _process(self):
        # We assume success was called because the transaction worked
        # TODO: Validate with stripe somehow.
        paid = request.form['paid']
        stripe_amount = request.form['amount']
        stripe_currency = request.form['currency']

        register_transaction(
            registration=self.registration,
            amount=conv_from_stripe_amount(
                stripe_amount,
                stripe_currency
            ),
            currency=stripe_currency,
            action=TransactionAction.complete,
            provider='stripe',
            data=request.form,
        )
        flash_msg = Markup(_(
            'Your payment request has been processed.'
        ))
        flash_type = 'success'

        reg_url = url_for(
            'event_registration.display_regform',
            self.registration.locator.registrant
        )
        flash(flash_msg, flash_type)
        return redirect(reg_url)



class RHStripeCancel(RH):
    """ The transaction was cancelled """

    def _process_args(self):
        self.token = request.args['token']
        self.registration = Registration.find_first(uuid=self.token)
        if not self.registration:
            raise BadRequest


    def _process(self):
        stripe_amount = request.form['amount']
        stripe_currency = request.form['currency']
        register_transaction(
            registration=self.registration,
            amount=conv_from_stripe_amount(
                stripe_amount,
                stripe_currency
            ),
            currency=stripe_currency,
            action=TransactionAction.reject,
            provider='stripe',
            data=request.form,
        )

        flash_msg = Markup(_(
            'Your transaction was cancelled, please retry'
        ))
        flash_type = 'error'

        reg_url = url_for(
            'event_registration.display_regform',
            self.registration.locator.registrant
        )
        flash(flash_msg, flash_type)
        return redirect(reg_url)
