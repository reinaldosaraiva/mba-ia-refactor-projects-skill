'use strict';

const { PAYMENT_APPROVED_CARD_PREFIX, PAYMENT_STATUS } = require('../config/constants');

/**
 * Decide approval based on a configurable card prefix. The fake decision rule
 * is preserved (project 2's original behaviour) but the prefix is now a
 * constant rather than an inline literal. Card number is never logged here.
 */
function charge({ card }) {
  const status = card && card.startsWith(PAYMENT_APPROVED_CARD_PREFIX)
    ? PAYMENT_STATUS.PAID
    : PAYMENT_STATUS.DENIED;
  // NOTE: card number deliberately not logged (PII residual call-out).
  return { status };
}

module.exports = { charge };
