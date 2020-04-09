import argparse
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path

sns.set(color_codes=True)
sns.set_style("white")

def load_data(file_name):
	with open(file_name, 'rb') as f:
		data = pickle.load(f)
	return data

def get_all_cur_data(run_dir, start, end):
	all_data = []
	for i in range(start, end+1):
		scores = load_data(run_dir + '/run_{}_all_data'.format(i) + '/per_episode_scores.pkl')
		all_data.append(scores)
	return np.array(all_data)

def get_all_old_data(old_run_dir, start, end):
	all_old_runs = []
	for i in range(start, end+1):
		scores = load_data(old_run_dir + '/sc_pretrained_False_training_scores_{}.pkl'.format(i))
		all_old_runs.append(scores)
	return np.array(all_old_runs)

def get_multi_cur_data(run_dirs, start, end):
	multi_cur_data = {}
	for run_dir in run_dirs:
		cur_data = get_all_cur_data(run_dir, start, end)
		args = load_data(run_dir + '/run_1_all_data/args.pkl')
		multi_cur_data['all_cur_data_nu_{}'.format(args.nu)] = {'cur_data' : cur_data, 'args' : args}
	return multi_cur_data

def plot_multi_avg_learning_curves(plot_dir, all_data, mdp_env_name, one_v_one=False, best_color_idx=None):
	columns = ['time_steps', 'run_data']
	colors = sns.color_palette("deep")
	i=0

	for data_name, data in all_data.items():		
		if 'cur' in data_name:	# Multiple current tests
			for cur_name, cur_dict in data.items():
				# Export current data dict
				args = cur_dict['args']
				cur_data = cur_dict['cur_data']
				
				# Plotting variables
				num_eps = len(cur_data[0])
				time_steps = np.linspace(1, num_eps, num=num_eps)
				label = 'DSC w/ Opt/Pes: nu={}'.format(args.nu)

				# Append all runs
				df_data = pd.DataFrame(columns=columns)
				for run in cur_data:
					df = pd.DataFrame(np.column_stack((time_steps, run)), columns=columns)
					df_data = df_data.append(df)

				if one_v_one:
					sns.lineplot(x='time_steps', y='run_data', data=df_data, label=label, ci=None, color=colors[best_color_idx])
				else:
					sns.lineplot(x='time_steps', y='run_data', data=df_data, label=label, ci=None, color=colors[i])
					i+=1

		else:	# Old tests
			# Plotting variables
			num_eps = len(data[0])
			time_steps = np.linspace(1, num_eps, num=num_eps)
			label = 'DSC (old)'

			# Append all runs
			df_data = pd.DataFrame(columns=columns)
			for run in data:
				df = pd.DataFrame(np.column_stack((time_steps, run)), columns=columns)
				df_data = df_data.append(df)

			if one_v_one:
				sns.lineplot(x='time_steps', y='run_data', data=df_data, label=label, ci=None, color=colors[-1])
			else:
				sns.lineplot(x='time_steps', y='run_data', data=df_data, label=label, ci=None, color=colors[i])
				i+=1

	# Plotting features
	plt.title('Average Reward: {}'.format(mdp_env_name))
	plt.ylabel('Reward')
	plt.xlabel('Episodes')
	plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

	# Save plots
	if one_v_one:
		plt.savefig("{}/one_v_one_learning_curves.png".format(plot_dir), bbox_inches='tight')
		plt.close()
		print("Plot {}/one_v_one_learning_curves.png saved!".format(plot_dir))
	else:
		plt.savefig("{}/multi_learning_curves.png".format(plot_dir), bbox_inches='tight')
		plt.close()
		print("Plot {}/multi_learning_curves.png saved!".format(plot_dir))

def main(args):
	# Create plotting dir (if not created)
	path = 'plots'
	Path(path).mkdir(exist_ok=True)

	# Old comparative data
	all_old_data = get_all_old_data(args.old_run_dir, 1, 5)

	# Multi hyperparameter data
	multi_cur_data = get_multi_cur_data(args.run_dirs, 1, 5)

	# Plot hyperparameter search runs
	all_data = {'multi_cur_data' : multi_cur_data}
	plot_multi_avg_learning_curves(plot_dir=path,
								   all_data=all_data,
								   mdp_env_name=args.mdp_env_name)

	# Plot 1v1 methods
	# best_cur_data = get_multi_cur_data([args.run_dirs[1]], 1, 5)
	# all_data = {'best_cur_data' : best_cur_data, 'all_old_data' : all_old_data}
	# plot_multi_avg_learning_curves(plot_dir=path,
	# 								 all_data=all_data,
	# 								 mdp_env_name=args.mdp_env_name,
	# 								 one_v_one=True,
	# 								 best_color_idx=1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--run_dirs', nargs='*', type=str, default="")
	parser.add_argument('--old_run_dir', type=str, default="")
	parser.add_argument('--mdp_env_name', type=str, default="")
	args = parser.parse_args()

	main(args)