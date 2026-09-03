/*
 * SearchBoost: AI-Powered Semantic Search & Reliability Engine
 * Copyright (C) 2026 Nikolaos Alexandrakis
 * Licensed under the MIT License.
 */

use crate::configurator::ObserverSettings;
use bollard::container::{ListContainersOptions, LogsOptions};
use bollard::Docker;
use futures_util::stream::StreamExt;
use std::collections::HashMap;
use std::io::Write;
use tracing::{error, info, warn};

pub async fn start_log_observer(settings: ObserverSettings) -> anyhow::Result<()> {
    info!("Starting Warden Observer Service");
    let docker = Docker::connect_with_local_defaults()?;

    std::fs::create_dir_all(&settings.log_path)
        .unwrap_or_else(|e| warn!("Could not create log dir: {}", e));

    let log_path = settings.log_path.clone();

    if let Some(label) = settings.container_label {
        info!("Warden: Label-based discovery active for: {}", label);
        let mut monitored_containers: std::collections::HashSet<String> =
            std::collections::HashSet::new();

        loop {
            let mut filters = HashMap::new();
            filters.insert("label".to_string(), vec![label.clone()]);

            let options = ListContainersOptions {
                all: true,
                filters,
                ..Default::default()
            };

            if let Ok(containers) = docker.list_containers(Some(options)).await {
                for container in containers {
                    if let Some(id) = container.id {
                        if !monitored_containers.contains(&id) {
                            monitored_containers.insert(id.clone());
                            let docker_clone = docker.clone();
                            let path_clone = log_path.clone();
                            let name = container
                                .names
                                .unwrap_or_default()
                                .first()
                                .cloned()
                                .unwrap_or_else(|| id.clone());

                            tokio::spawn(async move {
                                if let Err(e) =
                                    monitor_single_container(&docker_clone, &id, &name, &path_clone)
                                        .await
                                {
                                    error!("Warden: Failed to monitor container {}: {}", id, e);
                                }
                            });
                        }
                    }
                }
            }
            tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
        }
    } else if let Some(container_name) = settings.container_name {
        info!(
            "Warden: Fixed-name observation active for: {}",
            container_name
        );
        monitor_single_container(&docker, &container_name, &container_name, &log_path).await?;
    }

    Ok(())
}

async fn monitor_single_container(
    docker: &Docker,
    container_id: &str,
    display_name: &str,
    log_dir: &str,
) -> anyhow::Result<()> {
    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(format!("{}/service_observation.log", log_dir))?;

    let mut errors_file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(format!("{}/service_errors.log", log_dir))?;

    let options = LogsOptions::<String> {
        follow: true,
        stdout: true,
        stderr: true,
        timestamps: true,
        ..Default::default()
    };

    let mut stream = docker.logs(container_id, Some(options));
    info!(
        "Observer Active for container: {} [{}]",
        display_name, container_id
    );

    while let Some(log_result) = stream.next().await {
        if let Ok(log) = log_result {
            let log_text = format!("[{}] {}", display_name, log);
            if log_text.to_uppercase().contains("ERROR") {
                writeln!(errors_file, "[ALERT] {}", log_text.trim())?;
            }
            writeln!(file, "{}", log_text.trim())?;
        }
    }

    warn!("Observer session ended for container: {}", display_name);
    Ok(())
}
