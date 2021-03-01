use std::time::Instant;

#[cfg(feature = "wasm")]
wasm_json::pass_json!(func);

#[cfg(feature = "bin")]
wasm_json::json_args!(func);

pub fn func(_json: serde_json::Value) -> Result<serde_json::Value, anyhow::Error> {
    let time = Instant::now();

    let p = primal::Primes::all().nth(20000001 - 1).unwrap();

    Ok(serde_json::json!({
        "prime": p,
        "calc_time": time.elapsed().as_millis() as u64
    }))
}
