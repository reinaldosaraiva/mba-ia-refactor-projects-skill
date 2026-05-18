'use strict';

const required = (name) => {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
};

module.exports = {
  DB_PASS: required('DB_PASS'),
  PAYMENT_GATEWAY_KEY: required('PAYMENT_GATEWAY_KEY'),
  SMTP_USER: process.env.SMTP_USER || 'no-reply@example.com',
  PORT: parseInt(process.env.PORT || '3000', 10),
  HOST: process.env.HOST || '0.0.0.0',
};
