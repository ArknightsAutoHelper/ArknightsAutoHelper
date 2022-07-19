import React from 'react';
import ReactDOM from 'react-dom';
import { createRoot } from 'react-dom/client';
import './index.scss';
// import 'inobounce';
import App from './App';
// import * as serviceWorkerRegistration from './serviceWorkerRegistration';

import { FocusStyleManager } from '@blueprintjs/core';
import './darkmode';


FocusStyleManager.onlyShowFocusOnTabs();
const container = document.getElementById('root');
const root = createRoot(container!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// serviceWorkerRegistration.register();
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
