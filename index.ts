import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";
import { tuiPlugin } from "./src/channel.js";

const plugin = {
  id: "tui",
  name: "Terminal UI",
  description: "Terminal UI channel plugin",
  configSchema: emptyPluginConfigSchema(),
  register(api: OpenClawPluginApi) {
    api.registerChannel({ plugin: tuiPlugin });
  },
};

export default plugin;
