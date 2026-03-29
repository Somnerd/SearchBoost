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


use bollard::Docker;
use bollard::container::{LogOutput, LogsOptions, ListContainersOptions};
use futures_util::stream::StreamExt;
use std::io::Write;
use tracing::{info, error, warn};
use std::collections::HashMap;
use crate::configurator::ObserverSettings;

pub async fn start_log_observer(settings: ObserverSettings) -> anyhow::Result<()> {
    info!("Starting Warden Observer Service");
    let docker = Docker::connect_with_local_defaults()?;

    std::fs::create_dir_all(&settings.log_path).unwrap_or_else(|e| warn!("Could not create log dir: {}", e));
    
    let log_path = settings.log_path.clone();

    if let Some(label) = settings.container_label {
        info!("Warden: Label-based discovery active for: {}", label);
        let mut filters = HashMap::new();
        filters.insert("label".to_string(), vec![label.clone()]);
        
        let options = ListContainersOptions {
            all: true,
            filters,
            ..Default::default()
        };

        let containers = docker.list_containers(Some(options)).await?;
        info!("Warden: Discovered {} containers matching label", containers.len());

        for container in containers {
            if let Some(id) = container.id {
                let docker_clone = docker.clone();
                let path_clone = log_path.clone();
                let name = container.names.unwrap_or_default().get(0).cloned().unwrap_or_else(|| id.clone());
                
                tokio::spawn(async move {
                    if let Err(e) = monitor_single_container(&docker_clone, &id, &name, &path_clone).await {
                        error!("Warden: Failed to monitor container {}: {}", id, e);
                    }
                });
            }
        }
    } else {
        info!("Warden: Fixed-name observation active for: {}", settings.container_name);
        monitor_single_container(&docker, &settings.container_name, &settings.container_name, &log_path).await?;
    }

    Ok(())
}

async fn monitor_single_container(docker: &Docker, container_id: &str, display_name: &str, log_dir: &str) -> anyhow::Result<()> {
    let mut file = std::fs::OpenOptions::new()
        .create(true).append(true).open(format!("{}/service_observation.log", log_dir))?;

    let mut errors_file = std::fs::OpenOptions::new()
        .create(true).append(true).open(format!("{}/service_errors.log", log_dir))?;

    let options = LogsOptions::<String> {
        follow: true, stdout: true, stderr: true, timestamps: true, ..Default::default()
    };

    let mut stream = docker.logs(container_id, Some(options));
    info!("Observer Active for container: {} [{}]", display_name, container_id);

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