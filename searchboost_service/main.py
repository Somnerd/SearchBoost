import asyncio
import sys

from arq import create_pool
from arq.connections import RedisSettings

from searchboost_src.configurator import Configurator,get_configurator
from searchboost_src.argparser import Argsparser_Instance
from searchboost_src.logger import setup_logger


async def main():

    args = await Argsparser_Instance().final_arguments()

    logger = setup_logger(args.info)
    logger.info("Starting SearchBoost Service...")

    try:
        logger.debug("MAIN : RUNNING SERVICE ")

        config = get_configurator(logger=logger)

        bundle = await config.initialize(args)
        #logger.debug(f"""MAIN : Settings Bundle :
        #AI Settings: {bundle['ai']}
        #Search Settings: {bundle['search']}
        #Redis Settings: {bundle['redis']}
        #DB Settings: {bundle['db']}""")

        logger.debug("MAIN : Creating Redis Connection Pool...")
        logger.debug(f"MAIN : Redis Settings : {bundle['redis'].arq_settings}")
        redis_pool = await create_pool(bundle['redis'].arq_settings)

        logger.debug("MAIN : Submitting research job to Redis...")
        job = await redis_pool.enqueue_job('Worker.run_task', args.query, args)
        logger.info(f"Research job submitted! ID: {job.job_id}")

        try:
            logger.info("MAIN : Waiting for job to complete...")
            final_answer = await job.result(timeout=60, poll_delay=5)

            separator = "=" * 50
            logger.info(f"""{separator}
            MAIN : RESPONSE : \n---{final_answer}")
            {separator}""")
        except Exception as e:
            logger.error(f"MAIN: Error retrieving job result : {e}")

    except Exception as e:
        logger.error(f"MAIN : CRITICAL:{e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("""
        Disconnected from job tracking.
        The worker will still continue in the background.
        """)
        pass