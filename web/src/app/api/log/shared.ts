import { homedir } from "os"
import { join } from "path"

export function getLogDir(): string {
  return process.env.CIV6_LOG_DIR || join(homedir(), ".civ6-mcp")
}

export function getLogPath(): string {
  return process.env.CIV6_LOG_PATH || join(getLogDir(), "game_log.jsonl")
}
