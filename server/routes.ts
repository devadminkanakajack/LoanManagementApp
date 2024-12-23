import express, { type Express, type Request, Response, NextFunction } from "express";
import { createServer } from "http";
import { hash, compare } from "bcrypt";
import session from "express-session";
import { db } from "../db";
import { users, loans, borrowers, analytics, payments } from "@db/schema";
import { eq, sql, and, gte, lte } from "drizzle-orm";
import MemoryStore from "memorystore";
import path from "path";
import { fileURLToPath } from "url";
import Decimal from "decimal.js"; // Ensure Decimal is imported

const SessionStore = MemoryStore(session);

declare module "express-session" {
  interface SessionData {
    user: { id: number };
  }
}

// Authentication middleware
const requireAuth = (req: Request, res: Response, next: NextFunction) => {
  if (!req.session.user) {
    return res.status(401).json({ message: "Unauthorized" });
  }
  next();
};

// Role-based authorization middleware
const requireRole = (roles: string[]) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (!req.session.user) {
      return res.status(401).json({ message: "Unauthorized" });
    }

    const user = await db.query.users.findFirst({
      where: eq(users.id, req.session.user.id)
    });

    if (!user || !roles.includes(user.role)) {
      return res.status(403).json({ message: "Forbidden" });
    }

    next();
  };
};

export function registerRoutes(app: Express) {
  // Session setup
  app.use(
    session({
      store: new SessionStore({
        checkPeriod: 86400000 // prune expired entries every 24h
      }),
      secret: process.env.SESSION_SECRET || "your-secret-key",
      resave: false,
      saveUninitialized: false,
      cookie: {
        secure: process.env.NODE_ENV === "production",
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
      }
    })
  );

  // Authentication routes
  app.post("/api/auth/login", async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ message: "Missing required fields" });
    }

    try {
      const user = await db.query.users.findFirst({
        where: eq(users.username, username)
      });

      if (!user) {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      const validPassword = await compare(password, user.password);
      if (!validPassword) {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      req.session.user = { id: user.id }; // Ensure session user is initialized
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

  // Registration route
  app.post("/api/auth/register", async (req, res) => {
    const { username, password, email, fullName, phoneNumber, address, employmentStatus, monthlyIncome } = req.body;

    try {
      // Check if username or email already exists
      const existingUser = await db.query.users.findFirst({
        where: eq(users.username, username)
      });

      if (existingUser) {
        return res.status(400).json({ message: "Username already exists" });
      }

      const existingEmail = await db.query.users.findFirst({
        where: eq(users.email, email)
      });

      if (existingEmail) {
        return res.status(400).json({ message: "Email already registered" });
      }

      // Hash password
      const hashedPassword = await hash(password, 10);

      // Create user with borrower role
      const [newUser] = await db.insert(users).values({
        username,
        password: hashedPassword,
        email,
        fullName,
        role: 'borrower',
      }).returning();

      // Create borrower record with the new user's ID
      await db.insert(borrowers).values({
        userId: newUser.id, // Ensure this is correctly referencing the new user's ID
        phoneNumber,
        address,
        employmentStatus,
        monthlyIncome: new Decimal(monthlyIncome).toString(), // Convert Decimal to string
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
      let query = db.query.loans;
      
      if (status) {
        query = query.where(eq(loans.status, status as string));
      }
      
      if (startDate && endDate) {
        query = query.where(and(
          gte(loans.createdAt, new Date(startDate as string)),
          lte(loans.createdAt, new Date(endDate as string))
        ));
      }

      const allLoans = await query.findMany({
        with: {
          borrower: true,
          payments: true
        }
      });

      res.json(allLoans);
    } catch (error) {
      console.error('Error fetching loans:', error);
      res.status(500).json({ message: "Failed to fetch loans" });
    }
  });

  // Create loan endpoint with validation
  app.post("/api/loans", requireAuth, requireRole(['admin', 'loan_officer']), async (req, res) => {
    try {
      const { amount, interestRate, term, borrowerId } = req.body;

      if (!amount || !interestRate || !term || !borrowerId) {
        return res.status(400).json({ message: "Missing required fields" });
      }

      const newLoan = await db.insert(loans).values({
        amount: new Decimal(amount).toString(),
        interestRate: new Decimal(interestRate).toString(),
        term,
        borrowerId,
        status: 'pending',
        createdAt: new Date(),
        updatedAt: new Date()
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
        .set({ status, updatedAt: new Date() })
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

  const httpServer = createServer(app);
  return httpServer;
}