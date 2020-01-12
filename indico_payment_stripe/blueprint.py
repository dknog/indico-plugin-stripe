# -*- coding: utf-8 -*-
"""
    indico_payment_stripe.blueprint
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The plugin blueprint.

"""
from __future__ import unicode_literals

from indico.core.plugins import IndicoPluginBlueprint

from indico_payment_stripe.controllers import RHStripeSuccess, RHStripeCancel


blueprint = IndicoPluginBlueprint(
    'payment_stripe',
    __name__,
    url_prefix=(
        '/event/<confId>/registrations/'
        '<int:reg_form_id>/payment/response/stripe'
    )
)

blueprint.add_url_rule('/cancel', 'cancel', RHStripeCancel, methods=('GET', 'POST')) # TODO: Check if we need both GET/POST
blueprint.add_url_rule('/success', 'success', RHStripeSuccess, methods=('GET', 'POST')) # TODO: Check if we need both GET/POST
