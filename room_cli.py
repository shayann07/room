"""Small local Room command surface for existing provider sessions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from room_link import RoomLinkService


def main(argv=None):
    parser = argparse.ArgumentParser(prog="room")
    parser.add_argument("--db", default="room.sqlite3")
    parser.add_argument("command", choices=["read", "say", "claim"])
    parser.add_argument("project")
    parser.add_argument("--as", dest="participant", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--after", type=int, default=0)
    parser.add_argument("--text")
    parser.add_argument("--task")
    args = parser.parse_args(argv)
    service = RoomLinkService(Path(args.db), args.project)
    try:
        if args.command == "read":
            result = service.check_in(args.token, args.after)
        elif args.command == "say":
            result = service.post(args.token, args.text or "")
        else:
            baton = service.check_in(args.token)["baton"]
            result = service.claim(args.token, args.task or "", baton["revision"])
        print(json.dumps(result, sort_keys=True))
    finally:
        service.close()


if __name__ == "__main__":
    main()
