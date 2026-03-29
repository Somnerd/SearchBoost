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
use bollard::container::LogOutput;
use bollard::container::LogsOptions;
use futures_util::stream::StreamExt;
use std::io::Write;
use tracing::{info, error};

pub async fn start_log_observer(container_name: &str, log_dir: &str) -> anyhow::Result<()> {
    info!("Starting observer");
    let docker = Docker::connect_with_local_defaults()?;
    //info!("AFTER DOCKER");

    info!("BEFORE LOG FILE OPERATION");
    std::fs::create_dir_all(log_dir).unwrap_or_else(|e| tracing::warn!("Could not create log dir: {}", e));
    let mut file = std::fs::OpenOptions::new()
        .create(true).append(true).open(format!("{}/service_observation.log", log_dir))?;
    info!("AFTER LOG FILE OPERATION");


    let mut errors_file = std::fs::OpenOptions::new()
        .create(true).append(true).open(format!("{}/service_errors.log", log_dir))?;
    info!("AFTER ERROR FILE OPERATION");

    let options = LogsOptions::<String> {
        follow: true, stdout: true, stderr: true, timestamps: true, ..Default::default()
    };
    info!("AFTER IDK FILE OPERATION");

    let mut stream = docker.logs(container_name, Some(options));
    info!("Observer Active for: {}", container_name);

    while let Some(log_result) = stream.next().await {
        if let Ok(log) = log_result {
            let log_text = format!("{}", log);
            if log_text.to_uppercase().contains("ERROR") {
                writeln!(errors_file, "[ALERT] {}", log_text.trim())?;
            }
            writeln!(file, "{}", log_text.trim())?;
        }
    }
    Ok(())
}