from sys import argv
import socket
import struct
import pickle
import SPADE

# Dict mapping numeric values to dinucleotides to allow
# the program to convert received integers to dinucleotides
DINUCLEOTIDE_VALUE_TABLE = {
    1: "AA",
    2: "AC",
    3: "AG",
    4: "AT",
    5: "CC",
    6: "CA",
    7: "CG",
    8: "CT",
    9: "GG",
    10: "GA",
    11: "GC",
    12: "GT",
    13: "TT",
    14: "TA",
    15: "TC",
    16: "TG",
}


# Class for SPADE analyst client
class SPADEAnalyst:
    def __init__(self, host, port):
        self.host = host  # Server host
        self.port = port  # Server port

    # Function for sending requests to the SPADE server
    def send_request(self, request):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((self.host, self.port))  # Connect to server
            serialized_data = pickle.dumps(request)  # Serialize request data
            client.sendall(struct.pack("!I", len(serialized_data)))  # Send data length
            client.sendall(serialized_data)  # Send the actual request data

            # Receive data length header
            raw_length = client.recv(4)
            if not raw_length:
                raise EOFError("No data length header received.")
            data_length = struct.unpack("!I", raw_length)[0]

            # Receive actual response in chunks
            data = b""
            while len(data) < data_length:
                packet = client.recv(16384)
                if not packet:
                    raise EOFError("Connection closed before all data received.")
                data += packet

            response = pickle.loads(data)  # Deserialize response
            return response

    # Function for requesting a derived key from the SPADE server
    def derive_key(self, user_id, v):
        request = {"action": "derive_key", "user_id": user_id, "v": v}
        response = self.send_request(request)  # Send request and receive response

        # Check that server did not run into an error
        if response.get("error") is not None:
            print("Error: User not found.")
            return 0, 0, 0

        # Return derived key, encrypted data and data length
        return response.get("dk"), response.get("encrypted_data"), response.get("n")

    # Function for requesting public parameters for data length n
    def get_public_parameters(self, n):
        request = {"action": "get_public_parameters", "n": n}  # Form request
        response = self.send_request(request)  # Send request and receive response

        # Return public parameters from response
        return response.get("q"), response.get("g"), response.get("mpk")


# CLI interface for hypnogram data analysis
def hypnogram_interface(client):
    print("Type 'help' for commands.")
    while True:
        cmd = input("\n> ").strip().lower()
        print("")

        if cmd == "back":
            break
        elif cmd == "help":
            print("Available commands:")
            print(
                "     > analyze     | Analyze encrypted hypnogram data. Asks for user id and value."
            )
            print(
                "     > back        | Returns to the previous interface where you can choose data type to analyze."
            )
            print("     > help        | Prints this information.")
        elif cmd == "analyze":
            user_id = int(input("Enter user_id: "))
            value = int(input("Enter value: "))

            data, dk, n = get_encrypted_data(client, user_id, value)
            if data == 0:
                print("Something went wrong.")
                continue

            result = decrypt(client, data, dk, n, value)
            analyze_hypnogram(result, value)
        else:
            print("Unknown command.")


# CLI interface for dna data analysis
def dna_interface(client):
    print("Type 'help' for commands.")
    while True:
        print("")
        cmd = input("> ").strip().lower()
        print("")

        if cmd == "back":
            break
        elif cmd == "help":
            print("Available commands:")
            print(
                "     > analyze     | Analyze encrypted dna data. Asks for user id and value."
            )
            print(
                "     > back        | Returns to the previous interface where you can choose data type to analyze."
            )
            print("     > help        | Prints this information.")
        elif cmd == "analyze":
            user_id = int(input("Enter user_id: "))
            value = int(input("Enter value: "))

            data, dk, n = get_encrypted_data(client, user_id, value)
            if data == 0:
                print("Something went wrong.")
                continue

            result = decrypt(client, data, dk, n, value)
            analyze_genome(result, value)
        else:
            print("Unknown command.")


