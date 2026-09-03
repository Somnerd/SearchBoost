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

use failsafe::{backoff, failure_policy, Config, StateMachine};
use std::time::Duration;

// This makes your Relay code much cleaner to read
pub type WardenBreaker =
    StateMachine<failsafe::failure_policy::ConsecutiveFailures<std::iter::Repeat<Duration>>, ()>;

pub fn create_breaker(threshold: u32, retry_secs: u64) -> WardenBreaker {
    // 1. Set the "Cooldown" period (20 seconds)
    let retry_backoff = backoff::constant(Duration::from_secs(retry_secs));

    // 2. Set the "Strike" limit (5 failures)
    let policy = failure_policy::consecutive_failures(threshold, retry_backoff);

    // 3. Build the State Machine
    Config::new().failure_policy(policy).build()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_breaker_initial_state_permitted() {
        let breaker = create_breaker(5, 20);
        assert!(
            breaker.is_call_permitted(),
            "Circuit breaker should initially be closed (calls permitted)"
        );
    }

    #[test]
    fn test_breaker_trips_at_threshold() {
        let breaker = create_breaker(3, 20);

        // 1st failure: still permitted
        breaker.on_error();
        assert!(
            breaker.is_call_permitted(),
            "Circuit breaker should permit calls after 1 error (threshold 3)"
        );

        // 2nd failure: still permitted
        breaker.on_error();
        assert!(
            breaker.is_call_permitted(),
            "Circuit breaker should permit calls after 2 errors (threshold 3)"
        );

        // 3rd failure: threshold reached, should trip open
        breaker.on_error();
        assert!(
            !breaker.is_call_permitted(),
            "Circuit breaker should be open after reaching failure threshold"
        );
    }

    #[test]
    fn test_breaker_success_resets_consecutive_failures() {
        let breaker = create_breaker(3, 20);

        // 2 failures
        breaker.on_error();
        breaker.on_error();
        assert!(breaker.is_call_permitted());

        // Intermittent success resets the consecutive failure counter
        breaker.on_success();
        assert!(breaker.is_call_permitted());

        // Now 2 more failures should not trip the breaker since consecutive count was reset
        breaker.on_error();
        breaker.on_error();
        assert!(
            breaker.is_call_permitted(),
            "Failure counter should have been reset by on_success"
        );

        // 3rd consecutive failure after reset trips it
        breaker.on_error();
        assert!(
            !breaker.is_call_permitted(),
            "Circuit breaker should trip after 3 consecutive failures"
        );
    }

    #[test]
    fn test_breaker_cooldown_and_recovery() {
        // Create breaker with 0 second cooldown for immediate recovery testing
        let breaker = create_breaker(2, 0);

        breaker.on_error();
        breaker.on_error();

        // With retry_secs = 0, cooldown is 0 duration so next call probe should be permitted (half-open)
        assert!(
            breaker.is_call_permitted(),
            "Breaker should transition to half-open when cooldown expires"
        );

        // Success on probe closes the breaker
        breaker.on_success();
        assert!(
            breaker.is_call_permitted(),
            "Breaker should be fully closed after successful probe"
        );
    }
}
