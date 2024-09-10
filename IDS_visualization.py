import time
import random
import asciichartpy
from colorama import Fore, Back, Style, init
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

init(autoreset=True)  # Initialize colorama

class IDSVisualizer:
    def __init__(self):
        self.normal_traffic = []
        self.attack_traffic = []
        self.alerts = []
        self.max_data_points = 60

    def update_data(self, normal, attack, alert):
        self.normal_traffic.append(normal)
        self.attack_traffic.append(attack)
        self.alerts.append(alert)
        
        if len(self.normal_traffic) > self.max_data_points:
            self.normal_traffic.pop(0)
            self.attack_traffic.pop(0)
            self.alerts.pop(0)

    def print_ascii_chart(self):
        print(Fore.GREEN + "Normal Traffic:")
        print(asciichartpy.plot(self.normal_traffic, {'height': 10}))
        print(Fore.RED + "Attack Traffic:")
        print(asciichartpy.plot(self.attack_traffic, {'height': 10}))

    def print_alerts(self):
        print(Fore.YELLOW + "Alerts:")
        for alert in self.alerts[-10:]:  # Show last 10 alerts
            print(f"- {alert}")

    def setup_matplotlib(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.line1, = self.ax1.plot([], [], 'g-', label='Normal Traffic')
        self.line2, = self.ax1.plot([], [], 'r-', label='Attack Traffic')
        self.ax1.set_ylim(0, 100)
        self.ax1.legend()
        self.ax1.set_title('Network Traffic')

        self.ax2.set_ylim(0, 20)
        self.ax2.set_title('Alerts')
        self.alert_scatter, = self.ax2.plot([], [], 'yo', label='Alerts')

    def update_plot(self, frame):
        self.line1.set_data(range(len(self.normal_traffic)), self.normal_traffic)
        self.line2.set_data(range(len(self.attack_traffic)), self.attack_traffic)
        self.ax1.relim()
        self.ax1.autoscale_view()

        alert_x = [i for i, alert in enumerate(self.alerts) if alert]
        alert_y = [1] * len(alert_x)
        self.alert_scatter.set_data(alert_x, alert_y)
        self.ax2.relim()
        self.ax2.autoscale_view()

        return self.line1, self.line2, self.alert_scatter

def simulate_ids_for_presentation(visualizer):
    for _ in range(100):  # Simulate 100 time steps
        normal = random.randint(10, 50)
        attack = random.randint(0, 20)
        alert = random.random() < 0.1  # 10% chance of alert

        visualizer.update_data(normal, attack, alert)
        
        # Clear the console (works on Unix-like systems)
        print("\033c", end="")
        
        print(Fore.CYAN + "=== IDS Real-time Monitor ===")
        visualizer.print_ascii_chart()
        visualizer.print_alerts()
        
        time.sleep(0.5)  # Update every 0.5 seconds

if __name__ == "__main__":
    visualizer = IDSVisualizer()
    
    # Set up matplotlib animation
    visualizer.setup_matplotlib()
    ani = FuncAnimation(visualizer.fig, visualizer.update_plot, frames=100, interval=500, blit=True)
    plt.show(block=False)

    # Run the terminal-based visualization
    simulate_ids_for_presentation(visualizer)