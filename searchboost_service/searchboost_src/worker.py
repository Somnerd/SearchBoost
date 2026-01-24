import asyncio, logging
from arq.connections import RedisSettings
from searchboost_src.configurator import get_configurator
from searchboost_src.service import SearchBoostService
from searchboost_src.logger import setup_logger
from searchboost_src.database import DatabaseManager
from searchboost_src.service import PersistenceService

class Worker:
    def __init__(self):
        self.db_manager = None
        self.settings_bundle = None

    async def _ensure_db_ready(self, db_settings, log):
        if self.db_manager is None:
            log.info("WORKER: Configuring Database Manager for the first time...")
            self.db_manager = DatabaseManager(db_settings)
            await self.db_manager.init_db()
            log.info("WORKER: Database connection and schema verified.")
        else:
            log.info("WORKER: Database Manager already configured.")

    async def startup(self, ctx):
        ctx['logger'] = setup_logger("INFO")
        ctx['logger'].info("WORKER : Worker starting up...")
        self.config_manager = get_configurator(ctx['logger'])
        ctx['logger'].info("""WORKER : Configurator initialized.
                            Ready to process tasks.""")
        ctx['logger'].debug(f"WORKER : config_manager set : {self.config_manager}")

    async def shutdown(self, ctx):
        ctx['logger'].info("WORKER : Worker shutting down...")

    async def run_task(self, ctx, query: str, args_namespace):
        log = ctx['logger']

        self.settings_bundle = await self.config_manager.initialize(args_namespace)
        await self._ensure_db_ready(self.settings_bundle['db'], log)

        new_level = args_namespace.info.upper()
        log.setLevel(new_level)

        log.info(f"WORKER : Task Received | Query: {query} | JobID: {ctx.get('job_id')}")

        async with self.db_manager.get_session() as session:
            try:
                service = SearchBoostService(
                    **self.settings_bundle,
                    logger=log,
                    args=args_namespace
                )

                result = await service.run()

                db_service = PersistenceService(session, logger=log)
                await db_service.save_result(
                    job_id=ctx.get('job_id'),
                    query=query,
                    final_answer=result
                )

                return result
            except Exception as e:
                log.error(f"Task Failed | Error: {e}")
                raise e
            finally:
                log.setLevel(logging.INFO)

worker_logic = Worker()

class WorkerSettings:
    functions = [worker_logic.run_task]
    on_startup = worker_logic.startup
    on_shutdown = worker_logic.shutdown

    redis_settings = get_configurator().redis.arq_settings