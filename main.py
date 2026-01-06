import asyncio

from searchboost_src.argparser import parse_arguments, final_arguments
from searchboost_src.service import SearchBoostService
from searchboost_src.logger import setup_logger

async def main():

    logger = await setup_logger()
    args = await final_arguments()

    try:
        service = SearchBoostService(logger=logger,args=args)
        await service.initialize()
        await service.run()
    except Exception as e:
        logger.error(f"MAIN : CRITICAL:{e}")

if __name__ == "__main__":
    asyncio.run(main())