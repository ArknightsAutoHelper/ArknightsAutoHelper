import { Observable, Subject } from "rxjs";
import { IRpcChannel, JsonRpcDocument } from "./client";

export class WebSocketChannel implements IRpcChannel {
  private _ws: WebSocket;
  private _receiveSubject: Subject<JsonRpcDocument> = new Subject();
  public receiveChannel: Observable<JsonRpcDocument> = this._receiveSubject.asObservable();

  constructor(url: string) {
    this._ws = new WebSocket(url);
    this._ws.onmessage = (event) => {
      const document = JSON.parse(event.data);
      this._receiveSubject.next(document);
    };
  }

  send(document: JsonRpcDocument): void {
    this._ws.send(JSON.stringify(document));
  }
  close(): void {
    this._ws.close();
  }
}
