import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";
import { tarsChannelPlugin } from "./src/channel.js";

const plugin = {
  id: "tars-channel",
  name: "TARS Channel",
  description: "TARS custom channel plugin",
  configSchema: emptyPluginConfigSchema(),
  register(api: OpenClawPluginApi) {
    api.registerChannel({ plugin: tarsChannelPlugin });
  },
};

export default plugin;
