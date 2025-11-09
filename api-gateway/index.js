// ============================================
// API GATEWAY - Transport System
// ============================================
// Single Entry Point untuk semua microservices
// Port: 8080
// ============================================

require('dotenv').config();
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 8080;

// ============================================
// MIDDLEWARE CONFIGURATION
// ============================================

// Logging
app.use(morgan('combined'));

// CORS - Allow all origins (customize as needed)
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Body parser
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate Limiting - Prevent abuse
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.'
  }
});
app.use(limiter);

// ============================================
// SERVICE CONFIGURATION
// ============================================

const SERVICES = {
  USER: process.env.USER_SERVICE_URL || 'http://service-user:5001',
  ROUTE: process.env.ROUTE_SERVICE_URL || 'http://service-1-route:5002',
  STOP: process.env.STOP_SERVICE_URL || 'http://service-2-stop:5003',
  BUS: process.env.BUS_SERVICE_URL || 'http://service-3-bus:5004',
  SCHEDULE: process.env.SCHEDULE_SERVICE_URL || 'http://service-4-schedule:5005'
};

// ============================================
// AUTHENTICATION MIDDLEWARE
// ============================================

const authenticateAdmin = async (req, res, next) => {
  try {
    const token = req.headers.authorization;
    
    if (!token) {
      return res.status(401).json({
        error: 'No authorization token provided'
      });
    }

    // Verify token with User Service
    const response = await axios.get(`${SERVICES.USER}/verify-admin`, {
      headers: { Authorization: token }
    });

    if (response.data.valid) {
      req.user = response.data.user;
      next();
    } else {
      return res.status(403).json({
        error: 'Invalid or expired token'
      });
    }
  } catch (error) {
    console.error('Authentication error:', error.message);
    return res.status(403).json({
      error: 'Authentication failed',
      details: error.response?.data?.error || error.message
    });
  }
};

// ============================================
// PROXY CONFIGURATION
// ============================================

const proxyOptions = (target) => ({
  target,
  changeOrigin: true,
  onError: (err, req, res) => {
    console.error(`Proxy Error to ${target}:`, err.message);
    res.status(503).json({
      error: 'Service temporarily unavailable',
      service: target,
      details: err.message
    });
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`[PROXY] ${req.method} ${req.path} -> ${target}${req.path}`);
  }
});

// ============================================
// ROUTES - PUBLIC ENDPOINTS
// ============================================

// Health Check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'API Gateway',
    timestamp: new Date().toISOString(),
    services: SERVICES
  });
});

// Gateway Info
app.get('/', (req, res) => {
  res.json({
    message: 'Transport System API Gateway',
    version: '1.0.0',
    endpoints: {
      auth: '/api/auth/*',
      routes: '/api/routes/*',
      stops: '/api/stops/*',
      buses: '/api/buses/*',
      schedules: '/api/schedules/*'
    },
    documentation: '/api/docs'
  });
});

// API Documentation
app.get('/api/docs', (req, res) => {
  res.json({
    title: 'Transport System API',
    version: '1.0.0',
    baseUrl: `http://localhost:${PORT}`,
    services: [
      {
        name: 'Authentication',
        prefix: '/api/auth',
        endpoints: [
          { method: 'POST', path: '/api/auth/login', description: 'User login' },
          { method: 'POST', path: '/api/auth/register', description: 'User registration' }
        ]
      },
      {
        name: 'Routes',
        prefix: '/api/routes',
        endpoints: [
          { method: 'GET', path: '/api/routes', description: 'Get all routes' },
          { method: 'GET', path: '/api/routes/:id', description: 'Get route by ID' },
          { method: 'GET', path: '/api/routes/:id/stops', description: 'Get stops in route' },
          { method: 'GET', path: '/api/routes/:id/buses', description: 'Get buses on route' },
          { method: 'POST', path: '/api/routes/admin/add', description: 'Add route (Admin)', auth: true },
          { method: 'PUT', path: '/api/routes/admin/:id', description: 'Update route (Admin)', auth: true },
          { method: 'DELETE', path: '/api/routes/admin/:id', description: 'Delete route (Admin)', auth: true }
        ]
      },
      {
        name: 'Stops',
        prefix: '/api/stops',
        endpoints: [
          { method: 'GET', path: '/api/stops', description: 'Get all stops' },
          { method: 'GET', path: '/api/stops/:id', description: 'Get stop by ID' },
          { method: 'GET', path: '/api/stops/search', description: 'Search stops' },
          { method: 'POST', path: '/api/stops/admin/add', description: 'Add stop (Admin)', auth: true },
          { method: 'PUT', path: '/api/stops/admin/:id', description: 'Update stop (Admin)', auth: true },
          { method: 'DELETE', path: '/api/stops/admin/:id', description: 'Delete stop (Admin)', auth: true }
        ]
      },
      {
        name: 'Buses',
        prefix: '/api/buses',
        endpoints: [
          { method: 'GET', path: '/api/buses', description: 'Get all buses' },
          { method: 'GET', path: '/api/buses/:id', description: 'Get bus by ID' },
          { method: 'PUT', path: '/api/buses/:id/location', description: 'Update bus location' },
          { method: 'POST', path: '/api/buses', description: 'Register bus (Admin)', auth: true },
          { method: 'PUT', path: '/api/buses/:id/route', description: 'Assign bus to route (Admin)', auth: true },
          { method: 'PUT', path: '/api/buses/:id/speed', description: 'Update bus speed (Admin)', auth: true }
        ]
      },
      {
        name: 'Schedules & ETA',
        prefix: '/api/schedules',
        endpoints: [
          { method: 'GET', path: '/api/schedules/:routeId', description: 'Get route schedules' },
          { method: 'GET', path: '/api/schedules/eta', description: 'Calculate ETA (Real-time)' },
          { method: 'GET', path: '/api/schedules/stops/:id/arrivals', description: 'Get bus arrivals at stop' },
          { method: 'POST', path: '/api/schedules/admin/add', description: 'Add schedule (Admin)', auth: true }
        ]
      }
    ]
  });
});

