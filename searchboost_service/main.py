# -*- coding: utf-8 -*-
# SearchBoost: AI-Powered Semantic Search & Reliability Engine
# Copyright (C) 2026 Nikolaos Alexandrakis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------
# COMMERCIAL USE NOTICE:
# For licensing outside the scope of AGPLv3, contact: nikolasalexandrakis.work@gmail.com
# ---------------------------------------------------------------------

import asyncio
import httpx
import time

from searchboost_src.configurator import Configurator,get_configurator
from searchboost_src.argparser import Argsparser_Instance
from searchboost_src.logger import setup_logger
from searchboost_src.fallback_handler import perform_direct_search



async def submit_to_warden(logger, query, args, warden_url):
    payload = {
        "query" : query,
        "session_id" : "SB-SESSION-"+args.username, # The Warden uses this as the 'shard/identity' key
        "options": vars(args)
    }

    async with httpx.AsyncClient() as client:
        logger.info(f"MAIN : Routing request through Relay ({warden_url})...")
        response = await client.post(warden_url, json=payload,timeout=3.0)

        if response.status_code == 200:
            data = response.json()
            return data['id']
        elif response.status_code == 503:
            exception_message = "Warden is OPEN (Warden is protecting Redis)"
            raise Exception(exception_message)
        else:
            exception_message = f"Warden return error {response.status_code}: {response.text}"
            raise Exception(exception_message)

# Fallback and Response tracking is now managed by separate specialized logic

async def handle_response(logger, job_id, warden_url_base, timeout=120):
    """
    Phase 2: Polling the Warden's HTTP endpoint for results instead of Redis.
    Uses exponential backoff for polling.
    """
    start_time = time.time()
    poll_delay = 1.0 # Start with 1s
    max_delay = 8.0
    results_url = f"{warden_url_base}/results/{job_id}"

    logger.info(f"MAIN : Tracking job {job_id} via Warden HTTP...")

    async with httpx.AsyncClient() as client:
        while True:
            if time.time() - start_time > timeout:
                logger.error(f"MAIN : Tracking TIMEOUT reached for job {job_id}.")
                break

            try:
                response = await client.get(results_url, timeout=5.0)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "complete":
                        final_answer = data.get("result")
                        separator = "=" * 50
                        logger.info(f"""
{separator}
MAIN : RESPONSE RECEIVED :
{final_answer}
{separator}
                        """)
                        return
                elif response.status_code == 202:
                    # Accepted/Pending
                    pass
                else:
                    logger.debug(f"MAIN : Warden returned {response.status_code} during polling.")

            except Exception as e:
                logger.warning(f"MAIN : Polling error: {e}")

            await asyncio.sleep(poll_delay)
            # Exponential backoff
            poll_delay = min(poll_delay * 1.5, max_delay)

async def main():
    job_id = None
    args = await Argsparser_Instance().final_arguments()
    logger = setup_logger(args.info)

    logger.info("Starting SearchBoost Service...")

    try:
        logger.debug("MAIN : RUNNING SERVICE ")

        config = get_configurator(logger=logger)
        bundle = await config.initialize(args)

        # Configurator handles environment-aware routing (sb_warden vs 127.0.0.1)
        warden_url_base = bundle['warden'].base_url
        enqueue_url = f"{warden_url_base}/enqueue"

        try:
            job_id = await submit_to_warden(logger, args.query, args, enqueue_url)
            logger.info(f"MAIN : Successfully enqueued via Warden : ID : {job_id}")

            if job_id:
                await handle_response(logger, job_id, warden_url_base)

        except Exception as error:
            logger.error(f"MAIN : Warden Access Failed with Error : {error}")

            try:
                await perform_direct_search(logger, bundle, args)
            except Exception as fallback_error:
                logger.error(f"""
                MAIN :
                                    CRITICAL FAILURE - UNABLE TO ACCESS REDIS
                                    ERROR : {fallback_error}
                                    """)
                return None

    except Exception as init_error:
        logger.error(f"MAIN : Initialization Failed : {init_error}")
        return None

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("""
        Disconnected from job tracking.
        The worker will still continue in the background.
        """)
        pass