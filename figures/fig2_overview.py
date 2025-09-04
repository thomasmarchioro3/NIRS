import numpy as np
import matplotlib.pyplot as plt

# Use latex font
# plt.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
plt.rc('text', usetex=True)

if __name__ == "__main__":

    start_time: int = 0
    end_time: int = 5200

    attack_start_time: int = 2400
    attack_end_time: int = 2800

    attack2_start_time: int = 3600
    attack2_end_time: int = 3800

    window_start_time: int = 1400
    window_end_time: int = 3400

    flow_rate_per_second: int = 0.05

    threshold: float = 0.5

    t_idle: int = 500
    seed: int = 42

    np.random.seed(seed)

    # generate random flow timestamps
    flow_times = np.random.uniform(start_time, end_time, int((end_time - start_time) * flow_rate_per_second))
    flow_times = np.sort(flow_times)

    anomaly_scores = np.random.randn(len(flow_times))

    attack_flow_times = np.random.uniform(attack_start_time, attack_end_time, int((attack_end_time - attack_start_time) * flow_rate_per_second) * 2) 
    attack_flow_times = np.sort(attack_flow_times)

    attack_anomaly_scores = 3 + np.random.randn(len(attack_flow_times))

    attack2_flow_times = np.random.uniform(attack2_start_time, attack2_end_time, int((attack2_end_time - attack2_start_time) * flow_rate_per_second) * 2)
    attack2_flow_times = np.sort(attack2_flow_times)

    attack2_anomaly_scores = 3 + np.random.randn(len(attack2_flow_times))

    flow_times = np.append(flow_times, attack_flow_times)
    flow_times = np.append(flow_times, attack2_flow_times)
    anomaly_scores = np.append(anomaly_scores, attack_anomaly_scores)
    anomaly_scores = np.append(anomaly_scores, attack2_anomaly_scores)

    anomaly_scores = np.arctan(anomaly_scores * 0.54 / 2) * 2 / np.pi

    alert_window_start_time = attack_flow_times[0]
    alert_window_last_time = attack_flow_times[-1]
    alert_window_dead_time = attack_flow_times[-1] + t_idle

    plt.figure(figsize=(8, 3))
    plt.plot(flow_times[anomaly_scores <= threshold], anomaly_scores[anomaly_scores <= threshold], "g.", markersize=5)
    plt.plot(flow_times[anomaly_scores > threshold], anomaly_scores[anomaly_scores > threshold], "r.", markersize=5)
    # benign window
    plt.vlines(window_start_time, 0, threshold, colors="g")
    plt.vlines(window_end_time, 0, threshold, colors="g")
    plt.plot([window_start_time, window_end_time], [threshold, threshold], "g-")
    plt.fill_between([window_start_time, window_end_time], 0, threshold, color="g", alpha=0.2)
    plt.annotate("", xy=(window_start_time, 0.4), xytext=(window_end_time, 0.4), arrowprops=dict(arrowstyle="<->", color="g"))
    plt.annotate(r"$\Delta T_N$", xy=(.65 * window_start_time + .35 *window_end_time, 0.3), color="g", fontsize=14)
    
    # alert window
    plt.vlines(alert_window_start_time, threshold, 1, colors="r")
    plt.vlines(alert_window_last_time, threshold, 1, colors="r")
    plt.vlines(alert_window_dead_time, threshold, 1, colors="r", linestyles="dashed")
    plt.plot([alert_window_start_time, alert_window_last_time], [1, 1], "r-")
    plt.plot([alert_window_last_time, alert_window_dead_time], [1, 1], "r--")
    plt.fill_between([alert_window_start_time, alert_window_last_time], threshold, 1, color="r", alpha=0.2)
    
    # plot rightleft arrow from t to t+DeltaT
    plt.annotate("", xy=(alert_window_last_time, 0.8), xytext=(alert_window_dead_time, 0.8), arrowprops=dict(arrowstyle="<->", color="r"))
    plt.annotate(r"$\Delta T_A$", xy=(.6 * alert_window_last_time + .4 *alert_window_dead_time, 0.7), color="r", fontsize=14)

    plt.xlim(start_time, end_time)
    plt.ylim(0, 1.1)
    plt.yticks([threshold], [r"$\theta$"], fontsize=14)
    plt.xlabel("Time")
    plt.ylabel("Anomaly Score")
    plt.tight_layout()
    plt.savefig("figures/fig/overview.pdf")

    plt.show()
