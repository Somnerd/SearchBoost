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
pub struct DatabaseSettings {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: Option<String>,
    pub database: String,
}

impl DatabaseSettings {
    pub fn database_url(&self) -> String {
        match &self.password {
            Some(pass) if !pass.is_empty() => {
                format!("postgres://{}:{}@{}:{}/{}", self.user, pass, self.host, self.port, self.database)
            }
            _ => {
                format!("postgres://{}@{}:{}/{}", self.user, self.host, self.port, self.database)
            }
        }
    }
}

#[derive(Deserialize, Clone)]
pub struct Settings {
    pub network: NetworkSettings,
    pub observer: ObserverSettings,
    pub breaker: BreakerSettings,
    pub redis: RedisSettings,
    pub db: DatabaseSettings,
}

impl Settings {
    pub fn load() -> Self {
        // Bootstrap: Determine paths to master and discrete YAML configs via ENV
        let master_env = env::var("MASTER_CONFIG_PATH");
        let master_path = master_env.clone().unwrap_or_else(|_| "../configs/master_settings.yml".to_string());
            
        let discrete_env = env::var("WARDEN_CONFIG_PATH");
        let discrete_path = discrete_env.clone().unwrap_or_else(|_| "../configs/warden.yml".to_string());
 
        let settings = Config::builder()
            .add_source(File::new(&master_path, FileFormat::Yaml).required(master_env.is_ok()))
            .add_source(File::new(&discrete_path, FileFormat::Yaml).required(discrete_env.is_ok()))
            .add_source(config::Environment::with_prefix("WARDEN").separator("__").keep_prefix(false))
            .build()
            .expect("Warden Error: Could not find config file");

        let mut settings: Self = settings.try_deserialize()
            .expect("Warden Error: Config file format is invalid");

        // Explicit environment overrides for shared secrets
        if let Ok(pass) = env::var("REDIS_PASSWORD") {
            if !pass.is_empty() {
                settings.redis.password = Some(pass);
            }
        }
        if let Ok(pass) = env::var("DB_PASSWORD") {
            if !pass.is_empty() {
                settings.db.password = Some(pass);
            }
        }
        if let Ok(user) = env::var("DB_USER") {
            if !user.is_empty() {
                settings.db.user = user;
            }
        }
        if let Ok(host) = env::var("DB_HOST") {
            if !host.is_empty() {
                settings.db.host = host;
            }
        }
        if let Ok(port_str) = env::var("DB_PORT") {
            if let Ok(port) = port_str.parse::<u16>() {
                settings.db.port = port;
            }
        }
        if let Ok(name) = env::var("DB_NAME") {
            if !name.is_empty() {
                settings.db.database = name;
            }
        } else if let Ok(name) = env::var("DB_DATABASE") {
            if !name.is_empty() {
                settings.db.database = name;
            }
        }

        settings
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
