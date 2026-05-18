'use strict';

function success(res, data, message, http = 200) {
  const payload = { status: 'ok' };
  if (data !== undefined) payload.data = data;
  if (message) payload.message = message;
  return res.status(http).json(payload);
}

function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

module.exports = { success, asyncHandler };
