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
    await init_db()

async def shutdown(ctx):
    ctx['logger'].info("Worker shutting down...")

async def run_task(ctx, query: str, args_namespace):
    new_level = args_namespace.info.upper()
    ctx['logger'].setLevel(new_level)

    ctx['logger'].info(f"WORKER : Task Received | Query: {query} | JobID: {ctx.get('job_id')}")

    async with AsyncSessionLocal() as session:
        try:
            ctx['logger'].info(f"WORKER : Initiating configs")
            settings_bundle = await ctx['config_manager'].initialize(args_namespace)

            ctx['logger'].info(f"WORKER : Starting Service")
            service = SearchBoostService(
                **settings_bundle,
                logger=ctx['logger'],
                args=args_namespace
            )

            ctx['logger'].info(f"WORKER : Running Service")
            result = await service.run()

            db_service = PersistenceService(session, logger=ctx['logger'])
            await db_service.save_result(
                job_id=ctx.get('job_id'),
                query=query,
                final_answer=result
            )

            ctx['logger'].info(f"WORKER : Serving Results : {result}")
            ctx['logger'].info(f"Task Successful | JobID: {ctx.get('job_id')}")

            return result

        except Exception as e:
            ctx['logger'].error(f"Task Failed | JobID: {ctx.get('job_id')} | Error: {e}")
            raise e

        finally:
            ctx['logger'].setLevel(logging.INFO)

class WorkerSettings:
    functions = [run_task]
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = get_configurator().redis.arq_settings