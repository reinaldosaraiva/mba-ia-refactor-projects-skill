'use strict';

const { dbAll } = require('./db');

/**
 * Single JOIN replacing the original 1+N+N×M nested-callback fan-out.
 * Returns one row per (course, enrollment) tuple; controller groups by course.
 */
async function financialRowset() {
  return dbAll(`
    SELECT
      c.id          AS course_id,
      c.title       AS course_title,
      u.name        AS student_name,
      p.amount      AS payment_amount,
      p.status      AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u       ON u.id = e.user_id
    LEFT JOIN payments p    ON p.enrollment_id = e.id
    ORDER BY c.id, e.id
  `);
}

module.exports = { financialRowset };