# Function for fetching encrypted data information from the SPADE server
def get_encrypted_data(client, user_id, value):
    # Fetch required information from SPADE server
    dk, encrypted_data, n = client.derive_key(user_id, value)

    # Error check
    if dk == 0:
        return 0, 0, 0

    # Compile the encrypted data based on the received information
    h = []
    c = []
    h_done = False
    filename = ""

    # Check if the received encrypted data is in a file or in the response
    if encrypted_data[0].startswith("file:"):
        enc_file = encrypted_data[0].split(":")
        filename = enc_file[1]

        with open(filename, "r") as file:
            for datapoint in file:
                if datapoint.strip() == ":":
                    h_done = True
                else:
                    if h_done:
                        c.append(int(datapoint.strip()))
                    else:
                        h.append(int(datapoint.strip()))
    else:
        h, c = encrypted_data[0]["h"], encrypted_data[0]["c"]

    data = {"h": h, "c": c}

    # Return encrypted data, derived key and data length
    return data, dk, n


# Function for decrypting the encrypted data using the derived key
def decrypt(client, data, dk, n, v):
    q, g, mpk = client.get_public_parameters(n)  # Fetch public params
    cipher = SPADE.SPADE(n, q, g, mpk)  # Initialize SPADE cipher instance

    c = data["c"]  # Cipher text
    h = data["h"]  # Helping information
    y = cipher.decrypt(dk, c, h, v)  # Partially decrypted data

    # Return the partially decrypted data
    return y


# Function for analyzing partially decrypted hypnogram data
def analyze_hypnogram(data, v):
    # Compute how many times value appears and changes inside the data
    amount = data.count(1)
    breaks = sum(1 for i in range(len(data) - 1) if data[i] == 1 and data[i + 1] != 1)

    # Compute the sequences the value appears in
    sequence = 0
    sequences = []
    for datapoint in data:
        if datapoint == 1:
            sequence += 1
        else:
            if sequence > 0:
                sequences.append(sequence)
                sequence = 0

    if sequence > 0:
        sequences.append(sequence)

    # Print computed information about partially decrypted data
    print(f"\nThe value {v} appears a total of {amount} times in the hypnogram data.")
    print(
        f"The value changes from {v} to something else a total of {breaks} times in the hypnogram data."
    )
    print(f"The value {v} appears in the following sequences within the data:")
    for sequence in sequences:
        print(f"---     {sequence}")


# Function for analyzing partially decrypted dna data
def analyze_genome(data, v):
    # Compute the indexes the dinucleotide appears in
    locations = [i for i, value in enumerate(data) if value == 1]

    # Print all the indexes the dinucleotide appears in and how many times it appears inside the data
    for index in locations:
        print(f"{index} ", end="")
    print(
        f"\n\n^ The dinucleotide {DINUCLEOTIDE_VALUE_TABLE[v]} appears within the next indices inside the data ^"
    )
    print(
        f"The dinucleotide {DINUCLEOTIDE_VALUE_TABLE[v]} appears in the data {len(locations)} times"
    )


# Main function for the script
def main():
    if len(argv) == 3:
        # Initialize analyst client with provided host address and port
        client = SPADEAnalyst(host=argv[1], port=int(argv[2]))

        # Menu for choosing the type of data to analyze
        print("Connection successful.")
        while True:
            print("Would you like to analyze (h)ypnogram or (d)na records?")
            usr_input = input("> ").strip().lower()
            if usr_input == "h":
                hypnogram_interface(client)
            elif usr_input == "d":
                dna_interface(client)
            elif usr_input == "quit":
                break

    else:
        # Print usage instructions if incorrect arguments are provided
        print("Invalid number of arguments. Usage:")
        print("     python user_client.py <host> <port>")
        print("Example:")
        print("     python user_client.py localhost 5000")


if __name__ == "__main__":
    main()
