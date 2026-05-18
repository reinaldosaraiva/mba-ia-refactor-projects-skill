'use strict';

const user_model = require('../models/user_model');
const course_model = require('../models/course_model');
const enrollment_model = require('../models/enrollment_model');
const payment_model = require('../models/payment_model');
const payment_service = require('../services/payment_service');
const audit_service = require('../services/audit_service');
const legacy_crypto = require('../services/legacy_crypto');
const CacheService = require('../services/cache_service');
const { ValidationError, NotFoundError, PaymentDeniedError, AppError } = require('../errors');
const { PAYMENT_STATUS } = require('../config/constants');

const cache = new CacheService();

function validateBody(body) {
  const { usr, eml, pwd, c_id, card } = body || {};
  if (!usr || !eml || !c_id || !card) {
    throw new ValidationError('Campos obrigatórios: usr, eml, c_id, card');
  }
  if (!pwd) {
    throw new ValidationError('Senha (pwd) é obrigatória');
  }
  return { name: usr, email: eml, password: pwd, courseId: c_id, card };
}

async function process(body) {
  const { name, email, password, courseId, card } = validateBody(body);

  const course = await course_model.findActive(courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');

  let user = await user_model.findByEmail(email);
  if (!user) {
    const userId = await user_model.create({
      name,
      email,
      passHash: legacy_crypto.hashPassword(password),
    });
    user = { id: userId, name, email };
  }

  const { status } = payment_service.charge({ card });
  if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeniedError();

  const enrollmentId = await enrollment_model.create({
    user_id: user.id,
    course_id: courseId,
  });
  if (!enrollmentId) throw new AppError('Erro ao criar matrícula');

  await payment_model.create({
    enrollment_id: enrollmentId,
    amount: course.price,
    status,
  });

  await audit_service.log(`Checkout curso ${courseId} por ${user.id}`);
  cache.set(`last_checkout_${user.id}`, course.title);

  return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { process };
