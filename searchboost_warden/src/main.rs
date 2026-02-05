use bollard::Docker;
use bollard::query_parameters::{LogsOptions};
use futures_util::stream::StreamExt;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::copy_bidirectional;
use failsafe::{Config, CircuitBreaker, failure_policy, backoff};
use std::sync::Arc;
use std::time::Duration;
use tracing::{info, error};
// 1. THE WRAPPER: Instead of naming the complex library type,
// we use 'impl CircuitBreaker' to hide it.
struct Warden<C> {
    breaker: C,
}

async fn start_log_observer(container_name: &str) -> anyhow::Result<()> {
    let docker = Docker::connect_with_local_defaults()?;

    // 1. Setup the Log File
    let mut file = std::fs::OpenOptions::new()
        .create(true).append(true).open("warden_observation.log")?;

    // 2. Corrected LogsOptions syntax (No generics needed here)
    let options = LogsOptions::<String> {
        follow: true,
        stdout: true,
        stderr: true,
        ..Default::default()
    };

    let mut stream = docker.logs(container_name, Some(options));

    info!("👀 Observer Started for: {}", container_name);

    while let Some(log_result) = stream.next().await {
        match log_result {
            Ok(log) => {
                let log_text = format!("{}", log);

                // 3. Highlight Alerts
                if log_text.to_uppercase().contains("ERROR") || log_text.to_uppercase().contains("TIMEOUT") {
                    println!("🚨 ALERT in {}: {}", container_name, log_text.trim());
                    writeln!(file, "[ALERT] {}", log_text.trim())?;
                } else {
                    writeln!(file, "[INFO] {}", log_text.trim())?;
                }
            }
            Err(e) => error!("Error reading logs: {}", e),
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    // 2. Build the breaker normally
    let retry_backoff = backoff::constant(Duration::from_secs(20));
    let policy = failure_policy::consecutive_failures(5, retry_backoff);
    let breaker = Config::new()
        .failure_policy(policy)
        .build();


    tokio::spawn(async {
        if let Err(e) = start_log_observer("sb_python_engine").await {
            error!("Observer task failed : {}", e);
        }
    });

        // 3. Put it in our wrapper. Now the 'Arc' type is just 'Arc<Warden<...>>'
    // Rust can infer this much more easily.
    let warden = Arc::new(Warden { breaker });

    let domain_address = "0.0.0.0:8000";
    let redis_address = "sb_redis:6379";

    let listener = TcpListener::bind(domain_address).await?;
    info!("🛡️ Warden Active: Proxying {} -> {}", domain_address, redis_address);
    info!("🛡️ Warden Active: Proxying traffic while observing logs...");
    loop {
        let (mut client_stream, addr) = listener.accept().await?;
        let warden_clone = Arc::clone(&warden);
        let target = redis_address.to_string();

        tokio::spawn(async move {
            // 1. We perform the connection attempt FIRST
            let connection_attempt = TcpStream::connect(&target).await;

            // 2. We pass the RESULT of that attempt to the breaker
            // This allows the breaker to record success/failure
            let result = warden_clone.breaker.call(|| {
                connection_attempt
            }); // Note: No .await here because call() returns the Result directly

            match result {
                Ok(mut redis_stream) => {
                    info!("🟢 Connection established for {}", addr);
                    let _ = copy_bidirectional(&mut client_stream, &mut redis_stream).await;
                }
                Err(e) => {
                    error!("🔴 Warden Blocked Request for {}: {:?}", addr, e);
                }
            }
        });
    }
}