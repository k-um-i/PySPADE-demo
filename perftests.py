from sys import argv
import time
import random
import tracemalloc
import SPADE
import user_client
import analyst_client


# Function for running comprehensive SPADE tests based on the provided arguments
def run_test(num_users, vector_size, host, port):
    print(f"\nRunning test: {num_users} users, vector size {vector_size}.")
    print("")

    # Step 1. Generate random test data
    start = time.time()  # Track time
    tracemalloc.start()  # Track memory
    print("Generating data...")
    messages = [
        [random.randint(1, 10) for _ in range(vector_size)] for _ in range(num_users)
    ]
    print("Finished.")
    print("")

    # Compute memory usage and setup time and print it out
    memory_used = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    setup_time = time.time() - start
    print(f"Time taken for dummy data setup: {setup_time:.5f} seconds.")
    print(f"Memory used: {memory_used / 10**6:.2f} MB.")

    # Step 2. Register users.
    users = []
    start = time.time()  # Track time
    tracemalloc.start()  # Track memory
    for _ in range(num_users):
        user = user_client.SPADEUser(host, port)  # Create user instance
        user.register()  # Register user on the SPADE server
        users.append(user)  # Keep track of registered users

    # Compute memory usage and setup time and print it out
    memory_used = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    registration_time = time.time() - start
    print(f"Time taken for registration: {registration_time:.5f} seconds.")
    print(f"Memory used: {memory_used / 10**6:.2f} MB.")

    # Step 3. Encrypt user data and store it
    ciphertexts = []
    tracemalloc.start()  # Track memory
    start = time.time()  # Track time
    for i in range(num_users):
        user = users[i]
        q, g, mpk = user.get_public_parameters(vector_size)  # Retrieve public params
        cipher = SPADE.SPADE(vector_size, q, g, mpk)  # Initialize SPADE cipher

        # Encrypt the data vector using the users private key
        h, c = cipher.encrypt(messages[i], users[i].private_key)
        encrypted_data = {"h": h, "c": c}
        ciphertexts.append((h, c))

        # Create a request to store encrypted data on the server
        request = {
            "action": "store_data",
            "id": user.user_id,
            "encrypted_data": encrypted_data,
            "n": vector_size,
        }
        user.send_request(request)  # Send the request

    # Compute memory usage and setup time and print it out
    memory_used = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    encryption_time = time.time() - start
    print(f"Time taken for encryption: {encryption_time:.5f} seconds.")
    print(f"Memory used: {memory_used / 10**6:.2f} MB.")

    # Step 4. Derive decryption keys
    value = 3  # Search value for decryption key
    decryption_keys = []
    encrypted_data_list = []
    analyst = analyst_client.SPADEAnalyst(host, port)  # Initialize analyst client
    tracemalloc.start()  # Track memory
    start = time.time()  # Track time

    # Iterate through each user
    for i in range(num_users):
        id = i + 1

        # Derive a decryption key for the users data
        dk, encrypted_data, n = analyst.derive_key(user_id=id, v=value)
        decryption_keys.append(dk)  # Store derived decryption keys
        encrypted_data_list.append(encrypted_data)  # Store encrypted data

    # Compute memory usage and setup time and print it out
    memory_used = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    keyderivation_time = time.time() - start
    print(f"Time taken for key derivation: {keyderivation_time:.5f} seconds.")
    print(f"Memory used: {memory_used / 10**6:.2f} MB.")

    # Step 5. Decrypt the data
    decrypted_results = []
    tracemalloc.start()  # Track memory
    start = time.time()  # Track time

    # Iterate through each user
    for i in range(num_users):
        q, g, mpk = analyst.get_public_parameters(n)  # Get public params
        dk = decryption_keys[i]  # Fetch the derived decryption key for the user
        user_data = encrypted_data_list[i]

        # Extract the encrypted data and helper data
        encrypted_data = user_data[0]
        h, c = encrypted_data["h"], encrypted_data["c"]

        # Initialize the SPADE cipher and decrypt the data
        cipher = SPADE.SPADE(vector_size, q, g, mpk)
        result = cipher.decrypt(dk, c, h, value)
        decrypted_results.append(result)  # Store decrypted data

    # Compute memory usage and setup time and print it out
    memory_used = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    decryption_time = time.time() - start
    print(f"Time taken for decryption: {decryption_time:.5f} seconds.")
    print(f"Memory used: {memory_used / 10**6:.2f} MB.")


# Main function that handles the running of the tests
def main():
    if len(argv) != 3:  # Ensure that only host and port are provided
        print("Invalid amount of arguments.")
    else:
        host = argv[1]  # Server host address
        port = int(argv[2])  # Server port

        # Prompt to ensure the user is connecting to a fresh server instance.
        input(
            "\nPlease ensure that you are connecting to a fresh server instance. (Enter to continue)"
        )

        # Run test with 10 users and vector size 1000
        run_test(10, 1000, host, port)

        # Prompt for the user to restart the server for a fresh instance.
        input(
            "\nPlease restart your server to create a fresh instance before continuing. (Enter to continue)"
        )

        # Run test with 100 users and vector size 10 000
        run_test(100, 10000, host, port)


if __name__ == "__main__":
    main()
