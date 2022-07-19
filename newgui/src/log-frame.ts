import { ILogFrame, ILogRecord } from "./ILogFrame";

declare global {
    interface Window extends ILogFrame { 
    }
}


let logScrollbackLimit = 1500;
let logCount = 0;
let autoScroll = true;

let pendingRecords = document.createDocumentFragment();


function reflowCallback() {
    const container = document.querySelector('#log-container-body');
    const pendingCount = pendingRecords.childElementCount;
    if (logCount + pendingCount > logScrollbackLimit) {
        const trashBin = document.createDocumentFragment();
        const removeCount = logCount + pendingCount - logScrollbackLimit;
        let currentNodes = [...container.children];
        let childrenToRemove = currentNodes.slice(0, removeCount);
        trashBin.replaceChildren(...childrenToRemove); // detach from current parent
        trashBin.replaceChildren();  // ... then discard them
    }
    container.appendChild(pendingRecords);
    logCount = Math.min(logCount + pendingCount, logScrollbackLimit);
    if (autoScroll) {
        document.body.scrollTop = document.body.scrollHeight;
    }
}

const template = <HTMLTemplateElement>document.querySelector('#log-record-template');

window.addLogRecord = function (record: ILogRecord) {
    let newRecord = <DocumentFragment>template.content.cloneNode(true);
    newRecord.querySelector('.time-field').textContent = record.time.toISOString().substring(11, 23);
    newRecord.querySelector('.level-field').textContent = record.level;
    newRecord.querySelector('.message-field').textContent = record.message;
    (<HTMLElement>newRecord.querySelector('.log-record')).dataset.loglevel = record.level;
    if (pendingRecords.childElementCount == 0) {
        window.requestAnimationFrame(reflowCallback);
    }
    pendingRecords.appendChild(newRecord);
};

window.clearLog = function () {
    document.querySelector('#log-container-body').innerHTML = '';
};

window.setAutoScroll = function (value) {
    autoScroll = value;
};

window.setScrollBackLimit = function (limit) {
    logScrollbackLimit = limit;
    // window.requestAnimationFrame(reflowCallback);
};

window.setShowDebug = function (show) {
    document.querySelector('.log-container').classList.toggle('show-debug', show);
};

window.setDarkMode = function (dark) {
    document.body.classList.toggle('bp4-dark', dark);
};
