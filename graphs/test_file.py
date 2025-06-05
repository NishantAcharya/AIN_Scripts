import numpy as np
import matplotlib.pyplot as plt

def log_cdf(values, title="Log CDF", log_base=10, show_stats=True, save_path=None):
    """Create log-scale CDF plot with y-axis 0-100% and x-axis as log values."""
    vals = np.array(values)
    pos_vals = vals[vals > 0]
    if len(pos_vals) == 0:
        raise ValueError("No positive values for log transformation")
    
    sorted_vals = np.sort(pos_vals)
    percentiles = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals) * 100
    log_vals = np.log(sorted_vals) / np.log(log_base) if log_base != np.e else np.log(sorted_vals)
    
    plt.figure(figsize=(8, 5))
    plt.plot(log_vals, percentiles, 'b-', linewidth=2)
    plt.xlabel(f"Log{log_base if log_base != np.e else ''} Values")
    plt.ylabel("Cumulative Percentage (%)")
    plt.title(title)
    plt.ylim(0, 100)  # Fixed: should be 100, not 1
    plt.grid(True, alpha=0.3)
    
    if show_stats:
        plt.axvline(np.mean(log_vals), color='r', linestyle='--', alpha=0.7, 
                   label=f'Mean: {np.mean(log_vals):.2f}')
        plt.axvline(np.median(log_vals), color='g', linestyle='--', alpha=0.7, 
                   label=f'Median: {np.median(log_vals):.2f}')
        plt.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()

def log_cdf_multi(value_lists, labels=None, title="Log CDF Comparison", log_base=10, save_path=None):
    """Compare multiple datasets on log CDF plot."""
    if labels is None:
        labels = [f"Data {i+1}" for i in range(len(value_lists))]
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(value_lists)))
    
    for vals, label, color in zip(value_lists, labels, colors):
        pos_vals = np.array(vals)[np.array(vals) > 0]
        if len(pos_vals) == 0: 
            continue
        
        sorted_vals = np.sort(pos_vals)
        percentiles = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals) * 100
        log_vals = np.log(sorted_vals) / np.log(log_base) if log_base != np.e else np.log(sorted_vals)
        plt.plot(log_vals, percentiles, color=color, linewidth=2, label=label)
    
    plt.xlabel(f"Log{log_base if log_base != np.e else ''} Values")
    plt.ylabel("Cumulative Percentage (%)")
    plt.title(title)
    plt.ylim(0, 100)  # Fixed: should be 100, not 1
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    plt.show()

# Example usage:
if __name__ == "__main__":
    # Generate some sample data
    np.random.seed(42)
    data1 = np.random.lognormal(2, 1, 1000)
    data2 = np.random.lognormal(1.5, 0.8, 1000)
    
    # Single plot
    log_cdf(data1, title="Sample Log-Normal Data CDF")
    
    # Multi-dataset comparison
    log_cdf_multi([data1, data2], labels=["Dataset A", "Dataset B"], 
                  title="Comparison of Two Log-Normal Distributions")