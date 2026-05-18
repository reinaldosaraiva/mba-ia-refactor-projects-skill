'use strict';

const { dbRun } = require('./db');

async function create({ enrollment_id, amount, status }) {
  const { lastID } = await dbRun(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollment_id, amount, status],
  );
  return lastID;
}

module.exports = { create };
