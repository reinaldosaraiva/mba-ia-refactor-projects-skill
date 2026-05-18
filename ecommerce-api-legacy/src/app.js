'use strict';

const express = require('express');
const settings = require('./config/settings');
const db = require('./models/db');
const views = require('./views');
const errorHandler = require('./middlewares/error_handler');

async function buildApp() {
  await db.init();
  const app = express();
  app.use(express.json());
  views.register(app);
  app.use(errorHandler); // 4-arg signature — must be registered last
  return app;
}

if (require.main === module) {
  buildApp().then((app) => {
    app.listen(settings.PORT, settings.HOST, () => {
      console.log(`API rodando em http://${settings.HOST}:${settings.PORT}`);
    });
  }).catch((err) => {
    console.error('Boot failed:', err);
    process.exit(1);
  });
}

module.exports = { buildApp };
