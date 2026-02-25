import { homedir } from "os";
import { join } from "path";

export function getLogDir(): string {
  return process.env.CIV6_LOG_DIR || join(homedir(), ".civ6-mcp");
}

export function getLogFilePath(game: string): string {
  return join(getLogDir(), `log_${game}.jsonl`);
}
