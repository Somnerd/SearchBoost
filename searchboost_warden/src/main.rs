/*
 * SearchBoost: AI-Powered Semantic Search & Reliability Engine
 * Copyright (C) 2026 Nikolaos Alexandrakis
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 *
 * ---------------------------------------------------------------------
 * PROPRIETARY / COMMERCIAL LICENSING:
 * Use of this software in closed-source commercial applications or 
 * proprietary stacks is NOT permitted under AGPLv3. For a commercial 
 * license, please contact: nikolasalexandrakis.work@gmail.com
 * ---------------------------------------------------------------------
 */

mod observer;
mod relay;
mod configurator;
mod breaker;

use std::sync::Arc;
use tracing::{info, error};
use configurator::Settings;

pub struct Warden { 
    pub breaker: breaker::WardenBreaker,
    pub redis_client: redis::Client,
    pub db_pool: sqlx::PgPool,
}

#[tokio::main] 
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    
    let settings = Settings::load();
    let redis_url = settings.get_redis_url();
    
    let db_pool = sqlx::PgPool::connect(&settings.db.database_url()).await
        .expect("Warden Error: Could not connect to PostgreSQL metadata DB");

    let redis_client = redis::Client::open(redis_url)
        .expect("Invalid Redis URL in Config");
        
    let breaker = breaker::create_breaker(
        settings.breaker.breaker_threshold, 
        settings.breaker.breaker_retry_seconds
    );
    
    let warden = Arc::new(Warden { 
        breaker,
        redis_client,
        db_pool
    });

    let obs_name = settings.warden.observer.container_name.clone();
    let obs_path = settings.warden.observer.log_path.clone();

    tokio::spawn(async move {
        info!("Warden: Attempting to connect to Docker for container: {}", obs_name);
        if let Err(e) = observer::start_log_observer(&obs_name, &obs_path).await {
            error!("Observer failed: {}", e);
            info!("Are you running outside Docker?");
        }
    });

    info!("Warden Unified Entry Point Active on :{}", settings.warden.network.relay_port);
    relay::start_relay(settings.warden.network.relay_port, warden).await;

    Ok(())
}