import pandas as pd
from stqdm import stqdm
from collections import defaultdict
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt

class ChordDiagramData:
    def __init__(self, parquet_file_path):
        self.data = pd.read_parquet(parquet_file_path)
        self.unique_dates = self.data['aggregated_date'].unique()
    
    # def get_color_for_type(self, type_name):
    #     if type_name not in self.color_map:
    #         # Generate a new color if not already present
    #         color_palette = sns.color_palette("husl", 100)  # Using Seaborn's larger palette
    #         self.color_map[type_name] = to_hex(color_palette[len(self.color_map) % 100])
    #     return self.color_map[type_name]

    def get_data_for_day(self, day):
        # Filter the data for the given day
        data_day = self.data[self.data['aggregated_date'] == day]

        # Get unique list of types
        types = data_day['type'].unique()

        # Create an empty DataFrame to store the co-occurrence matrix
        matrix = pd.DataFrame(
            data=0, 
            index=types, 
            columns=types,
            dtype=float
        )

        # Pre-calculate the tokens and their total values for each type
        type_tokens = defaultdict(lambda: defaultdict(int))

        for _, row in stqdm(data_day.iterrows(), total=data_day.shape[0], desc="Preprocessing"):
            type_tokens[row['type']][row['token_name']] += row['total_value_usd']

        # For each pair of types
        for i, type_1 in stqdm(enumerate(types), total=len(types), desc="Processing types"):
            for j, type_2 in enumerate(types[i:]):  # Start from i to avoid duplicate calculations
                # Find the shared tokens
                shared_tokens = set(type_tokens[type_1].keys()) & set(type_tokens[type_2].keys())
                
                # For each shared token, add up the USD value and store it in the matrix
                for token in shared_tokens:
                    value = min(type_tokens[type_1][token], type_tokens[type_2][token])
                    matrix.loc[type_1, type_2] += value
                    matrix.loc[type_2, type_1] += value

        # Normalize the matrix
        total_value = matrix.values.sum()
        normalized_matrix = matrix / total_value

        # Convert the matrix into a list of lists for the chord diagram format
        matrix_values = normalized_matrix.values.tolist()

        # Generate a evenly distributed list of colors and convert them to hexadecimal format
        colors = [to_hex(plt.cm.tab20(i/len(types))) for i in range(len(types))]

        # Preparing the final data structure for chord diagram
        chord_data = {
            "matrix": matrix_values,
            "names": list(types),
            "colors": colors  # Color list adjusted to the number of types
        }

        return chord_data