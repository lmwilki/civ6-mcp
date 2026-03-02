import { NextRequest, NextResponse } from "next/server";
import { readFile, readdir, stat } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { getDiaryDir } from "../log/shared";

/** List available diary files (excludes _cities companion files) */
async function listDiaries(dir: string) {
  if (!existsSync(dir)) return [];
  const allFiles = await readdir(dir);
  const files = allFiles.filter(
    (f) =>
      f.startsWith("diary_") && f.endsWith(".jsonl") && !f.includes("_cities"),
  );
  const results = await Promise.all(
    files.map(async (f) => {
      const match = f.match(/^diary_(.+?)_/);
      const label = match ? match[1].replace(/_/g, " ") : f;
      let count = 0;
      let mtime = 0;
      let agentModel: string | undefined;
      let score: number | undefined;
      let civ: string | undefined;
      let leader: string | undefined;
      try {
        const content = await readFile(join(dir, f), "utf-8");
        const lines = content.split("\n").filter((l) => l.trim());
        count = lines.length;
        const fileStat = await stat(join(dir, f));
        mtime = fileStat.mtimeMs;
        // Extract agent fields from agent rows
        for (const line of lines) {
          try {
            const row = JSON.parse(line);
            if (row.is_agent) {
              if (row.agent_model && !agentModel) agentModel = row.agent_model;
              if (row.civ && !civ) civ = row.civ;
              if (row.leader && !leader) leader = row.leader;
              if (typeof row.score === "number") score = row.score; // keep latest
            }
          } catch {
            /* skip malformed */
          }
        }
      } catch {
        // ignore
      }
      const citiesFile = f.replace(".jsonl", "_cities.jsonl");
      const hasCities = existsSync(join(dir, citiesFile));
      // Use civ name from data (properly cased) over filename-derived label
      const displayLabel = civ || label;
      return { filename: f, label: displayLabel, leader, count, mtime, hasCities, agentModel, score };
    }),
  );
  return results
    .sort((a, b) => b.mtime - a.mtime)
    .map(({ mtime, ...rest }) => ({ ...rest, lastUpdated: mtime }));
}

/** Read entries from a specific JSONL file */
async function readDiary(dir: string, filename: string) {
  const path = join(dir, filename);
  if (!existsSync(path)) return [];
  const content = await readFile(path, "utf-8");
  const lines = content.split("\n").filter((l) => l.trim());
  const entries = [];
  for (const line of lines) {
    try {
      entries.push(JSON.parse(line));
    } catch {
      // skip malformed
    }
  }
  return entries;
}

export async function GET(req: NextRequest) {
  const dir = getDiaryDir();
  const file = req.nextUrl.searchParams.get("file");

  if (!file) {
    const diaries = await listDiaries(dir);
    return NextResponse.json({ diaries });
  }

  // Sanitize filename
  if (file.includes("..") || file.includes("/")) {
    return NextResponse.json({ error: "Invalid filename" }, { status: 400 });
  }

  // Serve cities companion file if requested
  const wantCities = req.nextUrl.searchParams.get("cities") === "1";
  if (wantCities) {
    const citiesFile = file.replace(".jsonl", "_cities.jsonl");
    const entries = await readDiary(dir, citiesFile);
    return NextResponse.json({ entries });
  }

  const entries = await readDiary(dir, file);
  return NextResponse.json({ entries });
}
