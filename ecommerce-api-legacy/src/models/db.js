'use strict';

const sqlite3 = require('sqlite3'); // .verbose() removed (deprecated-style chain)

/**
 * RESIDUAL: kept as `:memory:` per the original (v1 catalog has no
 * `in-memory-db-in-prod` slug). Encapsulated here so v1.1 can swap to a
 * file-backed path or a real engine in one place.
 */
const db = new sqlite3.Database(':memory:');

function dbRun(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function callback(err) {
      if (err) return reject(err);
      resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

function dbGet(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });
}

function dbAll(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });
}

function dbExec(sql) {
  return new Promise((resolve, reject) => {
    db.exec(sql, (err) => (err ? reject(err) : resolve()));
  });
}

async function init() {
  await dbExec(`
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
    CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
  `);
  // Seed only when the DB is empty (idempotent for restarts on a file-backed DB).
  const existing = await dbGet('SELECT COUNT(*) AS n FROM users');
  if (existing.n === 0) {
    await dbRun("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
      ['Leonan', 'leonan@fullcycle.com.br', '123']);
    await dbRun("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)",
      ['Clean Architecture', 997.00, 1]);
    await dbRun("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)",
      ['Docker', 497.00, 1]);
    await dbRun("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [1, 1]);
    await dbRun("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
      [1, 997.00, 'PAID']);
  }
}

module.exports = { db, dbRun, dbGet, dbAll, dbExec, init };
