import { homedir } from "os";
import { join } from "path";
import { readFile } from "fs/promises";
import { existsSync } from "fs";

export function getDiaryDir(): string {
  return process.env.CIV6_DIARY_DIR || join(homedir(), ".civ6-mcp");
}

export async function readJsonl<T>(path: string): Promise<T[]> {
  if (!existsSync(path)) return [];
  const content = await readFile(path, "utf-8");
  const entries: T[] = [];
  for (const line of content.split("\n")) {
    if (!line.trim()) continue;
    try {
      entries.push(JSON.parse(line));
    } catch {
      // skip malformed
    }
  }
  return entries;
}
