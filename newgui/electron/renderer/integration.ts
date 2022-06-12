
export type TitleBarStyle = "system" | "overlay";

export interface IElectronIntegration {
  setDarkModePreference(preference: string): Promise<void>;
  getDarkModePreference(): Promise<string>;
  getTitleBarStyle(): Promise<TitleBarStyle>;
  setTitleBarStyle(style: TitleBarStyle): Promise<void>;
}

declare global {
  interface Window {
    electronIntegration?: IElectronIntegration;
  }
}
