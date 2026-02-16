import {
  buildChannelConfigSchema,
  getChatChannelMeta,
  DEFAULT_ACCOUNT_ID,
  type ChannelPlugin,
} from "openclaw/plugin-sdk";

const meta = getChatChannelMeta("tars-channel");

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
      // TODO: Implement actual message sending
      console.log(`[TARS-CHANNEL] Sending to ${to}: ${text}`);
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
      
      // TODO: Implement actual channel server
      // This is where we'll start the WebSocket/HTTP server
      
      // For now, just log that we're "running"
      return () => {
        ctx.log?.info(`[tars-channel] Stopping TARS channel`);
      };
    },
  },
};
