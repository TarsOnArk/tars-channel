import type { ChannelPlugin, OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";
import { tarsChannelPlugin } from "./src/channel.js";
import { setTarsRuntime } from "./src/runtime.js";

const plugin = {
  id: "tars-channel",
  name: "TARS Channel",
  description: "TARS custom channel plugin",
  configSchema: emptyPluginConfigSchema(),
  register(api: OpenClawPluginApi) {
    setTarsRuntime(api.runtime);
    api.registerChannel({ plugin: tarsChannelPlugin as ChannelPlugin });
  },
};

export default plugin;
