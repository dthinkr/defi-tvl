import json

# Path to the JSON file
json_file_path = 'data/llama/arbitrum-bridge.json'

# Function to print the structure of the JSON file
def print_json_structure(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        print('Type of top-level element:', type(data))
        if isinstance(data, dict):
            print('Keys:', data.keys())
        elif isinstance(data, list) and len(data) > 0:
            print('Type of elements in list:', type(data[0]))
            if isinstance(data[0], dict):
                print('Keys of first element:', data[0].keys())

# Call the function
print_json_structure(json_file_path)
