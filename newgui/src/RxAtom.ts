import { bind, SUSPENSE } from "@react-rxjs/core";
import { createSignal } from "@react-rxjs/utils";
import { first, Observable } from "rxjs";

export class RxAtom<T = any> {
  changed$: Observable<T>;
  private sharedLatestObservable: Observable<T>;

  private emitter: (value: T) => void;
  private hook: { (): T; (): Exclude<T, typeof SUSPENSE>; };

  constructor(defaultValue: T) {
    const [observ$, emitter] = createSignal<T>();
    this.changed$ = observ$;
    this.emitter = emitter;
    const [hook, sharedLatest$] = bind(observ$, defaultValue);
    this.hook = hook;
    this.sharedLatestObservable = sharedLatest$;
  }

  public setValue = (value: T | ((oldValue: T) => T)) => {
    if (typeof value === "function") {
      const valueMapper = value as (oldValue: T) => T;
      this.getValue((value) => this.setValue(valueMapper(value)));
    } else {
      this.emitter(value);
    }
  };

  public useState = (): [T, typeof this.setValue] => {
    return [this.hook(), this.setValue];
  };

  public getValue = (consumer: (value: T) => void) => {
    this.sharedLatestObservable.pipe(first()).subscribe(value => {
      consumer(value);
    });
  };
}
