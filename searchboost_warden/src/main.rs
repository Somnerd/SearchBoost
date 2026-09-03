mod breaker;
mod configurator;
mod observer;
mod relay;

use configurator::Settings;
use std::sync::Arc;
use tokio_retry::strategy::{jitter, ExponentialBackoff};
use tokio_retry::Retry;
use tracing::{error, info};

pub struct Warden {
    pub breaker: breaker::WardenBreaker,
    pub redis_pool: deadpool_redis::Pool,
    pub db_pool: sqlx::PgPool,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let settings = Settings::load();
    let redis_url = settings.get_redis_url();

    let retry_strategy = ExponentialBackoff::from_millis(500).map(jitter).take(10); // Attempt for up to ~15-20s depending on jitter

    info!("Connecting to PostgreSQL...");
    let db_pool = Retry::start(retry_strategy.clone(), || async {
        sqlx::PgPool::connect(&settings.db.database_url()).await
    })
    .await
    .expect("FATAL: Could not connect to PostgreSQL metadata DB after retries");

    info!("Configuring Redis Connection Pool...");
    let redis_pool = deadpool_redis::Config::from_url(&redis_url)
        .create_pool(Some(deadpool_redis::Runtime::Tokio1))
        .expect("FATAL: Could not create Redis Connection Pool");

    let breaker = breaker::create_breaker(
        settings.breaker.breaker_threshold,
        settings.breaker.breaker_retry_seconds,
    );

    let warden = Arc::new(Warden {
        breaker,
        redis_pool,
        db_pool,
    });

    let obs_settings = settings.observer.clone();
    tokio::spawn(async move {
        info!("Warden: Initializing Observer Service...");
        if let Err(e) = observer::start_log_observer(obs_settings).await {
            error!("Observer failed: {}", e);
        }
    });

    info!(
        "Warden Unified Entry Point Active on :{}",
        settings.network.relay_port
    );
    relay::start_relay(settings.network.relay_port, warden).await;

    Ok(())
}
