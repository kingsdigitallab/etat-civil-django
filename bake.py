#!/usr/bin/env python

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Helper script for docker compose actions")
    parser.add_argument(
        "--dry", action="store_true", help="print the command rather than running it"
    )
    parser.add_argument(
        "--stack",
        type=str,
        default="local",
        help="stack where to run the command (local, production)",
    )
    parser.add_argument("-s", "--service", type=str,
                        help="service to apply the command to")
    parser.add_argument(
        "command",
        type=str,
        choices=[
            "up",
            "stop",
            "destroy",
            "restart",
            "shell",
            "run",
            "manage",
            "test",
            "coverage",
        ],
        help="command for the stack/service",
    )
    parser.add_argument(
        "options",
        type=str,
        nargs=argparse.REMAINDER,
        help="remaining arguments to be passed to the command",
    )

    args = parser.parse_args()

    compose_command = f"docker-compose -f {args.stack}.yml"

    dry = args.dry
    service = args.service if args.service else ""
    command = args.command
    options = " ".join(args.options)

    if command in ["up", "stop", "restart", "run"]:
        compose_command = f"{compose_command} {command} {service}"
    elif command == "destroy":
        compose_command = f"{compose_command} down --volumes --rmi all"
    elif command == "shell":
        if not service:
            print("! the shell command needs a service option")
            sys.exit(1)
        compose_command = f"{compose_command} run {service} '/bin/bash'"
    elif command == "manage":
        compose_command = f"{compose_command} run django python manage.py"
    elif command == "test":
        compose_command = f"{compose_command} run django pytest"
    elif command == "coverage":
        compose_command = f"{compose_command} run django coverage run -m pytest"
    else:
        print(f"! {command} is an invalid command")

    compose_command = f"{compose_command} {options}"

    print(f"{compose_command}")
    if not dry:
        os.system(compose_command)


if __name__ == "__main__":
    main()
