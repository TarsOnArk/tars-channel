/**
 * TARS Channel Unix Socket Server
 * Provides communication between OpenClaw and the PyQt5 display
 */
import * as net from "node:net";
import * as fs from "node:fs";
import * as path from "node:path";

export interface TarsServerOptions {
  socketPath?: string;
  logger?: {
    info?: (msg: string) => void;
    warn?: (msg: string) => void;
    error?: (msg: string) => void;
  };
  onMessage?: (text: string) => void;
}

export class TarsServer {
  private server: net.Server | null = null;
  private clients: Set<net.Socket> = new Set();
  private socketPath: string;
  private logger: TarsServerOptions["logger"];
  private onMessage?: (text: string) => void;

  constructor(options: TarsServerOptions = {}) {
    this.socketPath = options.socketPath || "/tmp/tars-channel.sock";
    this.onMessage = options.onMessage;
    this.logger = options.logger || {
      info: console.log,
      warn: console.warn,
      error: console.error,
    };
  }

  async start(): Promise<void> {
    // Clean up old socket if it exists
    if (fs.existsSync(this.socketPath)) {
      fs.unlinkSync(this.socketPath);
    }

    return new Promise((resolve, reject) => {
      this.server = net.createServer((socket) => {
        this.logger?.info?.(`[tars-channel] Display connected`);
        this.clients.add(socket);

        // Buffer for incomplete messages
        let buffer = "";

        socket.on("error", (err) => {
          this.logger?.error?.(`[tars-channel] Socket error: ${err.message}`);
        });

        socket.on("close", () => {
          this.logger?.info?.(`[tars-channel] Display disconnected`);
          this.clients.delete(socket);
        });

        // Handle incoming messages from display
        socket.on("data", (data) => {
          this.logger?.info?.(`[tars-channel] Received ${data.length} bytes of data`);
          buffer += data.toString();
          
          // Process complete messages (newline-delimited JSON)
          while (buffer.includes("\n")) {
            const idx = buffer.indexOf("\n");
            const line = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 1);
            
            if (!line.trim()) continue;
            
            this.logger?.info?.(`[tars-channel] Processing line: ${line.substring(0, 100)}`);
            try {
              const msg = JSON.parse(line);
              this.logger?.info?.(`[tars-channel] Parsed message type: ${msg.type}`);
              if (msg.type === "input" && msg.text && this.onMessage) {
                this.logger?.info?.(`[tars-channel] Received input from display: "${msg.text.substring(0, 50)}..."`);
                this.onMessage(msg.text);
              } else {
                this.logger?.warn?.(`[tars-channel] Message not processed: type=${msg.type}, hasText=${!!msg.text}, hasCallback=${!!this.onMessage}`);
              }
            } catch (err) {
              this.logger?.error?.(`[tars-channel] Error processing message: ${err instanceof Error ? err.message : String(err)}`);
              this.logger?.error?.(`[tars-channel] Stack: ${err instanceof Error ? err.stack : 'no stack'}`);
            }
          }
        });
      });

      this.server.on("error", (err) => {
        this.logger?.error?.(`[tars-channel] Server error: ${err.message}`);
        reject(err);
      });

      this.server.listen(this.socketPath, () => {
        this.logger?.info?.(`[tars-channel] Socket server listening on ${this.socketPath}`);
        // Set socket permissions so display app can connect
        fs.chmodSync(this.socketPath, 0o666);
        resolve();
      });
    });
  }

  async stop(): Promise<void> {
    // Close all client connections
    for (const client of this.clients) {
      try {
        client.destroy();
      } catch (err) {
        // Ignore errors when destroying clients
      }
    }
    this.clients.clear();

    // Close server
    if (this.server) {
      await new Promise<void>((resolve) => {
        this.server!.close(() => {
          this.logger?.info?.(`[tars-channel] Server stopped`);
          resolve();
        });
      });
      this.server = null;
    }
    
    // Always clean up socket file (even if server was already stopped)
    if (fs.existsSync(this.socketPath)) {
      try {
        fs.unlinkSync(this.socketPath);
        this.logger?.info?.(`[tars-channel] Cleaned up socket file`);
      } catch (err) {
        this.logger?.warn?.(`[tars-channel] Failed to clean socket: ${err}`);
      }
    }
  }

  /**
   * Send a message to all connected displays
   */
  sendMessage(text: string): void {
    const msg = JSON.stringify({
      type: "message",
      text: text,
      timestamp: Date.now(),
    }) + "\n";

    for (const client of this.clients) {
      try {
        client.write(msg);
      } catch (err) {
        this.logger?.error?.(`[tars-channel] Failed to send to client: ${err}`);
      }
    }
  }

  /**
   * Get number of connected displays
   */
  getClientCount(): number {
    return this.clients.size;
  }
}
