from __future__ import annotations

import os


def main() -> int:
    """
    Small helper entrypoint for debugging/manual seeding.

    In this project, seeding is normally performed by the worker via the
    `scrape_new_data` RabbitMQ task.
    """
    dsn = os.environ["DATABASE_URL"]
    seed = os.environ.get("SEED_JSON", "/data/applicant_data.json")

    print("This project seeds via worker 'scrape_new_data' task.")
    print(f"DATABASE_URL={dsn}")
    print(f"SEED_JSON={seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
