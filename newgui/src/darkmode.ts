import { colorScheme } from './AppGlobalState';

export type DrakModePreference = "light" | "dark" | "system";

function setMode(dark: boolean) {
  const html = document.documentElement;
  const body = document.body;
  if (dark) {
    html.classList.add('bp3-dark');
    body.classList.add('bp3-dark');
    document.querySelector('meta[name="theme-color"]').setAttribute("content", '#394B59');
  } else {
    html.classList.remove('bp3-dark');
    body.classList.remove('bp3-dark');
    document.querySelector('meta[name="theme-color"]').setAttribute("content", '#FFFFFF');
  }
}

export function updateDarkMode() {
  let preference = colorScheme.getValue();
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

colorScheme.subject.subscribe(value => {
  updateDarkMode();
});

// export function setDarkModePreference(mode: DrakModePreference) {
//   window.localStorage.setItem("darkmode", mode);
//   updateDarkMode();
// }

updateDarkMode();
// window['setDarkModePreference'] = setDarkModePreference;
