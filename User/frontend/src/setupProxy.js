/**
 * Proxy API requests to the backend in development.
 * /api/* -> http://localhost:5000/* (pathRewrite strips /api so backend sees /auth/register etc.)
 */
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      pathRewrite: (path) => {
        const rewritten = path.replace(/^\/api/, '') || '/';
        if (process.env.NODE_ENV !== 'production') {
          console.log(`[Proxy] ${path} -> ${rewritten}`);
        }
        return rewritten;
      },
      onError: (err, req, res) => {
        console.error('[Proxy] Error:', err.message);
      },
    })
  );
};
