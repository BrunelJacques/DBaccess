import json

# Your dictionary
data = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "Data Analysis", "Machine Learning"]
}

# Save to a JSON file
with open("data.json", "w") as f:
    json.dump(data, f, indent=4)  # indent4 makes it pretty human-readable.
    #json.dumps to convert the dictionary to a JSON string (not save to file),
    text = json.dumps(data, indent=4)

# Read from the JSON file
with open("data.json", "r") as f:
    loaded_data = json.load(f)

print(loaded_data)
