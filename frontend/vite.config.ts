// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, nitro (build-only using cloudflare as a default target),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

const nitroPreset = process.env.NITRO_PRESET ?? "node-server";
const isVercel = nitroPreset === "vercel";

export default defineConfig({
  vite: {
    build: {
      rollupOptions: {
        onwarn(warning, warn) {
          if (warning.code === "MODULE_LEVEL_DIRECTIVE") return;
          warn(warning);
        },
      },
    },
  },
  nitro: {
    preset: nitroPreset,
    ...(!isVercel && {
      output: {
        dir: ".output",
        serverDir: ".output/server",
        publicDir: ".output/public",
      },
    }),
  },
  tanstackStart: {
    server: { entry: "server" },
  },
});
