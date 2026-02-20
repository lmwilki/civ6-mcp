import { NextRequest, NextResponse } from "next/server"
import { readFileSync, existsSync } from "fs"
import { join } from "path"
import { getLogDir, getLogPath } from "./shared"

export async function GET(req: NextRequest) {
  const after = parseInt(req.nextUrl.searchParams.get("after") || "0", 10)
  const limit = parseInt(req.nextUrl.searchParams.get("limit") || "2000", 10)
  const session = req.nextUrl.searchParams.get("session")

  // If a session is specified, read its dedicated file directly (no filtering needed)
  // Otherwise fall back to the central log
  let logPath: string
  if (session) {
    const sessionFile = join(getLogDir(), `game_log_${session}.jsonl`)
    logPath = existsSync(sessionFile) ? sessionFile : getLogPath()
  } else {
    logPath = getLogPath()
  }

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
        // When reading central log without a session file, still filter
        if (session && entry.session !== session) continue
        entry.line = i + 1
        entries.push(entry)
      } catch {
        // Skip malformed lines
      }
    }

    return NextResponse.json(entries, {
      headers: { "X-Total-Lines": String(lines.length) },
    })
  } catch {
    return NextResponse.json([])
  }
}
