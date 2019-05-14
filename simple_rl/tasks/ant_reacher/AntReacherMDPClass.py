import os
import numpy as np
import random
from simple_rl.mdp.MDPClass import MDP
from mujoco_py import load_model_from_path, MjSim, MjViewer
from simple_rl.tasks.ant_reacher.AntReacherStateClass import AntReacherState


class AntReacherMDP(MDP):
    def __init__(self, dense_reward, seed, render, frame_skip):
        self.env_name = "ant_reacher"
        model_name = self.env_name + ".xml"
        p = os.path.join(os.path.expanduser("~"), "git-repos/skill-chaining/simple_rl/tasks/ant_reacher/mujoco_files/")
        self.model = load_model_from_path(p + model_name)
        self.sim = MjSim(self.model)
        self.state_dim = len(self.sim.data.qpos) + len(self.sim.data.qvel)
        self.action_dim = len(self.sim.model.actuator_ctrlrange)
        self.action_bounds = self.sim.model.actuator_ctrlrange[:, 1]

        np.random.seed(seed)
        random.seed(seed)

        self.visualize = render
        if self.visualize:
            self.viewer = MjViewer(self.sim)
        self.num_frames_skip = frame_skip

        self.goal_position = np.array([4., 4.])
        self.goal_tolerance = 0.6

        self.dense_reward = dense_reward

        self.reset()

        MDP.__init__(self, range(self.action_dim), self._transition_func, self._reward_func, self.init_state)

    def _reward_func(self, state, action):
        next_state_obs = self._step(action)
        next_state_pos = next_state_obs[:2]
        done = self.is_goal_position(next_state_pos)
        self.next_state = self._get_state(next_state_obs, done)

        if self.dense_reward:
            return -1. * self.distance_to_goal(next_state_pos)

        # Sparse reward
        return 0. if done else -1.

    def _transition_func(self, state, action):
        return self.next_state

    def execute_agent_action(self, action, option_idx=None):
        reward, next_state = super(AntReacherMDP, self).execute_agent_action(action)
        return reward, next_state

    def is_goal_state(self, state):
        if isinstance(state, AntReacherState):
            return state.is_terminal()
        position = state[:2]
        return self.is_goal_position(position)

    def _step(self, action):
        self.sim.data.ctrl[:] = action
        for _ in range(self.num_frames_skip):
            self.sim.step()
            if self.visualize:
                self.viewer.render()
        return self.get_observation()

    @staticmethod
    def _get_state(observation, done):
        """ Convert np obs array from gym into a State object. """
        obs = np.copy(observation)
        position = obs[:2]
        other_features = obs[2:]
        state = AntReacherState(position, other_features, done)
        return state

    def distance_to_goal(self, position):
        if isinstance(position, list):
            position = np.array(position)
        elif not isinstance(position, np.ndarray):
            raise TypeError(type(position))
        # position is a numpy array
        return np.linalg.norm(position - self.goal_position)

    def is_goal_position(self, position):
        return self.distance_to_goal(position) <= self.goal_tolerance

    def get_observation(self):
        return np.copy(np.concatenate((self.sim.data.qpos, self.sim.data.qvel)))

    def reset(self, training_time=True):
        # Reset controls
        self.sim.data.ctrl[:] = 0

        for i in range(len(self.sim.data.qpos)):
            self.sim.data.qpos[i] = 0.

        for i in range(len(self.sim.data.qvel)):
            self.sim.data.qvel[i] = 0.

        init_state_array = self.get_observation()
        self.init_state = self._get_state(init_state_array, done=False)
        print("Sampled init state = ", self.init_state.position)
        super(AntReacherMDP, self).reset()

    def __str__(self):
        return self.env_name