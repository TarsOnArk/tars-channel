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
}

export class TarsServer {
  private server: net.Server | null = null;
  private clients: Set<net.Socket> = new Set();
  private socketPath: string;
  private logger: TarsServerOptions["logger"];

  constructor(options: TarsServerOptions = {}) {
    this.socketPath = options.socketPath || "/tmp/tars-channel.sock";
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

        socket.on("error", (err) => {
          this.logger?.error?.(`[tars-channel] Socket error: ${err.message}`);
        });

        socket.on("close", () => {
          this.logger?.info?.(`[tars-channel] Display disconnected`);
          this.clients.delete(socket);
        });

        // Handle incoming messages from display (future use)
        socket.on("data", (data) => {
          try {
            const msg = JSON.parse(data.toString());
            this.logger?.info?.(`[tars-channel] Received from display: ${JSON.stringify(msg)}`);
            // TODO: Handle messages from display (e.g., button presses, voice input)
          } catch (err) {
            this.logger?.warn?.(`[tars-channel] Invalid message from display`);
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
      client.destroy();
    }
    this.clients.clear();

    // Close server
    if (this.server) {
      return new Promise((resolve) => {
        this.server!.close(() => {
          this.logger?.info?.(`[tars-channel] Server stopped`);
          // Clean up socket file
          if (fs.existsSync(this.socketPath)) {
            fs.unlinkSync(this.socketPath);
          }
          resolve();
        });
      });
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
