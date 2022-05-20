import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import env from "vite-plugin-env-compatible";
import { VitePWA } from 'vite-plugin-pwa'
import { join, resolve } from "path";
import electron from 'vite-plugin-electron';
import manifest from "./public/manifest.json";

export default defineConfig({
  plugins: [
    env(),
    react(),
    electron({
      main: {
        entry: 'electron/main/index.ts',
      },
    })
  ],
  resolve: {
    alias: [
      {
        find: /~(.+)/,
        replacement: join(process.cwd(), 'node_modules/$1'),
      }
    ]
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true
      }
    }
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
