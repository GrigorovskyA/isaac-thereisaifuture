"""Release gated collection after bootstrap and before optimizer/checkpoint work."""

from collections.abc import Callable
from typing import Any


def segment_callback(record: Callable[[str, Any], None] | None) -> Any:
    """Keep the optional RL dependency lazy; use SB3's public callback API."""
    from stable_baselines3.common.callbacks import BaseCallback

    class SegmentCallback(BaseCallback):
        def _on_step(self) -> bool:
            return True

        def _on_rollout_end(self) -> None:
            boundaries = self.training_env.env_method("end_collection_segment")
            if record is not None:
                record(
                    "collection_segment_suspended",
                    {"timesteps": self.num_timesteps, "boundaries": boundaries},
                )

    return SegmentCallback()
