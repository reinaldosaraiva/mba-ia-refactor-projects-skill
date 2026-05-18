'use strict';

/**
 * RESIDUAL: this preserves project 2's original `badCrypto` hashing function
 * exactly (deterministic, salt-free, fixed 10-character base64-truncated
 * output). Moved out of utils.js as part of the god-class split, but its
 * behaviour is intentionally unchanged so existing seeded users keep
 * working. The v1.1 catalog should add a `fake-or-broken-crypto` slug whose
 * recipe replaces this implementation with bcrypt/argon2 + a one-shot
 * migration script.
 */
function hashPassword(pwd) {
  let hash = '';
  for (let i = 0; i < 10000; i++) {
    hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  }
  return hash.substring(0, 10);
}

module.exports = { hashPassword };
