"""Exercise RecurrentPPO and checkpoint loading over the project observation and action spaces.

Always on the CPU, whatever device the training config names, so it runs on any machine. When
torch can use CUDA, one more model is trained on the GPU, saved and loaded for prediction on the
CPU, as frozen evaluation does with a checkpoint of the cuda learner. The learner runs the auxiliary
self-prediction phase after each update, and its saved state is loaded back. A second learner with
the E3B bonus (off in the shipped contract) pays one bonus, trains its inverse dynamics and reloads
its state.
"""

import json
import tempfile
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.episodes import ACTION_NVEC
from isaac_threrisaifuture.learner import PureRecurrentPPO
from isaac_threrisaifuture.normalization import ContinuousVecNormalize, check_continuous_only
from isaac_threrisaifuture.policy import StructuredFeatures, policy_kwargs


class StackSmokeEnv(gym.Env):
    """Synthetic compatibility check, not an Isaac simulator or a speed test.

    It only borrows the real space shapes: 2038 observations and MultiDiscrete([5, 5, 4]).
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


def pure_model(venv, device, **extra):
    """The pure profile's learner: rollout-level advantages, two minibatches per epoch and a short
    auxiliary phase over the replay."""
    return PureRecurrentPPO(
        "MlpLstmPolicy",
        venv,
        n_steps=8,
        batch_size=4,
        n_epochs=1,
        target_kl=0.03,
        auxiliary="spr_reward_done_v1",
        aux_steps=2,
        aux_batch=8,
        policy_kwargs=policy_kwargs(16, 16, net_arch=[16]),
        seed=42,
        device=device,
        verbose=0,
        **extra,
    )


def cuda_to_cpu(folder):
    """Train one rollout on the GPU, then load the saved model on the CPU and predict."""
    venv = ContinuousVecNormalize(DummyVecEnv([StackSmokeEnv]), gamma=0.998)
    try:
        model = pure_model(venv, "cuda")
        assert next(model.policy.parameters()).is_cuda, "the model is not on the GPU"
        model.learn(total_timesteps=8)
        model.save(Path(folder) / "cuda.zip")
    finally:
        venv.close()
    loaded = RecurrentPPO.load(Path(folder) / "cuda.zip", device="cpu")
    assert not next(loaded.policy.parameters()).is_cuda
    obs = np.zeros((1, OBSERVATION_SIZE), dtype=np.float32)
    action, _ = loaded.predict(obs, episode_start=np.array([True]), deterministic=True)
    assert loaded.action_space.contains(action[0]), f"Invalid predicted action: {action}"


def e3b_leg(folder):
    """E3B learner on the CPU: one paid bonus, the inverse-dynamics phase, a state round trip."""
    venv = ContinuousVecNormalize(DummyVecEnv([StackSmokeEnv]), gamma=0.998)
    try:
        model = pure_model(venv, "cpu", intrinsic="e3b_count_v1", e3b_embed_dim=16,
                           e3b_idm_steps=2, e3b_idm_batch=8)  # fmt: skip
        learner = model.e3b_learner
        obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        learner.start_episode(obs)
        paid = learner.reward(obs, 1)
        assert 0.0 <= paid <= model.e3b_beta, f"bonus out of range: {paid}"
        model.learn(total_timesteps=16)
        loss = float(model.logger.name_to_value["train/e3b_idm_loss"])
        assert np.isfinite(loss), "the E3B phase did not run"
        learner.save(Path(folder) / "e3b.pt")
        resumed = pure_model(venv, "cpu", intrinsic="e3b_count_v1", e3b_embed_dim=16)
        resumed.e3b_learner.load(Path(folder) / "e3b.pt")
        saved = learner.embedding.state_dict()
        for name, tensor in resumed.e3b_learner.embedding.state_dict().items():
            assert torch.equal(tensor, saved[name]), f"E3B state differs: {name}"
        return loss
    finally:
        venv.close()


def main():
    torch.set_num_threads(1)
    env = StackSmokeEnv()
    # The pure profile's stack: continuous-only normalizer, structured features and the
    # rollout-normalizing learner, on an explicit CPU device.
    venv = ContinuousVecNormalize(DummyVecEnv([StackSmokeEnv]), gamma=0.998)
    cuda = "skipped (CUDA not available)"
    try:
        check_env(env, warn=True)
        model = pure_model(venv, "cpu")
        assert isinstance(model.policy.features_extractor, StructuredFeatures)
        model.learn(total_timesteps=16)
        logged = model.logger.name_to_value
        assert np.isfinite(logged["train/aux_latent_loss"]), "the auxiliary phase did not run"
        assert np.isfinite(logged["train/aux_approx_kl"])
        assert len(model.auxiliary_learner.replay) == 16
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "stack-smoke.zip"
            model.save(checkpoint)
            model.auxiliary_learner.save(Path(folder) / "auxiliary.pt")
            resumed = PureRecurrentPPO.load(checkpoint, env=venv, device="cpu")
            resumed.auxiliary_learner.load(Path(folder) / "auxiliary.pt")
            saved = model.auxiliary_learner.model.state_dict()
            for name, tensor in resumed.auxiliary_learner.model.state_dict().items():
                assert torch.equal(tensor, saved[name]), f"auxiliary state differs: {name}"
            venv.save(str(Path(folder) / "vecnormalize.pkl"))
            normalizer = VecNormalize.load(
                str(Path(folder) / "vecnormalize.pkl"), DummyVecEnv([StackSmokeEnv])
            )
            check_continuous_only(normalizer)
            normalizer.training = False
            loaded = RecurrentPPO.load(checkpoint, env=env, device="cpu")
            obs, _ = env.reset(seed=42)
            obs = normalizer.normalize_obs(obs[None, :])[0]
            action, _ = loaded.predict(obs, episode_start=np.array([True]), deterministic=True)
            assert env.action_space.contains(action), f"Invalid predicted action: {action}"
            assert loaded.action_space == env.action_space
            assert loaded.observation_space.shape == (OBSERVATION_SIZE,)
            if torch.cuda.is_available():
                cuda_to_cpu(folder)
                cuda = "passed"
            e3b_loss = e3b_leg(folder)
        print(
            json.dumps(
                {
                    "rl_stack_smoke": "passed",
                    "timesteps": 16,
                    "device": "cpu",
                    "torch": torch.__version__,
                    "cuda_available": torch.cuda.is_available(),
                    "torch_cuda_build": torch.version.cuda,
                    "cuda_to_cpu_checkpoint": cuda,
                    "auxiliary": model.auxiliary,
                    "aux_approx_kl": float(logged["train/aux_approx_kl"]),
                    "e3b_idm_loss": e3b_loss,
                    "observation_size": OBSERVATION_SIZE,
                    "action_nvec": list(ACTION_NVEC),
                    "isaac_integration_tested": False,
                },
                indent=2,
            )
        )
    finally:
        env.close()
        venv.close()


if __name__ == "__main__":
    main()
