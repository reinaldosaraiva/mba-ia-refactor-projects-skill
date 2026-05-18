'use strict';

const user_model = require('../models/user_model');
const { NotFoundError } = require('../errors');

async function remove(id) {
  const user = await user_model.findById(id);
  if (!user) throw new NotFoundError(`Usuário ${id} não encontrado`);
  await user_model.remove(id);
  /*
   * RESIDUAL: enrollments/payments/audit_logs for this user are NOT cleaned
   * up (v1 catalog has no slug for missing-ORM-cascade). v1.1 should add
   * `missing-orm-cascade-or-manual-fk-cleanup` whose recipe wraps the delete
   * in a transaction that removes dependent rows or enables FK cascades.
   */
  return { message: 'Usuário deletado' };
}

module.exports = { remove };
