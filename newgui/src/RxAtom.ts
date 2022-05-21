import { BehaviorSubject, Observable, skip } from "rxjs";
import React from "react";
export class RxAtom<T = any> {
  subject: BehaviorSubject<T>;
  // private sharedLatestObservable: Observable<T>;

  constructor(defaultValue: T) {
    this.subject = new BehaviorSubject(defaultValue);
  }

  public setValue(value: T | ((oldValue: T) => T)) {
    if (typeof value === "function") {
      const valueMapper = value as (oldValue: T) => T;
      this.setValue(valueMapper(this.getValue()));
    } else {
      this.subject.next(value);
    }
  };

  public asObservable(emitCurrent: boolean = false): Observable<T> {
    return emitCurrent ? this.subject : this.subject.pipe(skip(1));
  }

  public useState = (): [T, typeof this.setValue] => {
    const [state, setState] = React.useState(this.getValue());
    React.useEffect(() => {
      const subscription = this.asObservable().subscribe(v => {
        console.log("setState", v);
        setState(v);
      });
      return () => subscription.unsubscribe();
    })
    return [state, this.setValue.bind(this)];
  };

  public getValue(): T {
    return this.subject.getValue();
  };

  // public getValue2(consumer: (T)=>void) {
  //   this.sharedLatestObservable.pipe(first()).subscribe(value => {
  //     consumer(value);
  //   });
  // };
}

