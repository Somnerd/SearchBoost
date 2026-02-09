use bollard::Docker;
use bollard::query_parameters::{LogsOptions};
use futures_util::stream::StreamExt;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::copy_bidirectional;
use failsafe::{Config, CircuitBreaker, failure_policy, backoff};
use std::sync::Arc;
use std::time::Duration;
use std::io::Write;
use std::fs::OpenOptions;
use tracing::{info, error};

struct Warden<C> {
    breaker: C,
}

async fn start_log_observer(container_name: &str) -> anyhow::Result<()> {
    let docker = Docker::connect_with_local_defaults()?;

    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/logs/service_observation.log")?;

    let mut errors_file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/logs/service_errors.log")?;

    let options = LogsOptions{
        follow: true,
        stdout: true,
        stderr: true,
        ..Default::default()
    };

    let mut stream = docker.logs(container_name, Some(options));

    info!("Observer Started for: {}", container_name);

    while let Some(log_result) = stream.next().await {
        match log_result {
            Ok(log) => {
                let log_text = format!("{}", log);

                //TODO - Make this more robust with regex or structured log parsing and create dynamic log files per hour or day
                if log_text.to_uppercase().contains("ERROR")|| log_text.to_uppercase().contains("WARNING") || log_text.to_uppercase().contains("DEBUG") {
                    println!("ALERT in {}: {}", container_name, log_text.trim());
                    writeln!(errors_file, "[ALERT] {}", log_text.trim())?;
                }

                writeln!(file, "{}", log_text.trim())?;
            }
            Err(e) => error!("Error reading logs: {}", e),
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let retry_backoff = backoff::constant(Duration::from_secs(20));
    let policy = failure_policy::consecutive_failures(5, retry_backoff);
    let breaker = Config::new()
        .failure_policy(policy)
        .build();

    //TODO - Make this dynamic based on env vars or config files

    let service_container_name = "sb_worker";

    tokio::spawn(async {
        if let Err(e) = start_log_observer(service_container_name).await {
            error!("Observer task failed : {}", e);
        }
    });

    let warden = Arc::new(Warden { breaker });

    let domain_address = "0.0.0.0:8000";
    let redis_address = "sb_redis:6379";

    let listener = TcpListener::bind(domain_address).await?;
    info!("Warden Active: Proxying {} -> {}", domain_address, redis_address);
    info!("Warden Active: Proxying traffic while observing logs...");
    loop {
        let (mut client_stream, addr) = listener.accept().await?;
        let warden_clone = Arc::clone(&warden);
        let target = redis_address.to_string();

        tokio::spawn(async move {
            let connection_attempt = TcpStream::connect(&target).await;
            let result = warden_clone.breaker.call(|| {
                connection_attempt
            });

            match result {
                Ok(mut redis_stream) => {
                    info!("Connection established for {}", addr);
                    let _ = copy_bidirectional(&mut client_stream, &mut redis_stream).await;
                }
                Err(e) => {
                    error!("Warden Blocked Request for {}: {:?}", addr, e);
                }
            }
        });
    }
}