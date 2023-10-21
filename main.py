import gdown

url = 'https://drive.google.com/uc?id=1omR46R5IdHNd3QcYrOvaFlXG3hpA1cEq'  # Replace with your file's ID
output = 'data/tvl/db/filename.extension'  # Replace with your desired output file path and name

gdown.download(url, output, quiet=False)