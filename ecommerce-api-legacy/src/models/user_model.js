'use strict';

const { dbGet, dbRun } = require('./db');

async function findByEmail(email) {
  return dbGet('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function findById(id) {
  return dbGet('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create({ name, email, passHash }) {
  const { lastID } = await dbRun(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, passHash],
  );
  return lastID;
}

async function remove(id) {
  const { changes } = await dbRun('DELETE FROM users WHERE id = ?', [id]);
  return changes;
}

module.exports = { findByEmail, findById, create, remove };
