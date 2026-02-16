import {
  buildChannelConfigSchema,
  getChatChannelMeta,
  DEFAULT_ACCOUNT_ID,
  type ChannelPlugin,
} from "openclaw/plugin-sdk";

const meta = getChatChannelMeta("tui");

// Minimal config schema for now
const TuiConfigSchema = {
  type: "object" as const,
  additionalProperties: false,
  properties: {
    enabled: { type: "boolean" as const },
    port: { type: "number" as const, default: 3030 },
  },
};

export const tuiPlugin: ChannelPlugin = {
  id: "tui",
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
  reload: { configPrefixes: ["channels.tui"] },
  configSchema: buildChannelConfigSchema(TuiConfigSchema),
  config: {
    listAccountIds: () => [DEFAULT_ACCOUNT_ID],
    resolveAccount: (cfg) => ({
      accountId: DEFAULT_ACCOUNT_ID,
      enabled: cfg.channels?.tui?.enabled ?? false,
      config: cfg.channels?.tui ?? {},
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
      // TODO: Implement actual message sending
      console.log(`[TUI] Sending to ${to}: ${text}`);
      return { channel: "tui", messageId: `tui-${Date.now()}` };
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
      ctx.log?.info(`[tui] Starting Terminal UI channel`);
      
      // TODO: Implement actual TUI server
      // This is where we'll start the WebSocket/HTTP server for the terminal
      
      // For now, just log that we're "running"
      return () => {
        ctx.log?.info(`[tui] Stopping Terminal UI channel`);
      };
    },
  },
};
