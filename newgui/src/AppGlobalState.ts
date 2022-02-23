import { Subject } from "rxjs";
import { DrakModePreference, updateDarkMode } from "./darkmode";
import { RxAtom } from "./RxAtom";

function storedGlobalState<T>(key: string, defaultValue?: T): RxAtom<T> {
  const value = loadLocalStoragePreference(key, defaultValue);
  const state = new RxAtom(value);
  state.changed$.subscribe(value => {
    localStorage.setItem(key, JSON.stringify(value));
  });
  return state;
}

type CurrentTab = "overview" | "gallery" | "statistics" | "settings" | "about";

function loadLocalStoragePreference<T>(key: string, defaultValue: T): T {
  const preferenceJson = window.localStorage.getItem(key);
  if (preferenceJson !== null) {
    return JSON.parse(preferenceJson) as T;
  } else {
    return defaultValue;
  }
}

export const currentTab = new RxAtom<CurrentTab>(null);
export const updateAvailiable = new RxAtom<boolean>(false);
export const currentDevice = new RxAtom<string>(null);
export const dispatcherState = new RxAtom<string>('running');
export const colorScheme = storedGlobalState<DrakModePreference>("darkmode", "system");
colorScheme.changed$.subscribe(value => {
  updateDarkMode();
});

export const logScrollbackLimit = storedGlobalState<number>("logScrollbackLimit", 1500);
export const showAboutOnStartup = storedGlobalState<boolean>("showAboutOnStartup", true);
export const autoUpdate = storedGlobalState<boolean>("autoUpdate", true);

export const log$ = new Subject();
