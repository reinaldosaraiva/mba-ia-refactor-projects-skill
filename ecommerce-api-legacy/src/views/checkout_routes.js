'use strict';

const { Router } = require('express');
const checkout_controller = require('../controllers/checkout_controller');
const { success, asyncHandler } = require('./response');

const router = Router();

router.post('/api/checkout', asyncHandler(async (req, res) => {
  const result = await checkout_controller.process(req.body);
  return success(res, result, 'Checkout realizado');
}));

module.exports = router;
