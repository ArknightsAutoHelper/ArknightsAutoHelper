import { colorSchemePreference } from './AppGlobalState';
import { RxAtom } from './RxAtom';
import * as electronIntegration from '../electron/renderer/integration';

export type DrakModePreference = "light" | "dark" | "system";

export const activeColorScheme = new RxAtom<DrakModePreference>(null);

if(window.electronIntegration) {
  colorSchemePreference.asObservable(true).subscribe((preference) => {
    window.electronIntegration.setDarkModePreference(preference);
  });
}

function setMode(dark: boolean) {
  const html = document.documentElement;
  const body = document.body;
  if (dark) {
    html.classList.add('bp4-dark');
    body.classList.add('bp4-dark');
    document.querySelector('meta[name="theme-color"]').setAttribute("content", '#394B59');
    activeColorScheme.setValue("dark");
  } else {
    html.classList.remove('bp4-dark');
    body.classList.remove('bp4-dark');
    document.querySelector('meta[name="theme-color"]').setAttribute("content", '#FFFFFF');
    activeColorScheme.setValue("light");
  }
}

export function updateDarkMode() {
  let preference = colorSchemePreference.getValue();
  // preference = preference ? JSON.parse(preference) : 'system';
  if (preference === "dark") {
    setMode(true);
  } else if (preference === "light") {
    setMode(false);
  } else {
    setMode(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
}

if (window.matchMedia) {
  const match = window.matchMedia('(prefers-color-scheme: dark)');
  try {
    match?.addEventListener('change', (e) => {
      updateDarkMode();
    })
  } catch (e) {}
}

colorSchemePreference.subject.subscribe(value => {
  updateDarkMode();
});

// export function setDarkModePreference(mode: DrakModePreference) {
//   window.localStorage.setItem("darkmode", mode);
//   updateDarkMode();
// }

updateDarkMode();
// window['setDarkModePreference'] = setDarkModePreference;
