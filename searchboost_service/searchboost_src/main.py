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

    #config = get_configurator(logger=logger)

    try:
        logger.debug("MAIN : RUNNING SERVICE ")

        config = get_configurator(logger=logger)

        bundle = await config.initialize(args)
        redis_pool = await create_pool(bundle['redis'].arq_settings)

        job = await redis_pool.enqueue_job('run_task', args.query, args)
        logger.info(f"Research job submitted! ID: {job.job_id}")


        try:
            status = await job.status()

            final_answer = await job.result()

            separator = "=" * 50
            logger.info(f"""{separator}
            MAIN : RESPONSE : \n---{final_answer}")
            {separator}""")
        except Exception as e:
            logger.error(f"MAIN: Error retrieving job result : {e}")
        #await asyncio.sleep(1)

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