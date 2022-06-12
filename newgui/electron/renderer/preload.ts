import { ipcRenderer } from 'electron';
import { IElectronIntegration, TitleBarStyle } from './integration';

console.log('preload!');

window.electronIntegration = {
  async setDarkModePreference(preference: string): Promise<void> {
    if (['light', 'dark', 'system'].includes(preference)) {
      await ipcRenderer.invoke("nativeTheme.themeSource", { set: preference });
    } else {
      console.error('Invalid dark mode preference:', preference);
    }
  },

  async getDarkModePreference(): Promise<string> {
    return await ipcRenderer.invoke("nativeTheme.themeSource", { get: null });
  },

  getTitleBarStyle(): Promise<TitleBarStyle> {
    return ipcRenderer.invoke("aah.titleBarStyle", { get: null });
  },

  setTitleBarStyle(style: TitleBarStyle): Promise<void> {
    throw new Error('Method not implemented.');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.electronIntegration.getTitleBarStyle().then((style) => {
    if (style !== 'system') {
      console.log('using custom title bar');
      document.documentElement.classList.add('use-custom-title-bar');
    }
  })
});
