import express, { type Express } from "express";
import { createServer } from "http";
import { hash, compare } from "bcrypt";
import session from "express-session";
import { db } from "../db";
import { users, loans, borrowers, payments } from "@db/schema";
import { eq, and, sql } from "drizzle-orm";
import MemoryStore from "memorystore";
import path from "path";
import { fileURLToPath } from "url";

const SessionStore = MemoryStore(session);

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

      req.session.userId = user.id;
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
    req.session.destroy(() => {
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

      // Create borrower record
      await db.insert(borrowers).values({
        userId: newUser.id,
        phoneNumber,
        address,
        employmentStatus,
        monthlyIncome: new Decimal(monthlyIncome),
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

  // Loan routes
  app.get("/api/loans", async (req, res) => {
    try {
      const allLoans = await db.query.loans.findMany({
        with: {
          borrower: true,
          payments: true
        }
      });
      res.json(allLoans);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch loans" });
    }
  });

  // Create new loan
  app.post("/api/loans", async (req, res) => {
    try {
      const newLoan = await db.insert(loans).values(req.body);
      res.json(newLoan);
    } catch (error) {
      res.status(500).json({ message: "Failed to create loan" });
    }
  });

  // Borrower routes
  app.get("/api/borrowers", async (req, res) => {
    try {
      const allBorrowers = await db.query.borrowers.findMany({
        with: {
          loans: true
        }
      });
      res.json(allBorrowers);
    } catch (error) {
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
          month: new Date(loan.createdAt).toLocaleString('default', { month: 'short' }),
          amount: parseFloat(loan.metricValue.toString())
        }))
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      res.status(500).json({ message: "Failed to fetch dashboard stats" });
    }
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
