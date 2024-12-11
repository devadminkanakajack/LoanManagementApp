import type { Express } from "express";
import { createServer } from "http";
import { hash, compare } from "bcrypt";
import session from "express-session";
import { db } from "../db";
import { users, loans, borrowers, payments } from "@db/schema";
import { eq, and } from "drizzle-orm";
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

  // Serve static files from the React app
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  app.use(express.static(path.join(__dirname, '../dist')));

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
