import { MongoClient, Db, Collection } from "mongodb";
import { logger } from "./logger";

let client: MongoClient | null = null;
let db: Db | null = null;

export async function getMongoDb(): Promise<Db | null> {
  const uri = process.env["MONGODB_URI"];
  if (!uri) return null;

  if (db) return db;

  try {
    client = new MongoClient(uri, { serverSelectionTimeoutMS: 3000 });
    await client.connect();
    const dbName = process.env["MONGODB_DB"] ?? "smart_travel";
    db = client.db(dbName);
    logger.info({ dbName }, "MongoDB connected");
    return db;
  } catch (err) {
    logger.warn({ err }, "MongoDB connection failed — using in-memory fallback");
    client = null;
    db = null;
    return null;
  }
}

export async function getCollection<T extends object>(name: string): Promise<Collection<T> | null> {
  const database = await getMongoDb();
  if (!database) return null;
  return database.collection<T>(name);
}
