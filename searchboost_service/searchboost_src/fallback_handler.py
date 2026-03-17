# -*- coding: utf-8 -*-
# SearchBoost: Fallback Module for Direct Redis Communication
# Copyright (C) 2026 Nikolaos Alexandrakis

import asyncio
import time
from arq import create_pool
from arq.jobs import Job, JobStatus

async def perform_direct_search(logger, bundle, args, timeout=120):
    """
    Handles the entire search lifecycle directly via Redis when the Warden is unavailable.
    Encapsulates all arq/redis dependencies to keep the main orchestrator clean.
    """

    logger.warning("FALLBACK: Initializing direct connection to Redis...")
    redis_pool = await create_pool(bundle['redis'].arq_settings)

    try:
        logger.debug("FALLBACK: Enqueuing research job...")
        job = await redis_pool.enqueue_job('Worker.run_task', args.query, args)
        job_id = job.job_id
        logger.info(f"FALLBACK: Job submitted directly! ID: {job_id}")

        start_time = time.time()
        last_status = None

        logger.info(f"FALLBACK: Tracking job {job_id} via Redis...")

        not_found_count: int = 0
        while True:
            if time.time() - start_time > timeout:
                logger.error(f"FALLBACK: Tracking TIMEOUT reached for job {job_id}.")
                return None

            status = await job.status()

            if status != last_status:
                match status:
                    case JobStatus.queued:
                        logger.info(f"FALLBACK: Job {job_id} is in the QUEUE...")

                    case JobStatus.in_progress:
                        logger.info(f"FALLBACK: Job {job_id} is currently IN PROGRESS...")

                    case JobStatus.deferred:
                        logger.info(f"FALLBACK: Job {job_id} is DEFERRED.")

                    case JobStatus.not_found:
                        not_found_count += 1
                        if not_found_count > 5:
                            logger.error(f"FALLBACK: Job {job_id} was lost (NOT FOUND threshold reached).")
                            return None
                        logger.warning(f"FALLBACK: Job {job_id} NOT FOUND (waiting propagation)...")

                    case JobStatus.complete:
                        logger.info(f"FALLBACK: Job {job_id} reports COMPLETION.")
                        break

                    case _:
                        logger.debug(f"FALLBACK: Job {job_id} is in unknown state: {status}")

                last_status = status

            await asyncio.sleep(2)

        # Fetch result
        logger.info("FALLBACK: Fetching final answer from Redis...")
        final_answer = await job.result(timeout=5)
        separator = "=" * 50
        logger.info(f"""
            {separator}
            FALLBACK : RESPONSE RECEIVED :
                {final_answer}
            {separator}
        """)
        return final_answer

    except Exception as e:
        logger.error(f"FALLBACK: Critical failure during direct search: {e}")
        return None
    finally:
        await redis_pool.close()
        logger.debug("FALLBACK: Redis connection pool closed.")
