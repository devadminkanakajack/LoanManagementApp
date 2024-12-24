import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from "@db/schema";

const pool = new Pool({
  host: 'localhost',
  port: 5050,
  user: 'postgres',
  database: 'postgres', // Replace with your actual database name
  password: 'root1234'       // Replace with your actual password
});

export const db = drizzle(pool, { schema });