// ============================================
// SERVICE PROXIES
// ============================================

// 1. USER SERVICE - Authentication
app.use('/api/auth/login', createProxyMiddleware({
  ...proxyOptions(SERVICES.USER),
  pathRewrite: { '^/api/auth/login': '/login' }
}));

app.use('/api/auth/register', createProxyMiddleware({
  ...proxyOptions(SERVICES.USER),
  pathRewrite: { '^/api/auth/register': '/register' }
}));

app.use('/api/auth/verify-admin', createProxyMiddleware({
  ...proxyOptions(SERVICES.USER),
  pathRewrite: { '^/api/auth/verify-admin': '/verify-admin' }
}));

// 2. ROUTE SERVICE
// Public routes
app.use('/api/routes/nearby', createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

app.use('/api/routes/:id/stops', createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

app.use('/api/routes/:id/buses', createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

app.use('/api/routes/:id', createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

app.use('/api/routes', createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

// Admin routes (with authentication)
app.use('/api/routes/admin', authenticateAdmin, createProxyMiddleware({
  ...proxyOptions(SERVICES.ROUTE),
  pathRewrite: { '^/api/routes': '/routes' }
}));

// 3. STOP SERVICE
// Public routes
app.use('/api/stops/search', createProxyMiddleware({
  ...proxyOptions(SERVICES.STOP),
  pathRewrite: { '^/api/stops': '/stops' }
}));

app.use('/api/stops/:id', createProxyMiddleware({
  ...proxyOptions(SERVICES.STOP),
  pathRewrite: { '^/api/stops': '/stops' }
}));

app.use('/api/stops', createProxyMiddleware({
  ...proxyOptions(SERVICES.STOP),
  pathRewrite: { '^/api/stops': '/stops' }
}));

// Admin routes
app.use('/api/stops/admin', authenticateAdmin, createProxyMiddleware({
  ...proxyOptions(SERVICES.STOP),
  pathRewrite: { '^/api/stops': '/stops' }
}));

// 4. BUS SERVICE
// Public routes
app.use('/api/buses/:id/location', createProxyMiddleware({
  ...proxyOptions(SERVICES.BUS),
  pathRewrite: { '^/api/buses': '/buses' }
}));

app.use('/api/buses/:id', createProxyMiddleware({
  ...proxyOptions(SERVICES.BUS),
  pathRewrite: { '^/api/buses': '/buses' }
}));

app.use('/api/buses', createProxyMiddleware({
  ...proxyOptions(SERVICES.BUS),
  pathRewrite: { '^/api/buses': '/buses' }
}));

// 5. SCHEDULE SERVICE
// Public routes
app.use('/api/schedules/eta', createProxyMiddleware({
  ...proxyOptions(SERVICES.SCHEDULE),
  pathRewrite: { '^/api/schedules': '' }
}));

app.use('/api/schedules/stops/:id/arrivals', createProxyMiddleware({
  ...proxyOptions(SERVICES.SCHEDULE),
  pathRewrite: { '^/api/schedules': '' }
}));

app.use('/api/schedules/:routeId/next-departures', createProxyMiddleware({
  ...proxyOptions(SERVICES.SCHEDULE),
  pathRewrite: { '^/api/schedules': '/schedules' }
}));

app.use('/api/schedules/:routeId', createProxyMiddleware({
  ...proxyOptions(SERVICES.SCHEDULE),
  pathRewrite: { '^/api/schedules': '/schedules' }
}));

// Admin routes
app.use('/api/schedules/admin', authenticateAdmin, createProxyMiddleware({
  ...proxyOptions(SERVICES.SCHEDULE),
  pathRewrite: { '^/api/schedules': '/schedules' }
}));

// ============================================
// ERROR HANDLING
// ============================================

// 404 Handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    path: req.path,
    method: req.method,
    suggestion: 'Check /api/docs for available endpoints'
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('Global Error:', err);
  res.status(err.status || 500).json({
    error: 'Internal server error',
    message: err.message,
    path: req.path
  });
});

// ============================================
// START SERVER
// ============================================

app.listen(PORT, () => {
  console.log('============================================');
  console.log('🚀 API Gateway Started');
  console.log('============================================');
  console.log(`Port: ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log('\n📡 Connected Services:');
  console.log(`  - User Service:     ${SERVICES.USER}`);
  console.log(`  - Route Service:    ${SERVICES.ROUTE}`);
  console.log(`  - Stop Service:     ${SERVICES.STOP}`);
  console.log(`  - Bus Service:      ${SERVICES.BUS}`);
  console.log(`  - Schedule Service: ${SERVICES.SCHEDULE}`);
  console.log('\n📚 Documentation: http://localhost:' + PORT + '/api/docs');
  console.log('❤️  Health Check:   http://localhost:' + PORT + '/health');
  console.log('============================================\n');
});