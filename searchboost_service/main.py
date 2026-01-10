import asyncio
import sys

from searchboost_src.argparser import Argsparser_Instance
from searchboost_src.service import SearchBoostService
from searchboost_src.logger import setup_logger
from searchboost_src.configurator import Configurator

async def main():

    argsparser= Argsparser_Instance()
    args = await argsparser.final_arguments()

    logger = setup_logger(args.info)
    logger.info("Starting SearchBoost Service...")
    config_manager = Configurator(logger=logger)

    try:
        logger.debug("MAIN : CONFIGURATOR INIT ")
        settings_bundle = await config_manager.initialize(args)
        logger.debug("MAIN : CONFIGURATOR INIT DONE ")
        logger.debug("MAIN : PASSING ARGS TO SERVICE ")
        service = SearchBoostService(
            **settings_bundle,
            logger=logger,
            args=args
            )
        logger.debug("MAIN : RUNNING SERVICE ")
        await service.run()
    except Exception as e:
        logger.error(f"MAIN : CRITICAL:{e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass