'use strict';

const report_model = require('../models/report_model');

async function financialReport() {
  const rows = await report_model.financialRowset();
  const byCourse = new Map();
  const order = [];
  for (const r of rows) {
    if (!byCourse.has(r.course_id)) {
      byCourse.set(r.course_id, { course: r.course_title, revenue: 0, students: [] });
      order.push(r.course_id);
    }
    const bucket = byCourse.get(r.course_id);
    if (r.student_name !== null && r.student_name !== undefined) {
      if (r.payment_status === 'PAID') bucket.revenue += r.payment_amount || 0;
      bucket.students.push({
        student: r.student_name,
        paid: r.payment_amount || 0,
      });
    }
  }
  return order.map((id) => byCourse.get(id));
}

module.exports = { financialReport };
