'use strict';

const { Router } = require('express');
const admin_controller = require('../controllers/admin_controller');
const { success, asyncHandler } = require('./response');

const router = Router();

router.get('/api/admin/financial-report', asyncHandler(async (req, res) => {
  const report = await admin_controller.financialReport();
  return success(res, report);
}));

module.exports = router;
