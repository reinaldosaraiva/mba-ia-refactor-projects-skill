'use strict';

const { AppError } = require('../errors');

// Express identifies error middleware by 4-argument signature — keep all four.
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
  if (err instanceof AppError) {
    return res.status(err.http).json({
      status: 'error',
      error: { code: err.code, message: err.message },
    });
  }
  console.error('Unhandled error:', err && err.stack ? err.stack : err);
  return res.status(500).json({
    status: 'error',
    error: { code: 'internal_error', message: 'Internal Server Error' },
  });
}

module.exports = errorHandler;
