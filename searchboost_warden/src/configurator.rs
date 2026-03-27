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

use serde::Deserialize;
use config::{Config, File, FileFormat};
use std::env;

#[derive(Deserialize, Clone)]
pub struct NetworkSettings {
    pub relay_port: u16,
}

#[derive(Deserialize, Clone)]
pub struct RedisSettings {
    pub host: String,
    pub port: u16,
    pub password: Option<String>,
}

#[derive(Deserialize, Clone)]
pub struct ObserverSettings {
    pub container_name: String,
    pub log_path: String,
}

#[derive(Deserialize, Clone)]
pub struct BreakerSettings {
    pub breaker_threshold: u32,
    pub breaker_retry_seconds: u64,
}

#[derive(Deserialize, Clone)]
pub struct WardenSettings {
    pub network: NetworkSettings,
    pub observer: ObserverSettings,
    pub breaker: BreakerSettings,
}

#[derive(Deserialize, Clone)]
pub struct Settings {
    pub warden: WardenSettings,
    pub redis: RedisSettings,
}

impl Settings {
    pub fn load() -> Self {
        let master_path = env::var("MASTER_CONFIG_PATH")
            .unwrap_or_else(|_| "../configs/master_settings.yml".to_string());
            
        let discrete_path = env::var("WARDEN_CONFIG_PATH")
            .unwrap_or_else(|_| "../configs/warden.yml".to_string());

        let settings = Config::builder()
            .add_source(File::new(&master_path, FileFormat::Yaml).required(false))
            .add_source(File::new(&discrete_path, FileFormat::Yaml).required(false))
            .add_source(config::Environment::with_prefix("WARDEN").separator("__"))
            .build()
            .expect("Warden Error: Could not find config file");

        settings.try_deserialize().expect("Warden Error: Config file format is invalid")
    }

    pub fn get_redis_url(&self) -> String {
        match &self.redis.password {
            Some(pass) if !pass.is_empty() => {
                format!("redis://:{}@{}:{}", pass, self.redis.host, self.redis.port)
            }
            _ => {
                format!("redis://{}:{}", self.redis.host, self.redis.port)
            }
        }
    }
}
