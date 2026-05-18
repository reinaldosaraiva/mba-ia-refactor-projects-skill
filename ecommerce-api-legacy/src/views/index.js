'use strict';

const checkout_routes = require('./checkout_routes');
const admin_routes = require('./admin_routes');
const user_routes = require('./user_routes');

function register(app) {
  app.use(checkout_routes);
  app.use(admin_routes);
  app.use(user_routes);
}

module.exports = { register };
