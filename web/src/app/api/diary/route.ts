import { NextRequest, NextResponse } from "next/server"
import { readFileSync, readdirSync, existsSync, statSync } from "fs"
import { homedir } from "os"
import { join } from "path"

function getDiaryDir(): string {
  return process.env.CIV6_DIARY_DIR || join(homedir(), ".civ6-mcp")
}

/** List available diary files (excludes _cities companion files) */
function listDiaries(dir: string) {
  if (!existsSync(dir)) return []
  const files = readdirSync(dir).filter(
    (f) => f.startsWith("diary_") && f.endsWith(".jsonl") && !f.includes("_cities")
  )
  return files
    .map((f) => {
      const match = f.match(/^diary_(.+?)_/)
      const label = match ? match[1].replace(/_/g, " ") : f
      let count = 0
      let mtime = 0
      let agent_model: string | undefined
      let leader: string | undefined
      try {
        const content = readFileSync(join(dir, f), "utf-8")
        const lines = content.split("\n").filter((l) => l.trim())
        count = lines.length
        mtime = statSync(join(dir, f)).mtimeMs
        // Extract metadata from the first agent entry
        for (const line of lines) {
          try {
            const row = JSON.parse(line)
            if (row.is_agent) {
              if (row.agent_model) agent_model = row.agent_model
              if (row.leader) leader = row.leader
              break
            }
          } catch { break }
        }
      } catch {
        // ignore
      }
      const citiesFile = f.replace(".jsonl", "_cities.jsonl")
      const hasCities = existsSync(join(dir, citiesFile))
      return { filename: f, label, count, mtime, hasCities, agent_model, leader }
    })
    .sort((a, b) => b.mtime - a.mtime)
    .map(({ mtime: _, ...rest }) => rest)
}

/** Read entries from a specific JSONL file */
function readDiary(dir: string, filename: string) {
  const path = join(dir, filename)
  if (!existsSync(path)) return []
  const content = readFileSync(path, "utf-8")
  const lines = content.split("\n").filter((l) => l.trim())
  const entries = []
  for (const line of lines) {
    try {
      entries.push(JSON.parse(line))
    } catch {
      // skip malformed
    }
  }
  return entries
}

export async function GET(req: NextRequest) {
  const dir = getDiaryDir()
  const file = req.nextUrl.searchParams.get("file")

  if (!file) {
    const diaries = listDiaries(dir)
    return NextResponse.json({ diaries })
  }

  // Sanitize filename
  if (file.includes("..") || file.includes("/")) {
    return NextResponse.json({ error: "Invalid filename" }, { status: 400 })
  }

  // Serve cities companion file if requested
  const wantCities = req.nextUrl.searchParams.get("cities") === "1"
  if (wantCities) {
    const citiesFile = file.replace(".jsonl", "_cities.jsonl")
    const entries = readDiary(dir, citiesFile)
    return NextResponse.json({ entries })
  }

  const entries = readDiary(dir, file)
  return NextResponse.json({ entries })
}
