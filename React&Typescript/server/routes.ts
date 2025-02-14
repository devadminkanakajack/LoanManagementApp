import express, { type Express, type Request, Response, NextFunction } from "express";
import { createServer } from "http";
import { hash, compare } from "bcrypt";
import session from "express-session";
import { db } from "../React&Typescript/db";
import { users, loans, borrowers, analytics, payments } from "@db/schema";
import { eq, sql, and, gte, lte, like, or } from "drizzle-orm";
import MemoryStore from "memorystore";
import path from "path";
import { fileURLToPath } from "url";
import Decimal from "decimal.js"; // Ensure Decimal is imported
import rateLimit from 'express-rate-limit';
import { z } from 'zod';

// Custom error classes
class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

const SessionStore = MemoryStore(session);

declare module "express-session" {
  interface SessionData {
    user: { 
      id: number;
      role: string;
      lastAccess?: string;
    };
  }
}

// Authentication middleware
const requireAuth = (req: Request, res: Response, next: NextFunction) => {
  if (!req.session.user) {
    return res.status(401).json({ message: "Unauthorized" });
  }
  next();
};

// Add a more comprehensive role check middleware
const requireRole = (roles: string[]) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (!req.session.user) {
      return res.status(401).json({ message: "Unauthorized" });
    }

    const user = await db.query.users.findFirst({
      where: eq(users.id, req.session.user.id),
      columns: {
        role: true,
        status: true
      }
    });

    if (!user || !roles.includes(user.role) || user.status !== 'active') {
      return res.status(403).json({ message: "Forbidden" });
    }

    next();
  };
};

const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(6)
});

const validateRequest = (schema: z.ZodSchema) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      await schema.parseAsync(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ message: "Validation error", errors: error.errors });
      } else {
        res.status(400).json({ message: "Validation error" });
      }
    }
  };
};

// Add a response wrapper utility
const createResponse = (data: any, message?: string) => ({
  success: true,
  data,
  message
});

// Enhanced input validation schemas
const userSchema = z.object({
  username: z.string().min(3).max(50),
  password: z.string().min(8).regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/),
  email: z.string().email(),
  fullName: z.string().min(2),
  role: z.enum(['admin', 'loan_officer', 'borrower'])
});

const loanSchema = z.object({
  amount: z.string().regex(/^\d+(\.\d{1,2})?$/),
  interestRate: z.string().regex(/^\d+(\.\d{1,2})?$/),
  term: z.number().positive(),
  borrowerId: z.number().positive(),
  purpose: z.string().min(5)
});

