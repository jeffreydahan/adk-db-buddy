import argparse
import sys
import db_deploy

def main():
    """
    This script deploys the back end services for the selected database.
    """
    parser = argparse.ArgumentParser(description="Deploy back end services.")
    parser.add_argument(
        "db_type",
        choices=["postgres", "sqlserver", "mysql", "bq"],
        help="The type of database to deploy. Choose from: postgres, sqlserver, mysql, bq",
    )
    args = parser.parse_args()

    if args.db_type == "postgres":
        print("Deploying Postgres back end...")
        db_deploy.main(args.db_type)
    else:
        print(f"Deployment for {args.db_type} is not yet implemented.")
        sys.exit(1)

if __name__ == "__main__":
    main()
