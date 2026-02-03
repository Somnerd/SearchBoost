use tokio::net::{TcpListener, TcpStream};
use tokio::io::copy_bidirectional;
// Note: we use Backoff and CircuitBreaker traits for the methods to be visible
use failsafe::{Config, backoff, CircuitBreaker};
use std::sync::Arc;
use tracing::{info, error};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    
    // 1. Fixed Config: Use consecutive_failures backoff
    // We also explicitly type the breaker so Arc knows what it's holding
    let breaker = Config::new()
        .backoff(backoff::consecutive_failures(5))
        .cooldown(std::time::Duration::from_secs(20))
        .build();

    // We wrap it in Arc for thread safety.
    // We don't need to specify the full complex type if we use it correctly below.
    let breaker = Arc::new(breaker);

    let domain_address = "0.0.0.0:8000";
    let redis_address = "sb_redis:6379";

    let listener = TcpListener::bind(domain_address).await?;
    info!("🛡️ Warden Active: Proxying {} -> {}", domain_address, redis_address);

    loop {
        let (mut client_stream, addr) = listener.accept().await?;
        let breaker_clone = Arc::clone(&breaker);

        // Convert to String to move into the async block safely
        let target = redis_address.to_string();

        tokio::spawn(async move {
            // .call() requires the future to be returned.
            // We use 'inner' to help the compiler infer the error type.
            let result = breaker_clone.call(|| {
                TcpStream::connect(target.clone())
            }).await;

            match result {
                Ok(mut redis_stream) => {
                    info!("🟢 Connection established for {}", addr);
                    let _ = copy_bidirectional(&mut client_stream, &mut redis_stream).await;
                }
                Err(e) => {
                    // This error 'e' can be a circuit breaker error or a connection error
                    error!("🔴 Request blocked: {:?}. Warden circuit may be OPEN.", e);
                }
            }
        });
    }
}