export function registerRoutes(app: Express) {
  // Session setup
  app.use(
    session({
      store: new SessionStore({
        checkPeriod: 86400000 // prune expired entries every 24h
      }),
      secret: process.env.SESSION_SECRET || "your-secret-key",
      name: 'sessionId', // Change cookie name from default 'connect.sid'
      resave: false,
      saveUninitialized: false,
      cookie: {
        secure: process.env.NODE_ENV === "production",
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000, // 24 hours
        sameSite: 'strict'
      }
    })
  );

  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
  });

  app.use('/api/', limiter);

  // Enhanced rate limiting configuration
  const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 5,
    message: { message: "Too many login attempts, please try again later" },
    standardHeaders: true,
    legacyHeaders: false
  });

  const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    message: { message: "Too many requests, please try again later" },
    standardHeaders: true,
    legacyHeaders: false
  });

  // Enhanced session configuration
  app.use(
    session({
      store: new SessionStore({
        checkPeriod: 86400000,
        stale: false
      }),
      secret: process.env.SESSION_SECRET || "your-secret-key",
      name: 'sessionId',
      resave: false,
      saveUninitialized: false,
      cookie: {
        secure: process.env.NODE_ENV === "production",
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000,
        sameSite: 'strict',
        path: '/',
        domain: process.env.NODE_ENV === 'production' ? process.env.DOMAIN : undefined
      }
    })
  );

  // Apply rate limiters
  app.use('/api/auth/login', authLimiter);
  app.use('/api/', apiLimiter);

  // Enhanced password hashing configuration
  const hashPassword = (password: string) => hash(password, 12);

  // Auth routes using Express Router
  const authRoutes = express.Router();
  app.use('/api/auth', authRoutes);

  // Loan routes with role-based access
  const loanRoutes = express.Router();
  loanRoutes.use(requireAuth);
  loanRoutes.get('/', requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const allLoans = await db.query.loans.findMany({
        with: {
          borrower: true,
          payments: true
        }
      });
      res.json(createResponse(allLoans, 'Loans retrieved successfully'));
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch loans" });
    }
  });
  loanRoutes.post('/', requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { amount, interestRate, term, borrowerId, purpose } = req.body;

      if (!amount || !interestRate || !term || !borrowerId || !purpose) {
        return res.status(400).json({ message: "Missing required fields" });
      }

      const newLoan = await db.insert(loans).values({
        amount: new Decimal(amount).toString(),
        interestRate: new Decimal(interestRate).toString(),
        term,
        borrowerId,
        purpose,
        status: 'pending',
        createdAt: new Date()
      }).returning();

      res.status(201).json(newLoan[0]);
    } catch (error) {
      console.error('Error creating loan:', error);
      res.status(500).json({ message: "Failed to create loan" });
    }
  });
  loanRoutes.patch('/:id/status', requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { id } = req.params;
      const { status } = req.body;

      if (!['pending', 'approved', 'rejected', 'active', 'paid', 'defaulted'].includes(status)) {
        return res.status(400).json({ message: "Invalid status" });
      }

      const updatedLoan = await db.update(loans)
        .set({ status })
        .where(eq(loans.id, parseInt(id)))
        .returning();

      if (!updatedLoan.length) {
        return res.status(404).json({ message: "Loan not found" });
      }

      res.json(updatedLoan[0]);
    } catch (error) {
      console.error('Error updating loan status:', error);
      res.status(500).json({ message: "Failed to update loan status" });
    }
  });
  app.use('/api/loans', loanRoutes);

  // Enhanced authentication route with validation
  app.post("/api/auth/login", validateRequest(loginSchema), async (req, res) => {
    const { username, password } = req.body;

    try {
      const user = await db.query.users.findFirst({
        where: eq(users.username, username)
      });

      if (!user || user.status !== 'active') {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      const validPassword = await compare(password, user.password);
      if (!validPassword) {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      req.session.user = { 
        id: user.id,
        role: user.role,
        lastAccess: new Date().toISOString()
      };

      // Update last login timestamp
      await db.update(users)
        .set({ lastLoginAt: new Date() })
        .where(eq(users.id, user.id));

      res.json({
        id: user.id,
        username: user.username,
        role: user.role,
        permissions: user.permissions
      });
    } catch (error) {
      console.error("Login error:", error);
      res.status(500).json({ message: "Internal server error" });
    }
  });

  app.post("/api/auth/logout", (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        return res.status(500).json({ message: "Logout failed" });
      }
      res.json({ message: "Logged out successfully" });
    });
  });

  // Enhanced registration with stronger validation
  app.post("/api/auth/register", validateRequest(userSchema), async (req, res) => {
    const { username, password, email, fullName, phoneNumber, address, employmentStatus, monthlyIncome } = req.body;

    try {
      const hashedPassword = await hashPassword(password);

      // Transaction to ensure atomicity
      const newUser = await db.transaction(async (tx) => {
        const [user] = await tx.insert(users).values({
          username,
          password: hashedPassword,
          email,
          fullName,
          role: 'borrower',
          status: 'active'
        }).returning();

        await tx.insert(borrowers).values({
          phoneNumber,
          address,
          employmentStatus,
          monthlyIncome: new Decimal(monthlyIncome).toString()
        });

        return user;
      });

      res.status(201).json({ 
        message: "Registration successful",
        user: {
          id: newUser.id,
          username: newUser.username,
          role: newUser.role,
          email: newUser.email,
          fullName: newUser.fullName
        }
      });
    } catch (error) {
      console.error("Registration error:", error);
      res.status(500).json({ message: "Failed to register user" });
    }
  });

  // User routes
  app.get("/api/users", async (req, res) => {
    try {
      const allUsers = await db.query.users.findMany();
      res.json(allUsers.map(user => ({
        id: user.id,
        username: user.username,
        role: user.role,
        email: user.email,
        fullName: user.fullName
      })));
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch users" });
    }
  });

  // Enhanced loan routes
  app.get("/api/loans", requireAuth, async (req, res) => {
    try {
      const { status, startDate, endDate } = req.query;
      let whereConditions = undefined;
      
      if (status && ['active', 'pending', 'approved', 'rejected', 'completed', 'defaulted'].includes(status as string)) {
        whereConditions = eq(loans.status, status as any);
      }
      
      if (startDate && endDate) {
        const dateCondition = and(
          gte(loans.createdAt, new Date(startDate as string)),
          lte(loans.createdAt, new Date(endDate as string))
        );
        whereConditions = whereConditions ? and(whereConditions, dateCondition) : dateCondition;
      }

      const allLoans = await db.query.loans.findMany({
        where: whereConditions,
        with: {
          borrower: true,
          payments: true
        }
      });

      res.json(createResponse(allLoans, 'Loans retrieved successfully'));
    } catch (error) {
      console.error('Error fetching loans:', error);
      res.status(500).json({ message: "Failed to fetch loans" });
    }
  });

  // Create loan endpoint with validation
  app.post("/api/loans", requireAuth, requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { amount, interestRate, term, borrowerId, purpose } = req.body;

      if (!amount || !interestRate || !term || !borrowerId || !purpose) {
        return res.status(400).json({ message: "Missing required fields" });
      }

      const newLoan = await db.insert(loans).values({
        amount: new Decimal(amount).toString(),
        interestRate: new Decimal(interestRate).toString(),
        term,
        borrowerId,
        purpose,
        status: 'pending',
        createdAt: new Date()
      }).returning();

      res.status(201).json(newLoan[0]);
    } catch (error) {
      console.error('Error creating loan:', error);
      res.status(500).json({ message: "Failed to create loan" });
    }
  });

  // Update loan status
  app.patch("/api/loans/:id/status", requireAuth, requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { id } = req.params;
      const { status } = req.body;

      if (!['pending', 'approved', 'rejected', 'active', 'paid', 'defaulted'].includes(status)) {
        return res.status(400).json({ message: "Invalid status" });
      }

      const updatedLoan = await db.update(loans)
        .set({ status })
        .where(eq(loans.id, parseInt(id)))
        .returning();

      if (!updatedLoan.length) {
        return res.status(404).json({ message: "Loan not found" });
      }

      res.json(updatedLoan[0]);
    } catch (error) {
      console.error('Error updating loan status:', error);
      res.status(500).json({ message: "Failed to update loan status" });
    }
  });

  // Record loan payment
  app.post("/api/loans/:id/payments", requireAuth, async (req, res) => {
    try {
      const { id } = req.params;
      const { amount, paymentDate } = req.body;

      if (!amount || !paymentDate) {
        return res.status(400).json({ message: "Missing required fields" });
      }

      const payment = await db.insert(payments).values({
        loanId: parseInt(id),
        amount: new Decimal(amount).toString(),
        paymentDate: new Date(paymentDate),
        status: 'pending',
        createdAt: new Date()
      }).returning();

      res.status(201).json(payment[0]);
    } catch (error) {
      console.error('Error recording payment:', error);
      res.status(500).json({ message: "Failed to record payment" });
    }
  });

  // Enhanced borrower routes
  app.get("/api/borrowers", requireAuth, requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { search } = req.query;
      let query = db.query.borrowers;
      
      if (search) {
        // Add search functionality if needed
      }

      const allBorrowers = await query.findMany({
        with: {
          loans: true,
          user: {
            columns: {
              password: false // Exclude sensitive data
            }
          }
        }
      });

      res.json(allBorrowers);
    } catch (error) {
      console.error('Error fetching borrowers:', error);
      res.status(500).json({ message: "Failed to fetch borrowers" });
    }
  });

  // Dashboard stats endpoint
  app.get("/api/dashboard/stats", async (req, res) => {
    try {
      const [
        totalLoans,
        totalBorrowers,
        defaultedLoans,
        monthlyLoans
      ] = await Promise.all([
        db.select({ count: sql<number>`count(*)` }).from(loans).then(result => result[0].count),
        db.select({ count: sql<number>`count(*)` }).from(borrowers).then(result => result[0].count),
        db.select({ count: sql<number>`count(*)` }).from(loans)
          .where(eq(loans.status, 'defaulted'))
          .then(result => result[0].count),
        db.query.analytics.findMany({
          where: eq(analytics.metricType, 'loan_volume'),
          orderBy: (analytics, { desc }) => [desc(analytics.createdAt)],
          limit: 12
        })
      ]);

      const totalAmount = await db.select({
        sum: sql<string>`sum(${loans.amount}::numeric)::text`
      }).from(loans);

      res.json({
        totalLoans,
        totalBorrowers,
        totalAmount: parseFloat(totalAmount[0]?.sum || '0'),
        defaultedLoans,
        monthlyLoans: monthlyLoans.map(loan => ({
          month: loan.createdAt ? new Date(loan.createdAt).toLocaleString('default', { month: 'short' }) : 'Unknown',
          amount: parseFloat(loan.metricValue.toString())
        }))
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      res.status(500).json({ message: "Failed to fetch dashboard stats" });
    }
  });

  // Error handling middleware
  app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    console.error(err.stack);
    res.status(500).json({ message: "Something broke!" });
  });

  // Add a centralized error handler
  const errorHandler = (err: Error, req: Request, res: Response, next: NextFunction) => {
    console.error(err.stack);
    
    // Remove sensitive information from error responses
    const sanitizedError = {
      message: process.env.NODE_ENV === 'production' 
        ? 'Internal server error' 
        : err.message,
      code: err instanceof ValidationError ? 400 
        : err instanceof AuthenticationError ? 401 
        : 500
    };
    
    res.status(sanitizedError.code).json({ message: sanitizedError.message });
  };
  
  app.use(errorHandler);

  // Serve static files from the React app
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  app.use(express.static(path.join(__dirname, '../dist/public')));

  // Handle React routing, return all requests to React app
  app.get('*', (req, res) => {
    if (req.url.startsWith('/api')) {
      res.status(404).json({ message: 'API endpoint not found' });
    } else {
      res.sendFile(path.join(__dirname, '../dist/index.html'));
    }
  });

  // API Routes
  app.use('/api/v1', apiLimiter);

  // API Endpoints
  app.get('/api/v1/status', (req, res) => {
    res.json({ status: 'healthy', version: '1.0.0' });
  });

  // Loan API endpoints
  loanRoutes.get('/api/v1/loans', requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { status, startDate, endDate, page = 1, limit = 10 } = req.query;
      const offset = (Number(page) - 1) * Number(limit);

      let whereConditions = undefined;
      if (status && ['active', 'pending', 'approved', 'rejected', 'completed', 'defaulted'].includes(status as string)) {
        whereConditions = eq(loans.status, status as 'active' | 'pending' | 'approved' | 'rejected' | 'completed' | 'defaulted');
      }
      if (startDate && endDate) {
        const dateCondition = and(
          gte(loans.createdAt, new Date(startDate as string)),
          lte(loans.createdAt, new Date(endDate as string))
        );
        whereConditions = whereConditions ? and(whereConditions, dateCondition) : dateCondition;
      }

      const loanResults = await db.query.loans.findMany({
        where: whereConditions,
        with: { borrower: true, payments: true },
        limit: Number(limit),
        offset
      });

      const [{ count }] = await db.select({ count: sql<number>`count(*)` }).from(loans);
      const total = Number(count);

      res.json({
        data: loans,
        pagination: {
          page: Number(page),
          limit: Number(limit),
          total,
          pages: Math.ceil(total / Number(limit))
        }
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch loans' });
    }
  });

  // Borrower API endpoints
  app.get('/api/v1/borrowers', requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { page = 1, limit = 10, search } = req.query;
      const offset = (Number(page) - 1) * Number(limit);

      const borrowerResults = await db.query.borrowers.findMany({
        where: search ? 
          or(
            like(users.fullName, `%${search as string}%`),
            like(users.email, `%${search as string}%`)
          )
        : undefined,
        with: {
          user: true
        },
        limit: Number(limit),
        offset
      });

      const [{ count }] = await db.select({ count: sql<number>`count(*)` }).from(borrowers);
      const total = Number(count);

      res.json({
        data: borrowers,
        pagination: {
          page: Number(page),
          limit: Number(limit),
          total,
          pages: Math.ceil(total / Number(limit))
        }
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch borrowers' });
    }
  });

  // Analytics API endpoints
  app.get('/api/v1/analytics/dashboard', requireRole(['admin']), async (req, res) => {
    try {
      const stats = await getDashboardStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch analytics' });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
async function getDashboardStats() {
  const today = new Date();
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  const [
    totalActiveLoans,
    totalBorrowers,
    monthlyStats,
    loansByStatus,
    totalAmount
  ] = await Promise.all([
    db.select({ count: sql<number>`count(*)` })
      .from(loans)
      .where(eq(loans.status, 'active'))
      .then(result => result[0].count),
    
    db.select({ count: sql<number>`count(*)` })
      .from(borrowers)
      .then(result => result[0].count),
    
    db.select({
      totalLoans: sql<number>`count(*)`,
      totalAmount: sql<string>`sum(${loans.amount}::numeric)::text`
    })
    .from(loans)
    .where(and(
      gte(loans.createdAt, firstDayOfMonth),
      lte(loans.createdAt, lastDayOfMonth)
    )),

    db.select({
      status: loans.status,
      count: sql<number>`count(*)`
    })
    .from(loans)
    .groupBy(loans.status),

    db.select({
      sum: sql<string>`sum(${loans.amount}::numeric)::text`
    })
    .from(loans)
  ]);

  return {
    totalActiveLoans,
    totalBorrowers,
    monthlyStats: {
      loans: monthlyStats[0]?.totalLoans || 0,
      amount: parseFloat(monthlyStats[0]?.totalAmount || '0')
    },
    loansByStatus: Object.fromEntries(
      loansByStatus.map(item => [item.status, item.count])
    ),
    totalAmount: parseFloat(totalAmount[0]?.sum || '0'),
    lastUpdated: new Date().toISOString()
  };
}

