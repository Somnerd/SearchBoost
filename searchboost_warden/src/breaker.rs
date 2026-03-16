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

use failsafe::{Config, failure_policy, backoff, StateMachine};
use std::time::Duration;

// This makes your Relay code much cleaner to read
pub type WardenBreaker = StateMachine<
    failsafe::failure_policy::ConsecutiveFailures<std::iter::Repeat<Duration>>, 
    ()
>;

pub fn create_breaker(threshold: u32, retry_secs: u64) -> WardenBreaker {
    // 1. Set the "Cooldown" period (20 seconds)
    let retry_backoff = backoff::constant(Duration::from_secs(retry_secs));
    
    // 2. Set the "Strike" limit (5 failures)
    let policy = failure_policy::consecutive_failures(threshold, retry_backoff);
    
    // 3. Build the State Machine
    Config::new()
        .failure_policy(policy)
        .build()
}