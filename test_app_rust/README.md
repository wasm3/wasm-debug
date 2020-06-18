## Building

Install the `wasm32-wasi` target:
```
$ rustup target add wasm32-wasi
```

You should now be able to compile:
```
$ cargo build --target=wasm32-wasi
$ cp ./target/wasm32-wasi/debug/app.wasm ./
```
