'use strict';

class AppError extends Error {
  constructor(message, code = 'internal_error', http = 500) {
    super(message);
    this.code = code;
    this.http = http;
  }
}

class ValidationError extends AppError {
  constructor(message) { super(message, 'validation_error', 400); }
}

class NotFoundError extends AppError {
  constructor(message) { super(message, 'not_found', 404); }
}

class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 'payment_denied', 400); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeniedError };
