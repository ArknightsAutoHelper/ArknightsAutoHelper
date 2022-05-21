import { app, BrowserWindow, shell, ipcMain, nativeTheme, BrowserWindowConstructorOptions } from 'electron'
import { release } from 'os'
import path from 'path'
import contextMenu from 'electron-context-menu';

// Set application name for Windows 10+ notifications
if (process.platform === 'win32') app.setAppUserModelId(app.getName())

process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

let win: BrowserWindow | null = null

function getWindowTitleOverlaySetting() {
  // TODO: macOS/Linux
  return { color: nativeTheme.shouldUseDarkColors ? '#383e47' : '#ffffff', symbolColor: nativeTheme.shouldUseDarkColors ? '#abb3bf' : '#1c2127' };
}

function getBackgroundColor() {
  return nativeTheme.shouldUseDarkColors ? '#383e47' : '#ffffff';
}

const titleBarStyle = 'overlay';

function getTitleBarWindowOptions(style): BrowserWindowConstructorOptions {
  if (style === 'overlay') {
    return {
      titleBarStyle: 'hidden',
      titleBarOverlay: getWindowTitleOverlaySetting(),
    }
  }
  else return {};
}

async function createWindow() {
  win = new BrowserWindow({
    backgroundColor: getBackgroundColor(),
    ...getTitleBarWindowOptions(titleBarStyle),
    
    webPreferences: {
      contextIsolation: false,
      nodeIntegration: true,
      preload: path.join(__dirname, '../electron-preload/preload.js'),
    },
    width: 960,
    height: 640,
    // useContentSize: true,
    minWidth: 640,
    minHeight: 480,
    icon: path.join(__dirname, '../../public/favicon.ico'),
  })
  win.setMenu(null);
  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, '../renderer/index.html'))
  } else {
    // 🚧 Use ['ENV_NAME'] avoid vite:define plugin
    const url = `http://${process.env['VITE_DEV_SERVER_HOST']}:${process.env['VITE_DEV_SERVER_PORT']}`

    win.loadURL(url)
    // win.webContents.openDevTools()
  }

  // Make all links open with the browser, not with the application
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https:')) shell.openExternal(url)
    return { action: 'deny' }
  })

  nativeTheme.on('updated', () => {
    win.setTitleBarOverlay(getWindowTitleOverlaySetting());
  })
}

contextMenu({
    showSearchWithGoogle: false,
});
app.whenReady().then(createWindow)

ipcMain.handle("nativeTheme.themeSource", (event, action) => {
  if (action.hasOwnProperty("get")) {
    return nativeTheme.themeSource;
  } else {
    const value = action.set;
    nativeTheme.themeSource = value;
  }
})


ipcMain.handle("aah.titleBarStyle", (event, action) => {
  if ('get' in action) {
    return titleBarStyle;
  } else {
    console.log('setTitleBarStyle', action.set);
  }
})



app.on('window-all-closed', () => {
  win = null
  if (process.platform !== 'darwin') app.quit()
})



app.on('activate', () => {
  const allWindows = BrowserWindow.getAllWindows()
  if (allWindows.length) {
    allWindows[0].focus()
  } else {
    createWindow()
  }
})
