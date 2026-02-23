import {
  buildChannelConfigSchema,
  getChatChannelMeta,
  DEFAULT_ACCOUNT_ID,
  createReplyPrefixOptions,
  type ChannelPlugin,
  type OpenClawConfig,
} from "openclaw/plugin-sdk";
import { TarsServer } from "./server.js";
import { getTarsRuntime } from "./runtime.js";

const CHANNEL_ID = "tars-channel" as const;
const meta = getChatChannelMeta(CHANNEL_ID);

// Global server instance
let tarsServer: TarsServer | null = null;

/**
 * Handle an inbound message from the display, dispatch through OpenClaw's
 * reply pipeline, and send the reply back to the display.
 */
async function handleTarsInbound(params: {
  text: string;
  cfg: OpenClawConfig;
  accountId: string;
  log?: { info?: (msg: string) => void; warn?: (msg: string) => void; error?: (msg: string) => void };
}): Promise<void> {
  const { text, cfg, accountId, log } = params;
  const core = getTarsRuntime();

  const baseRoute = core.channel.routing.resolveAgentRoute({
    cfg,
    channel: CHANNEL_ID,
    accountId,
    peer: { kind: "direct", id: "tars-display" },
  });
  // Force a separate session for tars-channel so replies route through sendText
  const route = {
    ...baseRoute,
    sessionKey: `agent:main:tars-channel:tars-display`,
  };

  const storePath = core.channel.session.resolveStorePath(cfg.session?.store, {
    agentId: route.agentId,
  });

  const envelopeOptions = core.channel.reply.resolveEnvelopeFormatOptions(cfg);
  const previousTimestamp = core.channel.session.readSessionUpdatedAt({
    storePath,
    sessionKey: route.sessionKey,
  });

  const body = core.channel.reply.formatAgentEnvelope({
    channel: "TARS",
    from: "tars-display",
    timestamp: Date.now(),
    previousTimestamp,
    envelope: envelopeOptions,
    body: text,
  });

  const ctxPayload = core.channel.reply.finalizeInboundContext({
    Body: body,
    RawBody: text,
    CommandBody: text,
    From: "tars-channel:tars-display",
    To: "tars-channel:tars",
    SessionKey: route.sessionKey,
    AccountId: route.accountId,
    ChatType: "direct",
    ConversationLabel: "TARS Display",
    SenderName: "Noah",
    SenderId: "tars-display",
    Provider: CHANNEL_ID,
    Surface: CHANNEL_ID,
    MessageSid: `tars-${Date.now()}`,
    Timestamp: Date.now(),
    OriginatingChannel: CHANNEL_ID,
    OriginatingTo: "tars-channel:tars",
    CommandAuthorized: true,
  });

  await core.channel.session.recordInboundSession({
    storePath,
    sessionKey: ctxPayload.SessionKey ?? route.sessionKey,
    ctx: ctxPayload,
    onRecordError: (err) => {
      log?.error?.(`[tars-channel] Failed updating session meta: ${String(err)}`);
    },
  });

  const { onModelSelected, ...prefixOptions } = createReplyPrefixOptions({
    cfg,
    agentId: route.agentId,
    channel: CHANNEL_ID,
    accountId,
  });

  await core.channel.reply.dispatchReplyWithBufferedBlockDispatcher({
    ctx: ctxPayload,
    cfg,
    dispatcherOptions: {
      ...prefixOptions,
      deliver: async (payload) => {
        const replyText = (payload as { text?: string }).text?.trim() ?? "";
        if (replyText && tarsServer) {
          tarsServer.sendMessage(replyText);
          log?.info?.(`[tars-channel] Sent reply to display: ${replyText.substring(0, 50)}...`);
        }
      },
      onError: (err) => {
        log?.error?.(`[tars-channel] Reply delivery failed: ${String(err)}`);
      },
    },
    replyOptions: {
      onModelSelected,
    },
  });
}

export const tarsChannelPlugin: ChannelPlugin = {
  id: CHANNEL_ID,
  meta: { ...meta },
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
  reload: { configPrefixes: [`channels.${CHANNEL_ID}`] },
  configSchema: null,
  config: {
    listAccountIds: () => [DEFAULT_ACCOUNT_ID],
    resolveAccount: (cfg) => ({
      accountId: DEFAULT_ACCOUNT_ID,
      enabled: cfg.channels?.[CHANNEL_ID]?.enabled ?? false,
      config: cfg.channels?.[CHANNEL_ID] ?? {},
      token: "local",
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
      console.log(`[tars-channel] sendText called! to=${to}, text=${text?.substring(0, 80)}..., hasServer=${!!tarsServer}, clients=${tarsServer?.getClientCount() ?? 0}`);
      if (tarsServer) {
        tarsServer.sendMessage(text);
      }
      return { channel: CHANNEL_ID, messageId: `${CHANNEL_ID}-${Date.now()}` };
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

      // Stop existing server if running (cleanup from failed restart)
      if (tarsServer) {
        ctx.log?.warn(`[tars-channel] Cleaning up existing server`);
        try { await tarsServer.stop(); } catch {}
        tarsServer = null;
      }

      const log = {
        info: (msg: string) => ctx.log?.info?.(msg),
        warn: (msg: string) => ctx.log?.warn?.(msg),
        error: (msg: string) => ctx.log?.error?.(msg),
      };

      // Create and start Unix socket server
      tarsServer = new TarsServer({
        socketPath: "/tmp/tars-channel.sock",
        logger: log,
        onMessage: (text) => {
          log.info(`[tars-channel] Received input: ${text.substring(0, 80)}`);
          // Load fresh config for each message
          const cfg = ctx.cfg;
          handleTarsInbound({
            text,
            cfg: cfg as OpenClawConfig,
            accountId: ctx.accountId,
            log,
          }).catch((err) => {
            log.error(`[tars-channel] Inbound dispatch error: ${err instanceof Error ? err.message : String(err)}`);
            if (err instanceof Error && err.stack) {
              log.error(`[tars-channel] Stack: ${err.stack}`);
            }
          });
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
