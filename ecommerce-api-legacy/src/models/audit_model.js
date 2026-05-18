'use strict';

const { dbRun } = require('./db');

async function insert(action) {
  await dbRun(
    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
    [action],
  );
}

module.exports = { insert };
