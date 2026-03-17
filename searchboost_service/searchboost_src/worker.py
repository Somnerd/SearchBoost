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
        ctx['logger'].info("WORKER : Worker starting up...")
        self.config_manager = get_configurator(ctx['logger'])
        ctx['logger'].info("""WORKER : Configurator initialized.
                            Ready to process tasks.""")
        ctx['logger'].debug(f"WORKER : config_manager set : {self.config_manager}")

    async def shutdown(self, ctx):
        ctx['logger'].info("WORKER : Worker shutting down...")

    async def run_task(self, ctx, query: str, args_namespace):
        log = ctx.get('logger', logging.getLogger("sb_worker"))

        if isinstance(args_namespace, dict):
            from argparse import Namespace
            args_namespace = Namespace(**args_namespace)

        self.settings_bundle = await self.config_manager.initialize(args_namespace)
        await self._ensure_db_ready(self.settings_bundle['db'], log)

        log_level = getattr(args_namespace, 'info', 'INFO').upper()
        log.setLevel(log_level)

        log.info(f"WORKER : Task Received | Query: {query} | JobID: {ctx.get('job_id')}")

        async with self.db_manager.get_session() as session:
            try:
                service_keys = {k: v for k, v in self.settings_bundle.items() if k != 'warden'}
                service = SearchBoostService(
                    **service_keys,
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