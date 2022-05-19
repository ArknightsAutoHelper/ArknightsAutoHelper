import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import env from "vite-plugin-env-compatible";
import { join, resolve } from "path";
export default defineConfig({
    plugins: [env(), react()],
    resolve: {
        alias: [
            {
                find: /~(.+)/,
                replacement: join(process.cwd(), 'node_modules/$1'),
            }
        ]
    },
    build: {
        rollupOptions: {
          input: {
            main: resolve(__dirname, 'index.html'),
            logFrame: resolve(__dirname, 'log-frame.html')
          }
        }
      }
});
