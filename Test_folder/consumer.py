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
  

def read_all_lines_no_newlines(filename):
  """
  Reads all lines from a file and removes all newline characters ('\n') from each line.

  Args:
    filename: The name of the file to read.

  Returns:
    A list of strings, where each string is a line from the file without newline characters.
  """
  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []


def main(buffer_size, producer_file, consumer_file, inpt_file):
  #The script will go through the  producer file and read the inputs there
  #Wait (This part will signify us checking the status of the items)
  #If the status is completed, then download, which will be another sleep here
  ## And then add to consumer, else keep looping
  # Stop when the size of the consumer file is the same as the inpts file

  print('Starting consumer...')

  consumed = 0
  exists_producer = False

  #Checking if the main IP file exists
  if not os.path.exists(inpt_file):
      raise Exception(f"Error: File '{inpt_file}' not found.")
  
  #Checking if the producer file exists
  if not os.path.exists(producer_file):
      print(f"Warning: File '{producer_file}' not found. Producer to assumer 0 consumed")
  else:
      exists_producer = True

  #Checking if the consumer file exists
  if not os.path.exists(consumer_file):
      print(f"Warning: File '{consumer_file}' not found. Making consumer file.")
      fd = open(consumer_file, 'w')
      fd.close()
      exists_consumer = True

  inpts = count_lines_in_file(inpt_file)

  while consumed < inpts:
      #Reading the producer file
      if os.path.exists(producer_file):
        p_lines = read_all_lines_no_newlines(producer_file)
      else:
          print(f"Warning: File '{producer_file}' not found. Producer to assumed 0 consumed")
          p_lines = []
      c_lines = read_all_lines_no_newlines(consumer_file)

      #All elements that have been produced but not consumed yet
      f_lines = [x for x in p_lines if x not in set(c_lines)]

      if len(f_lines) == 0:
          print(f"Nothing to consume, Sleeping")
          time.sleep(3) #Sleep for a longer time than producer
          continue
      
      for item in f_lines:
          print(f"Consuming {item}")
          with open(consumer_file, 'a') as file:
              file.write(f"{item}\n")
          consumed += 1
          if consumed == inpts:
              break
          
main(1000, "producer.txt", "consumer.txt", "test_inpts.txt")
         