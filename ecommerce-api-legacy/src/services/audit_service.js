'use strict';

const audit_model = require('../models/audit_model');

async function log(action) {
  await audit_model.insert(action);
}

module.exports = { log };
