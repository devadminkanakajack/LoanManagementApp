import { pgTable, text, serial, timestamp, boolean, decimal, json, integer } from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { relations } from 'drizzle-orm';

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").unique().notNull(),
  password: text("password").notNull(),
  role: text("role", { enum: ['super_admin', 'administrator', 'sales_officer', 'accounts_officer', 'recoveries_officer', 'office_admin', 'borrower'] }).notNull(),
  email: text("email").unique().notNull(),
  fullName: text("full_name").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
  permissions: json("permissions").$type<string[]>().default(['view']),
});

export const borrowers = pgTable("borrowers", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id),
  phoneNumber: text("phone_number").notNull(),
  address: text("address").notNull(),
  employmentStatus: text("employment_status").notNull(),
  monthlyIncome: decimal("monthly_income").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const loans = pgTable("loans", {
  id: serial("id").primaryKey(),
  borrowerId: integer("borrower_id").references(() => borrowers.id),
  amount: decimal("amount").notNull(),
  term: integer("term").notNull(), // in months
  interestRate: decimal("interest_rate").notNull(),
  status: text("status", { enum: ['pending', 'approved', 'rejected', 'active', 'completed', 'defaulted'] }).notNull(),
  purpose: text("purpose").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
  approvedBy: integer("approved_by").references(() => users.id),
  approvedAt: timestamp("approved_at"),
});

export const payments = pgTable("payments", {
  id: serial("id").primaryKey(),
  loanId: integer("loan_id").references(() => loans.id),
  amount: decimal("amount").notNull(),
  paymentDate: timestamp("payment_date").notNull(),
  status: text("status", { enum: ['pending', 'completed', 'failed'] }).notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const usersRelations = relations(users, ({ many }) => ({
  loans: many(loans),
  borrowers: many(borrowers),
}));

export const borrowersRelations = relations(borrowers, ({ one, many }) => ({
  user: one(users, {
    fields: [borrowers.userId],
    references: [users.id],
  }),
  loans: many(loans),
}));

export const loansRelations = relations(loans, ({ one, many }) => ({
  borrower: one(borrowers, {
    fields: [loans.borrowerId],
    references: [borrowers.id],
  }),
  approver: one(users, {
    fields: [loans.approvedBy],
    references: [users.id],
  }),
  payments: many(payments),
}));

export const paymentsRelations = relations(payments, ({ one }) => ({
  loan: one(loans, {
    fields: [payments.loanId],
    references: [loans.id],
  }),
}));

export const insertUserSchema = createInsertSchema(users);
export const selectUserSchema = createSelectSchema(users);
export const insertBorrowerSchema = createInsertSchema(borrowers);
export const insertLoanSchema = createInsertSchema(loans);
export const insertPaymentSchema = createInsertSchema(payments);
