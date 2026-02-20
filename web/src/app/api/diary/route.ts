import { NextRequest, NextResponse } from "next/server"
import { readFileSync, readdirSync, existsSync, statSync } from "fs"
import { homedir } from "os"
import { join } from "path"

function getDiaryDir(): string {
  return process.env.CIV6_DIARY_DIR || join(homedir(), ".civ6-mcp")
}

/** List available diary files */
function listDiaries(dir: string): { filename: string; label: string; count: number }[] {
  if (!existsSync(dir)) return []
  const files = readdirSync(dir).filter((f) => f.startsWith("diary_") && f.endsWith(".jsonl"))
  return files
    .map((f) => {
      const match = f.match(/^diary_(.+?)_/)
      const label = match ? match[1].replace(/_/g, " ") : f
      let count = 0
      let mtime = 0
      try {
        const content = readFileSync(join(dir, f), "utf-8")
        count = content.split("\n").filter((l) => l.trim()).length
        mtime = statSync(join(dir, f)).mtimeMs
      } catch {
        // ignore
      }
      return { filename: f, label, count, mtime }
    })
    .sort((a, b) => b.mtime - a.mtime)
    .map(({ mtime: _, ...rest }) => rest)
}

/** Read entries from a specific diary file */
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
    // List available diaries
    const diaries = listDiaries(dir)
    return NextResponse.json({ diaries })
  }

  // Sanitize filename
  if (file.includes("..") || file.includes("/")) {
    return NextResponse.json({ error: "Invalid filename" }, { status: 400 })
  }

  const entries = readDiary(dir, file)
  return NextResponse.json({ entries })
}
