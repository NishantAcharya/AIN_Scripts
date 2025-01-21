import os
import time
def read_n_lines_no_newlines(filename, n):
  """
  Reads the first n lines from a file and removes all newline characters ('\n') from each line.

  Args:
    filename: The name of the file to read.
    n: The number of lines to read.

  Returns:
    A list of strings, where each string is a line from the file without newline characters.
  """

  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file.readlines()[:n]]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  

def read_n_lines_from_line(filename, start_line, n):
  """
  Reads n lines from a given line in a file.

  Args:
    filename: The name of the file to read.
    start_line: The line number to start reading from (1-indexed).
    n: The number of lines to read.

  Returns:
    A list of strings, where each string is a line from the file.
  """
  try:
    with open(filename, 'r') as file:
      f_lines = file.readlines()
      lines = [line.strip() for line in f_lines]
      if start_line < 1 or start_line > len(lines):
        raise ValueError(f"Invalid start line: {start_line}")
      end_line = min(start_line + n - 1, len(lines))
      return lines[start_line - 1:end_line]
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  except ValueError as e:
    print(e)
    return []
  

  
def count_lines_in_file(filename):
  """
  Counts the total number of lines in a given file.

  Args:
    filename: The name of the file to count lines in.

  Returns:
    The total number of lines in the file.
  """
  try:
    with open(filename, 'r') as file:
      return sum(1 for _ in file)  # Efficiently count lines using generator expression
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return 0

def main(buffer_size, producer_file, consumer_file, inpt_file):
    print('Starting producer...')
  
    consumed = 0
    produced = 0
    exists_consumer = False

    #Checking if the main IP file exists
    if not os.path.exists(inpt_file):
        raise Exception(f"Error: File '{inpt_file}' not found.")

    if not os.path.exists(producer_file):
        print(f"Warning: File '{producer_file}' not found. Making producer file.")
        fd = open(producer_file, 'w')
        fd.close()
        exists_producer = True

    inpts = count_lines_in_file(inpt_file)

    current_line = 1
    while produced < inpts:
        if not os.path.exists(consumer_file):
          print(f"Warning: File '{consumer_file}' not found. Producer to assumer 0 consumed")
        else:
            consumed = count_lines_in_file(consumer_file)
            print(f'Consumed: {consumed}')
        
        produced = count_lines_in_file(producer_file)
        print(f'Produced: {produced} -- Inpts: {inpts}')

        if produced - consumed >= buffer_size:
           print('Buffer full...')
           time.sleep(2)
           continue
        
        to_read = abs(buffer_size - (produced - consumed))
        print(f'To read: {to_read}')
        
        print('Producing...')
        lines = read_n_lines_from_line(inpt_file, current_line, to_read)
        current_line += to_read
        with open(producer_file, 'a') as file:
            for line in lines:
                file.write(line + '\n')

main(1000,'producer.txt','consumer.txt','test_inpts.txt')
    



  
