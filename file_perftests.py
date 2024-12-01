import user_client
import analyst_client
import time

# import tracemalloc
from sys import argv
from os import listdir
from os.path import isfile, join


# Function for testing user client encryption of all hypnogram files.
def user_tests_hypnogram(data_folder, host, port):
    print("")

    # Fetch all files in the data folder that are not already encrypted
    files = [
        f
        for f in listdir(data_folder)
        if isfile(join(data_folder, f)) and not f.endswith(".encrypted")
    ]

    # Print out summary of operations
    print(f"Encrypting a total of {len(files)} files.")
    print("Operations per file:")
    print("     - Initialize user")
    print("     - Register user")
    print("     - Encrypt file")

    start = time.time()  # Measure operation time
    # tracemalloc.start() # Uncomment to track memory usage (Ruins performance????)

    # Iterate through each data file
    for file in files:
        user = user_client.SPADEUser(host, port)  # Initialize SPADE user
        user.register()  # Register user with the SPADE server
        user.encrypt_hypnogram(data_folder + file)  # Encrypt the file

    # Calculate and print out time taken for operations
    encryption_time = time.time() - start
    print(
        f"\nTime taken for initialization, registration and encryption for {len(files)} files: {encryption_time:.5f} seconds."
    )

    ### Uncomment for memory usage tracking
    # memory_used = tracemalloc.get_traced_memory()[1]
    # tracemalloc.stop()
    # print(f"Memory used: {memory_used / 10**6:.2f} MB.\n")

    # Return the amount files that were processed
    return len(files)


# Function for testing user client encryption of all dna files.
def user_tests_dna(data_folder, host, port):
    print("")

    # Fetch all files in the data folder that are not already encrypted
    files = [
        f
        for f in listdir(data_folder)
        if isfile(join(data_folder, f)) and not f.endswith(".encrypted")
    ]

    # Print out summary of operations
    print(f"Encrypting a total of {len(files)} files.")
    print("Operations per file:")
    print("     - Initialize user")
    print("     - Register user")
    print("     - Encrypt file")

    start = time.time()  # Measure operation time
    # tracemalloc.start() # Uncomment to track memory usage (Ruins performance????)

    # Iterate through each data file
    for file in files:
        user = user_client.SPADEUser(host, port)  # Initialize SPADE user
        user.register()  # Register user with the SPADE server
        user.encrypt_genome(data_folder + file)  # Encrypt the file

    # Calculate and print out time taken for operations
    encryption_time = time.time() - start
    print(
        f"\nTime taken for initialization, registration and encryption for {len(files)} files: {encryption_time:.5f} seconds."
    )

    ### Uncomment for memory usage tracking
    # memory_used = tracemalloc.get_traced_memory()[1]
    # tracemalloc.stop()
    # print(f"Memory used: {memory_used / 10**6:.2f} MB.\n")

    # Return the amount of files that were processed
    return len(files)


# Function for testing decryption of analyst client
def analyst_tests(host, port, n_of_users):
    print("")

    # Initialize analyst client
    analyst = analyst_client.SPADEAnalyst(host, port)

    # Print out summary of operations
    print(f"Decrypting a total of {n_of_users} files.")
    print("Operations per file:")
    print("     - Get data and derive key")
    print("     - Decrypt data using received key")

    start = time.time()  # Track operation time

    # Iterate through each registered user on the server
    for i in range(n_of_users):
        # Get encrypted data and derived key from the SPADE server
        data, dk, n = analyst_client.get_encrypted_data(analyst, i + 1, 3)
        # Decrypt the encrypted data
        result = analyst_client.decrypt(analyst, data, dk, n, 3)

    # Calculate and print out time taken for operations
    decryption_time = time.time() - start
    print(
        f"\nTime taken for key derivation and decryption of {n_of_users} files: {decryption_time:.5f} seconds."
    )


# Main function that handles running of the tests
def main():
    if len(argv) == 3:
        host = argv[1]  # Provided server host address
        port = int(argv[2])  # Provided server port
        n_of_users = 0  # Initialize the number of processed users/files

        # Perform user tests for hypnogram data
        n_of_users += user_tests_hypnogram("datasets/hypnogram/", host, port)

        # Perform user tests for dna data
        n_of_users += user_tests_dna("datasets/dna/", host, port)

        # Perform analyst tests for all previously processed data
        analyst_tests(host, port, n_of_users)
    else:
        # Print out error if incorrect arguments are provided
        print("Invalid arguments.")


if __name__ == "__main__":
    main()
