import { Observable, Subject, Subscription } from "rxjs";

export type RpcId = string | number | null;

export type JsonRpcParams = any[] | {[key: string]: any};

export interface JsonRpcRequest {
  jsonrpc: '2.0';
  id?: RpcId;
  method: string;
  params?: JsonRpcParams;
}

interface JsonRpcResultResponse {
  jsonrpc: '2.0';
  id: RpcId;
  result: any;
}

interface JsonRpcErrorResponse {
  jsonrpc: '2.0';
  id: RpcId;
  error: {
    code: number;
    message: string;
    data?: any;
  };
}

export type JsonRpcResponse = JsonRpcResultResponse | JsonRpcErrorResponse;
export type JsonRpcDocument = JsonRpcRequest | JsonRpcResponse;

// websocket or electron ipc
export interface IRpcChannel {
  send(document: JsonRpcDocument): void;
  receiveChannel: Observable<JsonRpcDocument>;
  close(): void;
}

export class RpcClient {
  private _channel: IRpcChannel;
  private _channelSub: Subscription;
  private _nextId: number = 0;
  private _callbacks: Map<RpcId, (doc: JsonRpcDocument) => void> = new Map();
  private _notifyHandlers: ((method: string, params?: JsonRpcParams) => void)[] = [];

  private _notifySubject: Subject<JsonRpcDocument> = new Subject();

  public notificationObservable = this._notifySubject.asObservable();

  constructor(channel: IRpcChannel) {
    this._channel = channel;
  }

  public setChannel(channel: IRpcChannel): void {
    const oldChannel = this._channel;
    oldChannel.close();
    this._channel = channel;
    if (this._channelSub) {
      this._channelSub.unsubscribe();
    }
    this._channelSub = this._channel.receiveChannel.subscribe(this.handleReceive.bind(this));
  }

  public send<T>(method: string, params: JsonRpcParams): Promise<T> {
    const id = this._nextId++;
    return new Promise((resolve, reject) => {
      this._channel.send({ jsonrpc: '2.0', id, method, params });
      this._callbacks[id] = (result: JsonRpcResponse) => {
        if ('error' in result) {
          reject(result.error);
        } else {
          resolve(result.result);
        }
      };
    });
  }

  private handleReceive(document: JsonRpcDocument): void {
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
      this._notifySubject.next(document);
    }
  }

  public onNotify(handler: (method: string, params?: JsonRpcParams) => void): void {
    this._notifyHandlers.push(handler);
  }

}