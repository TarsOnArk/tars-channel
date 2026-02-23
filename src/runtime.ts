import type { PluginRuntime } from "openclaw/plugin-sdk";

let runtime: PluginRuntime | null = null;

export function setTarsRuntime(next: PluginRuntime) {
  runtime = next;
}

export function getTarsRuntime(): PluginRuntime {
  if (!runtime) {
    throw new Error("TARS runtime not initialized");
  }
  return runtime;
}
