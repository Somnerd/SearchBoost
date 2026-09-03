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

use config::{Config, File, FileFormat};
use serde::Deserialize;
use std::env;

#[derive(Deserialize, Clone, Debug, PartialEq)]
pub struct NetworkSettings {
    pub relay_port: u16,
}

#[derive(Deserialize, Clone, Debug, PartialEq)]
pub struct RedisSettings {
    pub host: String,
    pub port: u16,
    pub password: Option<String>,
}

#[derive(Deserialize, Clone, Debug, PartialEq)]
pub struct ObserverSettings {
    pub container_name: Option<String>,
    pub container_label: Option<String>,
    pub log_path: String,
}

#[derive(Deserialize, Clone, Debug, PartialEq)]
pub struct BreakerSettings {
    pub breaker_threshold: u32,
    pub breaker_retry_seconds: u64,
}

#[derive(Deserialize, Clone, Debug, PartialEq)]
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
                format!(
                    "postgres://{}:{}@{}:{}/{}",
                    self.user, pass, self.host, self.port, self.database
                )
            }
            _ => {
                format!(
                    "postgres://{}@{}:{}/{}",
                    self.user, self.host, self.port, self.database
                )
            }
        }
    }
}

#[derive(Deserialize, Clone, Debug, PartialEq)]
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
        let master_path = master_env
            .clone()
            .unwrap_or_else(|_| "../configs/master_settings.yml".to_string());

        let discrete_env = env::var("WARDEN_CONFIG_PATH");
        let discrete_path = discrete_env
            .clone()
            .unwrap_or_else(|_| "../configs/warden.yml".to_string());

        let settings = Config::builder()
            .add_source(File::new(&master_path, FileFormat::Yaml).required(master_env.is_ok()))
            .add_source(File::new(&discrete_path, FileFormat::Yaml).required(discrete_env.is_ok()))
            .add_source(
                config::Environment::with_prefix("WARDEN")
                    .separator("__")
                    .keep_prefix(false),
            )
            .build()
            .expect("Warden Error: Could not find config file");

        let mut settings: Self = settings
            .try_deserialize()
            .expect("Warden Error: Config file format is invalid");

        // 🛡️ Elegant Environment Overrides
        // We prioritize explicit environment variables (e.g., from Docker secrets)
        // over the values found in YAML configuration files.
        let get_env = |var: &str| env::var(var).ok().filter(|s| !s.is_empty());

        if let Some(pass) = get_env("REDIS_PASSWORD") {
            settings.redis.password = Some(pass);
        }
        if let Some(pass) = get_env("DB_PASSWORD") {
            settings.db.password = Some(pass);
        }
        if let Some(user) = get_env("DB_USER") {
            settings.db.user = user;
        }
        if let Some(host) = get_env("DB_HOST") {
            settings.db.host = host;
        }
        if let Some(name) = get_env("DB_NAME").or_else(|| get_env("DB_DATABASE")) {
            settings.db.database = name;
        }
        if let Some(port) = get_env("DB_PORT").and_then(|s| s.parse().ok()) {
            settings.db.port = port;
        }
        if let Some(label) = get_env("WARDEN_OBSERVER_CONTAINER_LABEL") {
            settings.observer.container_label = Some(label);
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    // Mutex to synchronize environment variable manipulation across parallel tests
    static ENV_MUTEX: Mutex<()> = Mutex::new(());

    struct ScopedEnv {
        vars: Vec<(&'static str, Option<String>)>,
    }

    impl ScopedEnv {
        fn set(vars: &[(&'static str, &str)]) -> Self {
            let mut saved = Vec::new();
            for &(k, v) in vars {
                saved.push((k, env::var(k).ok()));
                // SAFETY: We hold ENV_MUTEX across the test lifetime to prevent data races.
                unsafe { env::set_var(k, v) };
            }
            ScopedEnv { vars: saved }
        }
    }

    impl Drop for ScopedEnv {
        fn drop(&mut self) {
            for (k, prev) in &self.vars {
                match prev {
                    Some(val) => unsafe { env::set_var(k, val) },
                    None => unsafe { env::remove_var(k) },
                }
            }
        }
    }

    fn dummy_settings(redis_pass: Option<String>) -> Settings {
        Settings {
            network: NetworkSettings { relay_port: 14141 },
            observer: ObserverSettings {
                container_name: None,
                container_label: None,
                log_path: "/tmp".to_string(),
            },
            breaker: BreakerSettings {
                breaker_threshold: 5,
                breaker_retry_seconds: 20,
            },
            redis: RedisSettings {
                host: "127.0.0.1".to_string(),
                port: 6379,
                password: redis_pass,
            },
            db: DatabaseSettings {
                host: "127.0.0.1".to_string(),
                port: 5432,
                user: "postgres".to_string(),
                password: None,
                database: "testdb".to_string(),
            },
        }
    }

    #[test]
    fn test_database_url_formatting() {
        let db_with_pass = DatabaseSettings {
            host: "postgres-host".to_string(),
            port: 5432,
            user: "sb_user".to_string(),
            password: Some("secret".to_string()),
            database: "sb_db".to_string(),
        };
        assert_eq!(
            db_with_pass.database_url(),
            "postgres://sb_user:secret@postgres-host:5432/sb_db"
        );

        let db_without_pass = DatabaseSettings {
            host: "postgres-host".to_string(),
            port: 5432,
            user: "sb_user".to_string(),
            password: None,
            database: "sb_db".to_string(),
        };
        assert_eq!(
            db_without_pass.database_url(),
            "postgres://sb_user@postgres-host:5432/sb_db"
        );

        let db_with_empty_pass = DatabaseSettings {
            host: "postgres-host".to_string(),
            port: 5432,
            user: "sb_user".to_string(),
            password: Some("".to_string()),
            database: "sb_db".to_string(),
        };
        assert_eq!(
            db_with_empty_pass.database_url(),
            "postgres://sb_user@postgres-host:5432/sb_db"
        );
    }

    #[test]
    fn test_redis_url_formatting() {
        assert_eq!(
            dummy_settings(Some("p@ssword".to_string())).get_redis_url(),
            "redis://:p@ssword@127.0.0.1:6379"
        );
        assert_eq!(
            dummy_settings(None).get_redis_url(),
            "redis://127.0.0.1:6379"
        );
        assert_eq!(
            dummy_settings(Some("".to_string())).get_redis_url(),
            "redis://127.0.0.1:6379"
        );
    }

    #[test]
    fn test_settings_load_with_environment_overrides() {
        let _lock = ENV_MUTEX.lock().unwrap();
        let _env = ScopedEnv::set(&[
            ("REDIS_PASSWORD", "redis_secret_pass_123"),
            ("DB_PASSWORD", "db_secret_pass_456"),
            ("DB_USER", "custom_postgres_user"),
            ("DB_HOST", "db.internal.local"),
            ("DB_NAME", "custom_searchboost"),
            ("DB_PORT", "5433"),
            (
                "WARDEN_OBSERVER_CONTAINER_LABEL",
                "com.searchboost.env=staging",
            ),
        ]);

        let settings = Settings::load();

        assert_eq!(
            settings.redis.password,
            Some("redis_secret_pass_123".to_string())
        );
        assert_eq!(settings.db.password, Some("db_secret_pass_456".to_string()));
        assert_eq!(settings.db.user, "custom_postgres_user");
        assert_eq!(settings.db.host, "db.internal.local");
        assert_eq!(settings.db.database, "custom_searchboost");
        assert_eq!(settings.db.port, 5433);
        assert_eq!(
            settings.observer.container_label,
            Some("com.searchboost.env=staging".to_string())
        );

        // Verify compound URLs generated from these overridden settings
        assert_eq!(
            settings.get_redis_url(),
            format!(
                "redis://:redis_secret_pass_123@{}:{}",
                settings.redis.host, settings.redis.port
            )
        );
        assert_eq!(
            settings.db.database_url(),
            "postgres://custom_postgres_user:db_secret_pass_456@db.internal.local:5433/custom_searchboost"
        );
    }

    #[test]
    fn test_settings_load_with_db_database_fallback() {
        let _lock = ENV_MUTEX.lock().unwrap();
        let _env = ScopedEnv::set(&[("DB_NAME", ""), ("DB_DATABASE", "fallback_database_name")]);

        let settings = Settings::load();
        assert_eq!(settings.db.database, "fallback_database_name");
    }

    #[test]
    fn test_settings_load_custom_config_path() {
        let _lock = ENV_MUTEX.lock().unwrap();
        let _env = ScopedEnv::set(&[
            ("MASTER_CONFIG_PATH", "../configs/master_settings.yml"),
            ("WARDEN_CONFIG_PATH", "../configs/warden.yml"),
            ("DB_PORT", "6543"),
        ]);

        let settings = Settings::load();
        assert_eq!(settings.network.relay_port, 14141);
        assert_eq!(settings.db.port, 6543);
    }
}
