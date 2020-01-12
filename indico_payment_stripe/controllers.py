# -*- coding: utf-8 -*-
"""
    indico_payment_stripe.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers used by the plugin.

"""
from __future__ import unicode_literals

import stripe
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

from pprint import pformat


__all__ = ['RHStripeSuccess', 'RHStripeCancel']

STRIPE_TRX_ACTION_MAP = {
    'succeeded': TransactionAction.complete,
    'failed': TransactionAction.reject,
    'pending': TransactionAction.pending
}


class RHStripeSuccess(RH):
    """ Validate transaction and mark as paid """

    CSRF_ENABLED = False

    def _process_args(self):
        self.token = request.args['token']
        self.session = request.args['session_id']
        self.registration = Registration.find_first(uuid=self.token)
        if not self.registration:
            raise BadRequest

    def _get_event_settings(self, settings_name):
        event_settings = current_plugin.event_settings
        return event_settings.get(
            self.registration.registration_form.event,
            settings_name
        )

    def _process(self):
        # We assume success was called because the transaction worked
        # TODO: Validate with stripe somehow.
        # Fetch the PaymentIntent

        use_event_api_keys = self._get_event_settings('use_event_api_keys')
        sec_key = (
            self._get_event_settings('sec_key')
            if use_event_api_keys else
            current_plugin.settings.get('sec_key')
        )
        reg_url = url_for(
            'event_registration.display_regform',
            self.registration.locator.registrant
        )

        try:
            stripe.api_key = sec_key
            session = stripe.checkout.Session.retrieve(self.session)

            payment_intent = stripe.PaymentIntent.retrieve(
                session['payment_intent']
            )

            status = payment_intent['status']


            stripe_amount = payment_intent['amount_received']
            stripe_currency = payment_intent['currency']
        except err.APIConnectionError as e:
            current_plugin.logger.exception(e)
            flash(
                _(
                    'There was a problem connecting to Stripe.'
                    ' Please try again.'
                ),
                'error'
            )

        if status == 'succeeded':
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

            flash(flash_msg, flash_type)
            return redirect(reg_url)

        else:
            flash(_('The payment was not completed. Please retry'))
            return redirect(url_for(
                'event_registration.display_regform', self.registration.locator.registrant
            ))





class RHStripeCancel(RH):
    """ The transaction was cancelled """

    def _process(self):
        flash(_('You cancelled the payment process.'), 'info')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))
