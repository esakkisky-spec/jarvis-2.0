import kagglehub
from kagglehub import KaggleDatasetAdapter

def load_medicine_data():
    # Set the path to the file you'd like to load
    file_path = "Medicine_Details.csv"

    # Load the latest version
    print("Downloading/Loading dataset...")
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "singhnavjot2062001/11000-medicine-details",
        file_path,
        pandas_kwargs={"compression": "zip"}
    )
    
    return df

if __name__ == "__main__":
    df = load_medicine_data()
    print("First 5 records:\n", df.head())
