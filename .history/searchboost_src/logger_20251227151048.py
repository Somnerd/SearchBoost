    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        encoding='utf-8',
        format='%(levelname)s - %(message)s ',
        handlers=[
            logging.FileHandler("searchboost.log", mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
            ]
        )
