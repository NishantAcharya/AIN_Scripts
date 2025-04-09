import multiprocessing
import sys
import random

def worker_function(data):
    """
    This function will be executed by each process.
    It receives a single input argument.
    """
    # Get the current process name
    process_name = multiprocessing.current_process().name

    # Process the data
    result = data * 2  # Example processing

    print(f"Process {process_name} is processing data: {data}")
    print(result)

    return result

if __name__ == '__main__':
    # Prepare input data
    input_data = [1, 2, 3, 4, 5]

    # Create a Pool with 4 processes
    with multiprocessing.Pool(processes=4) as pool:
        # Use pool.map to apply the worker function to each input
        pool.map(worker_function, input_data)