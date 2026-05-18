'use strict';

const { Router } = require('express');
const user_controller = require('../controllers/user_controller');
const { success, asyncHandler } = require('./response');

const router = Router();

router.delete('/api/users/:id', asyncHandler(async (req, res) => {
  const result = await user_controller.remove(parseInt(req.params.id, 10));
  return success(res, result);
}));

module.exports = router;
