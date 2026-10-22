"""Exercise RecurrentPPO and checkpoint loading over the project observation and action spaces."""

import json
import tempfile
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.env_checker import check_env

from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.episodes import ACTION_NVEC


class StackSmokeEnv(gym.Env):
    """Synthetic compatibility check, not an Isaac simulator or a speed test.

    It only borrows the real space shapes: 1837 observations and MultiDiscrete([5, 5, 4]).
    """

    observation_space = gym.spaces.Box(-1, 1, shape=(OBSERVATION_SIZE,), dtype=np.float32)
    action_space = gym.spaces.MultiDiscrete(list(ACTION_NVEC))

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.steps = 0
        return np.zeros(OBSERVATION_SIZE, dtype=np.float32), {}

    def step(self, action):
        self.steps += 1
        return (
            np.zeros(OBSERVATION_SIZE, dtype=np.float32),
            float(np.all(action == 0)),
            False,
            self.steps >= 8,
            {},
        )


def main():
    torch.set_num_threads(1)
    env = StackSmokeEnv()
    try:
        check_env(env, warn=True)
        model = RecurrentPPO(
            "MlpLstmPolicy",
            env,
            n_steps=8,
            batch_size=8,
            n_epochs=1,
            policy_kwargs={"lstm_hidden_size": 16, "net_arch": [16]},
            seed=42,
            device="cpu",
            verbose=0,
        )
        model.learn(total_timesteps=16)
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "stack-smoke.zip"
            model.save(checkpoint)
            loaded = RecurrentPPO.load(checkpoint, env=env, device="cpu")
            obs, _ = env.reset(seed=42)
            action, _ = loaded.predict(obs, episode_start=np.array([True]), deterministic=True)
            assert env.action_space.contains(action), f"Invalid predicted action: {action}"
            assert loaded.action_space == env.action_space
            assert loaded.observation_space.shape == (OBSERVATION_SIZE,)
        print(
            json.dumps(
                {
                    "rl_stack_smoke": "passed",
                    "timesteps": 16,
                    "device": "cpu",
                    "torch": torch.__version__,
                    "cuda_available": torch.cuda.is_available(),
                    "observation_size": OBSERVATION_SIZE,
                    "action_nvec": list(ACTION_NVEC),
                    "isaac_integration_tested": False,
                },
                indent=2,
            )
        )
    finally:
        env.close()


if __name__ == "__main__":
    main()
