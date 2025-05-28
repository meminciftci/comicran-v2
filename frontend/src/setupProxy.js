// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',                     // any request starting with /api
    createProxyMiddleware({
      target: 'http://10.0.0.200:5006',  // your orchestrator HTTP server
      changeOrigin: true,
      secure: false,
      ws: true,
      onError: (err, req, res) => {
        console.error('Proxy Error:', err);
        res.status(500).send('Proxy Error');
      }
    })
  );
};
