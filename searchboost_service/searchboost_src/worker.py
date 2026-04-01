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
        log = ctx['logger']
        self.config_manager = get_configurator(log)
        log.info("WORKER : Initialization starting...")

        # 1. Initialize Configuration with slight retry logic
        settings = None
        for attempt in range(3):
            try:
                settings = await self.config_manager.initialize(None)
                break
            except Exception as e:
                log.error(f"WORKER : Config initialization failed (attempt {attempt+1}): {e}")
                await asyncio.sleep(2 ** attempt)

        if not settings:
            log.error("WORKER : Failed to initialize configuration after retries. Manual intervention requested.")
            return

        # 2. Sovereign Pivot: Ensure models are pre-downloaded on boot
        try:
            from ollama import AsyncClient
            ai_cfg = settings['ai']
            client = AsyncClient(host=ai_cfg.base_url)

            # Pulling models sequentially to avoid overwhelming local resources
            required_models = [ai_cfg.model, "nomic-embed-text"]
            for m in required_models:
                log.info(f"WORKER : Validating model '{m}' presence...")
                try:
                    await client.pull(m)
                    log.info(f"WORKER : Model '{m}' is ready.")
                except Exception as pull_err:
                    log.warning(f"WORKER : Could not pull model '{m}': {pull_err}")
            
            log.info("WORKER : Model synchronization check complete.")
        except ImportError:
            log.warning("WORKER : 'ollama' library not found. Skipping auto-pull.")
        except Exception as e:
            log.warning(f"WORKER : Unexpected error during model synchronization: {e}")

        log.info("WORKER : Startup sequence finalized. Ready for tasks.")

    async def shutdown(self, ctx):
        ctx['logger'].info("WORKER : Worker shutting down...")

    async def run_task(self, ctx, query: str, args_namespace):
        log = ctx.get('logger', logging.getLogger("sb_worker"))
        
        log.info(f"WORKER : RAW PAYLOAD RECEIVED -> query='{query}', args_namespace={args_namespace}")

        if isinstance(args_namespace, dict):
            from argparse import Namespace
            args_namespace = Namespace(**args_namespace)

        # Ensure the service has the query available via the namespace object
        setattr(args_namespace, 'query', query)

        self.settings_bundle = await self.config_manager.initialize(args_namespace)
        await self._ensure_db_ready(self.settings_bundle['db'], log)

        log_level = getattr(args_namespace, 'info', 'INFO').upper()
        log.setLevel(log_level)

        log.info(f"WORKER : Task Received | Query: {query} | JobID: {ctx.get('job_id')}")

        async with self.db_manager.get_session() as session:
            try:
                service_keys = {k: v for k, v in self.settings_bundle.items() if k != 'warden'}

                # Extract the session identity from the job_id: "SB-SESSION-guest:uuid" → "SB-SESSION-guest"
                session_id = ctx.get('job_id', '').rsplit(':', 1)[0] or None
                log.info(f"WORKER : Session ID resolved as: '{session_id}'")

                service = SearchBoostService(
                    **service_keys,
                    logger=log,
                    args=args_namespace,
                    session_id=session_id
                )

                result = await service.run(db_session=session)

                db_service = PersistenceService(session, logger=log)
                await db_service.save_result(
                    job_id=ctx.get('job_id'),
                    query=query,
                    final_answer=result
                )

                redis_pool = ctx.get('redis')
                if redis_pool:
                    await redis_pool.setex(name=f"sb:result:{ctx.get('job_id')}", time=86400, value=result)

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