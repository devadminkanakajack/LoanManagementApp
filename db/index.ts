import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from "@db/schema";

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  user: 'postgres',
  database: 'your_database_name', // Replace with your actual database name
  password: 'your_password'       // Replace with your actual password
});

export const db = drizzle(pool, { schema });
