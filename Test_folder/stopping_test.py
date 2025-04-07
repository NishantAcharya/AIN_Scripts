import sys

#Testing taking sys arguments
if len(sys.argv) < 3:
    print("Please provide at least two arguments.")
    sys.exit(1)

arg1 = sys.argv[1]
arg2 = sys.argv[2]

print(f"First argument: {arg1}")
print(f"Second argument: {arg2}")
