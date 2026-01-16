import asyncio , logging
from arq.connections import RedisSettings
from searchboost_src.configurator import Configurator,get_configurator
from searchboost_src.service import SearchBoostService
from searchboost_src.logger import setup_logger

async def startup(ctx):

    ctx['logger'] = setup_logger("INFO")
    ctx['logger'].info("Worker starting up...")
    ctx['config_manager'] = get_configurator(ctx['logger'])
    ctx['logger'].info("Worker context initialized.")

async def shutdown(ctx):
    ctx['logger'].info("Worker shutting down...")

async def run_task(ctx, query: str, args_namespace):
    job_logger = logging.getLogger("searchboost.job")
    new_level = args_namespace.info.upper()
    job_logger.setLevel(new_level)

    ctx['logger'].info(f"Task Received | Query: {query} | JobID: {ctx.get('job_id')}")

    try:
        settings_bundle = await ctx['config_manager'].initialize(args_namespace)

        service = SearchBoostService(
            **settings_bundle,
            logger=job_logger,
            args=args_namespace
        )

        result = await service.run()

        job_logger.info(f"Task Successful | JobID: {ctx.get('job_id')}")
        return result

    except Exception as e:
        job_logger.error(f"Task Failed | JobID: {ctx.get('job_id')} | Error: {e}")
        raise e

    finally:
        job_logger.setLevel(logging.INFO)

class WorkerSettings:
    functions = [run_task]
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = get_configurator().redis.arq_settings