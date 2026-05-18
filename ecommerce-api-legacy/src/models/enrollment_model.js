'use strict';

const { dbRun } = require('./db');

async function create({ user_id, course_id }) {
  const { lastID } = await dbRun(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
    [user_id, course_id],
  );
  return lastID;
}

module.exports = { create };
