import {
  buildChannelConfigSchema,
  getChatChannelMeta,
  DEFAULT_ACCOUNT_ID,
  type ChannelPlugin,
} from "openclaw/plugin-sdk";
import { TarsServer } from "./server.js";

const meta = getChatChannelMeta("tars-channel");

// Global server instance
let tarsServer: TarsServer | null = null;

// Minimal config schema for now
const TarsChannelConfigSchema = {
  type: "object" as const,
  additionalProperties: false,
  properties: {
    enabled: { type: "boolean" as const },
    port: { type: "number" as const, default: 3030 },
  },
};

export const tarsChannelPlugin: ChannelPlugin = {
  id: "tars-channel",
  meta: {
    ...meta,
  },
  capabilities: {
    chatTypes: ["direct"],
    polls: false,
    reactions: false,
    threads: false,
    media: false,
    nativeCommands: false,
  },
  streaming: {
    blockStreamingCoalesceDefaults: { minChars: 100, idleMs: 500 },
  },
  reload: { configPrefixes: ["channels.tars-channel"] },
  configSchema: buildChannelConfigSchema(TarsChannelConfigSchema),
  config: {
    listAccountIds: () => [DEFAULT_ACCOUNT_ID],
    resolveAccount: (cfg) => ({
      accountId: DEFAULT_ACCOUNT_ID,
      enabled: cfg.channels?.["tars-channel"]?.enabled ?? false,
      config: cfg.channels?.["tars-channel"] ?? {},
      token: "",
    }),
    defaultAccountId: () => DEFAULT_ACCOUNT_ID,
    isConfigured: () => true,
    describeAccount: (account) => ({
      accountId: account.accountId,
      enabled: account.enabled,
      configured: true,
    }),
  },
  outbound: {
    deliveryMode: "direct",
    chunker: null,
    textChunkLimit: 4000,
    sendText: async ({ to, text }) => {
      if (tarsServer) {
        tarsServer.sendMessage(text);
      }
      return { channel: "tars-channel", messageId: `tars-channel-${Date.now()}` };
    },
  },
  status: {
    defaultRuntime: {
      accountId: DEFAULT_ACCOUNT_ID,
      running: false,
      lastStartAt: null,
      lastStopAt: null,
      lastError: null,
    },
    collectStatusIssues: () => [],
    buildChannelSummary: ({ snapshot }) => ({
      configured: snapshot.configured ?? true,
      running: snapshot.running ?? false,
      lastStartAt: snapshot.lastStartAt ?? null,
      lastStopAt: snapshot.lastStopAt ?? null,
      lastError: snapshot.lastError ?? null,
    }),
    buildAccountSnapshot: ({ account, runtime }) => ({
      accountId: account.accountId,
      enabled: account.enabled,
      configured: true,
      running: runtime?.running ?? false,
      lastStartAt: runtime?.lastStartAt ?? null,
      lastStopAt: runtime?.lastStopAt ?? null,
      lastError: runtime?.lastError ?? null,
    }),
  },
  gateway: {
    startAccount: async (ctx) => {
      ctx.log?.info(`[tars-channel] Starting TARS channel`);
      
      // Create and start Unix socket server
      tarsServer = new TarsServer({
        socketPath: "/tmp/tars-channel.sock",
        logger: {
          info: (msg) => ctx.log?.info?.(msg),
          warn: (msg) => ctx.log?.warn?.(msg),
          error: (msg) => ctx.log?.error?.(msg),
        },
      });
      
      try {
        await tarsServer.start();
        ctx.log?.info(`[tars-channel] Server started successfully`);
      } catch (err) {
        ctx.log?.error?.(
          `[tars-channel] Failed to start server: ${err instanceof Error ? err.message : String(err)}`
        );
        throw err;
      }
      
      // Return cleanup function
      return async () => {
        ctx.log?.info(`[tars-channel] Stopping TARS channel`);
        if (tarsServer) {
          await tarsServer.stop();
          tarsServer = null;
        }
      };
    },
  },
};
