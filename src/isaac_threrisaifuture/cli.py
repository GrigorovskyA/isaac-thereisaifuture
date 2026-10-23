"""Runtime diagnostics and explicitly opted-in post-death lifecycle; never launches the game."""

import argparse
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

from .observation import BridgeError, ProtocolError
from .observer_client import ObservationClient, ObserverConfig
from .training import PURE_CONFIG


def doctor() -> dict[str, object]:
    packages = (
        "gymnasium",
        "numpy",
        "pydantic",
        "PyYAML",
        "torch",
        "stable-baselines3",
        "sb3-contrib",
        "tensorboard",
    )
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "project": "isaac-threrisaifuture",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
        "game_integration": "observer_implemented_runtime_unverified",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    observe = commands.add_parser("observe", help="Listen for the read-only Lua observer")
    observe.add_argument("--host", default="127.0.0.1")
    observe.add_argument("--port", type=int, default=9528)
    observe.add_argument("--accept-timeout", type=float, default=10.0)
    observe.add_argument("--handshake-timeout", type=float, default=3.0)
    observe.add_argument("--message-timeout", type=float, default=3.0)
    observe.add_argument("--samples", type=int, default=50)
    observe.add_argument("--reconnects", type=int, default=0)
    observe.add_argument(
        "--restart-after-death",
        action="store_true",
        help="Opt in to 3 post-death restart attempts / 10 minutes per game instance",
    )
    observe.add_argument(
        "--confirmed-save-slot",
        type=int,
        choices=[2],
        help="Operator confirmation after manually selecting file 2; not slot detection",
    )
    approve = commands.add_parser(
        "approve-training", help="Write the bounded live-loop approval for save file 2"
    )
    approve.add_argument("--game-directory", type=Path)
    approve.add_argument("--hours", type=float, default=8.0)
    restarts = approve.add_mutually_exclusive_group()
    restarts.add_argument("--max-restarts", type=int, default=1000)
    restarts.add_argument(
        "--unlimited-restarts",
        action="store_true",
        help="Write max_restarts 0 (no count limit; the lease and fault caps still apply)",
    )
    approve.add_argument("--confirmed-save-slot", type=int, choices=[2], required=True)
    live = commands.add_parser("live", help="Live loop: random actions or training on file 2")
    live.add_argument("--mode", choices=["random", "train"], default="random")
    live.add_argument(
        "--steps",
        type=int,
        help="Agent steps / training timesteps (default: 3000 random, unbounded train)",
    )
    live.add_argument(
        "--minutes",
        type=float,
        help="Wall-time cap (default: 30 random; train uses the config budget, at most 8 h)",
    )
    live.add_argument("--max-faults", type=int, default=20)
    live.add_argument("--seed", type=int)
    live.add_argument(
        "--config",
        type=Path,
        default=PURE_CONFIG,
        help="Training config (train mode); default configs/training-pure-v4.yaml",
    )
    live.add_argument("--resume", action="store_true")
    live.add_argument("--out-dir", type=Path, default=Path("runs/live"))
    live.add_argument("--connection-timeout", type=float, default=300.0)
    live.add_argument("--launch", action="store_true", help="Preflight, then start isaac-ng.exe")
    live.add_argument("--game-directory", type=Path)
    live.add_argument("--confirmed-save-slot", type=int, choices=[2], required=True)
    evaluate = commands.add_parser(
        "eval-live", help="Attach-only frozen checkpoint or random policy pilot on file 2"
    )
    evaluate.add_argument("--policy", choices=["checkpoint", "random"], required=True)
    evaluate.add_argument("--checkpoint", type=Path, help="Exact checkpoint directory")
    evaluate.add_argument("--expected-config-hash", help="Required with --policy checkpoint")
    evaluate.add_argument("--expected-training-seed", type=int)
    evaluate.add_argument("--policy-seed", type=int, default=0)
    evaluate.add_argument("--steps", type=int, default=2000, help="Decision cap")
    evaluate.add_argument("--minutes", type=float, default=6.0, help="Absolute wall-time cap")
    evaluate.add_argument("--accept-timeout", type=float, default=300.0)
    evaluate.add_argument("--max-faults", type=int, default=0)
    evaluate.add_argument(
        "--operator-assistance",
        choices=["assisted", "unassisted", "unknown"],
        default="unknown",
        help="Declared for the whole session; physical input is not detected",
    )
    evaluate.add_argument("--out-dir", type=Path, default=Path("runs/eval-live"))
    evaluate.add_argument("--confirmed-save-slot", type=int, choices=[2], required=True)
    args = parser.parse_args()
    if args.command == "doctor":
        print(json.dumps(doctor(), indent=2, ensure_ascii=False))
        return
    if args.command == "eval-live":
        _eval_live_command(args)
        return
    if args.command in ("approve-training", "live"):
        _live_command(args)
        return
    try:
        if args.samples < 1 or args.reconnects < 0:
            raise ValueError("Samples must be positive; reconnects must be nonnegative")
        if args.restart_after_death and args.confirmed_save_slot != 2:
            raise ValueError("Restart mode requires --confirmed-save-slot 2 after manual selection")
        config = ObserverConfig(
            args.host,
            args.port,
            args.accept_timeout,
            args.handshake_timeout,
            args.message_timeout,
            restart_after_death=args.restart_after_death,
        )
        with ObservationClient(config) as client:
            print(json.dumps({"event": "listening", "address": client.address}), flush=True)
            remaining = args.samples
            retries = args.reconnects
            while remaining:
                try:
                    print(client.accept().model_dump_json(), flush=True)
                    while remaining:
                        print(client.receive().model_dump_json(), flush=True)
                        remaining -= 1
                except ProtocolError:
                    raise
                except BridgeError as exc:
                    if retries == 0:
                        raise
                    retries -= 1
                    print(
                        f"Observation interrupted: {exc}; awaiting a new session", file=sys.stderr
                    )
    except KeyboardInterrupt:
        print("Observation stopped; sockets closed.", file=sys.stderr)
    except (BridgeError, ValueError) as exc:
        print(f"Observation error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _live_command(args: argparse.Namespace) -> None:
    from .live import LiveRunOptions, run_live, write_training_approval

    try:
        if args.command == "approve-training":
            from .launcher import discover_game

            directory = args.game_directory or discover_game()
            path = write_training_approval(
                directory,
                hours=args.hours,
                max_restarts=0 if args.unlimited_restarts else args.max_restarts,
            )
            print(f"Training approval written: {path}")
            print("Fully restart Isaac to load it (the mod reads it once per game launch).")
            return
        directory = None
        if args.launch:
            from .launcher import discover_game

            directory = args.game_directory or discover_game()
        logs = run_live(
            LiveRunOptions(
                mode=args.mode,
                out_dir=args.out_dir,
                connection_timeout=args.connection_timeout,
                steps=args.steps or (3000 if args.mode == "random" else 10**9),
                minutes=args.minutes or (30.0 if args.mode == "random" else 480.0),
                max_faults=args.max_faults,
                seed=args.seed,
                config_path=args.config,
                resume=args.resume,
                launch_directory=directory,
            )
        )
        print(f"Live run finished; logs in {logs}")
    except KeyboardInterrupt:
        print("Live run stopped; input released, game left running.", file=sys.stderr)
    except (BridgeError, OSError, ValueError) as exc:
        print(f"Live run error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _eval_live_command(args: argparse.Namespace) -> None:
    from .checkpoints import CheckpointError
    from .live_evaluation import FrozenLiveOptions, load_policy, run_frozen_live, summary_line

    try:
        options = FrozenLiveOptions(
            policy=args.policy,
            out_dir=args.out_dir,
            checkpoint=args.checkpoint,
            expected_config_hash=args.expected_config_hash,
            expected_training_seed=args.expected_training_seed,
            policy_seed=args.policy_seed,
            steps=args.steps,
            minutes=args.minutes,
            accept_timeout=args.accept_timeout,
            max_faults=args.max_faults,
            operator_assistance=args.operator_assistance,
        )
        policy = load_policy(options)
    except (CheckpointError, ValueError) as exc:
        print(f"Evaluation not started: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        result = run_frozen_live(options, policy)
    except (BridgeError, OSError, ValueError) as exc:
        print(f"Evaluation error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(summary_line(result))
    if result.exit_code:
        raise SystemExit(result.exit_code)


if __name__ == "__main__":
    main()
