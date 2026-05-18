'use strict';

const { dbGet, dbAll } = require('./db');
const { COURSE_STATUS_ACTIVE } = require('../config/constants');

async function findActive(id) {
  return dbGet('SELECT * FROM courses WHERE id = ? AND active = ?', [id, COURSE_STATUS_ACTIVE]);
}

async function listAll() {
  return dbAll('SELECT * FROM courses');
}

module.exports = { findActive, listAll };
