import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import env from "vite-plugin-env-compatible";
import { join, resolve } from "path";
import electron from 'vite-plugin-electron';

export default defineConfig({
  plugins: [
    env(),
    react(),
    electron({
      main: {
        entry: 'electron/main/index.ts',
      },
      preload: {
        input: join(__dirname, 'electron/renderer/preload.ts'),
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
