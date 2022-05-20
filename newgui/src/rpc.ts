
export type RpcId = string | number;

type JsonRpcParams = any[] | object;

interface JsonRpcDocument {
  jsonrpc: '2.0';
  id?: RpcId;
  method?: string;
  params?: JsonRpcParams;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

// websocket or electron ipc
export interface RpcChannel {
  send(document: JsonRpcDocument): void;
  onReceive(callback: (document: JsonRpcDocument) => void): void;
  close(): void;
}

export class RpcClient {
  private _channel: RpcChannel;
  private _nextId: number = 0;
  private _callbacks: Map<RpcId, (doc: JsonRpcDocument) => void> = new Map();
  private _notifyHandlers: ((method: string, params?: JsonRpcParams) => void)[] = [];

  constructor(channel: RpcChannel) {
    this._channel = channel;
  }

  public setChannel(channel: RpcChannel): void {
    const oldChannel = this._channel;
    oldChannel.close();
    this._channel = channel;
    this._channel.onReceive(this.handleReceive.bind(this));
  }

  public send<T>(method: string, params: JsonRpcParams): Promise<T> {
    const id = this._nextId++;
    return new Promise((resolve, reject) => {
      this._channel.send({ jsonrpc: '2.0', id, method, params });
      this._callbacks[id] = (result: JsonRpcDocument) => {
        if (result.error) {
          reject(result.error);
        } else {
          resolve(result.result);
        }
      };
    });
  }

  public handleReceive(document: JsonRpcDocument): void {
    if (document.jsonrpc !== '2.0') {
      console.error('Invalid JSON-RPC document:', document);
      return;
    }
    if ('result' in document || 'error' in document) {
      const callback = this._callbacks.get(document.id);
      if (callback) {
        this._callbacks.delete(document.id);
        callback(document);
      } else {
        console.error('Received JSON-RPC response with unregistered id:', document);
      }
    } else if (typeof document.method === 'string') {
      this._notifyHandlers.forEach(handler => handler(document.method, document.params));
    }
  }

  public onNotify(handler: (method: string, params?: JsonRpcParams) => void): void {
    this._notifyHandlers.push(handler);
  }

}