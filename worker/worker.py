import logging
import os
import time


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "info").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll_interval = int(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "2"))

    logging.info("ZFlow worker started")

    while True:
        # TODO: fetch next task from queue and run pipeline stages.
        logging.debug("Worker idle")
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
