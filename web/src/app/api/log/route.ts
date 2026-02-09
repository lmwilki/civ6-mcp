import { NextRequest, NextResponse } from "next/server"
import { readFileSync, existsSync } from "fs"
import { homedir } from "os"
import { join } from "path"

function getLogPath(): string {
  return process.env.CIV6_LOG_PATH || join(homedir(), ".civ6-mcp", "game_log.jsonl")
}

export async function GET(req: NextRequest) {
  const after = parseInt(req.nextUrl.searchParams.get("after") || "0", 10)
  const limit = parseInt(req.nextUrl.searchParams.get("limit") || "500", 10)

  const logPath = getLogPath()
  if (!existsSync(logPath)) {
    return NextResponse.json([])
  }

  try {
    const content = readFileSync(logPath, "utf-8")
    const lines = content.split("\n").filter((l) => l.trim())

    const entries = []
    for (let i = after; i < lines.length && entries.length < limit; i++) {
      try {
        const entry = JSON.parse(lines[i])
        entry.line = i + 1
        entries.push(entry)
      } catch {
        // Skip malformed lines
      }
    }

    return NextResponse.json(entries)
  } catch {
    return NextResponse.json([])
  }
}
