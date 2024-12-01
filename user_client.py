from sys import argv
import socket
import pickle
import random
import struct
import SPADE

# Dict for mapping dinucleotides to numeric values
DINUCLEOTIDE_VALUE_TABLE = {
    "AA": 1,
    "AC": 2,
    "AG": 3,
    "AT": 4,
    "CC": 5,
    "CA": 6,
    "CG": 7,
    "CT": 8,
    "GG": 9,
    "GA": 10,
    "GC": 11,
    "GT": 12,
    "TT": 13,
    "TA": 14,
    "TC": 15,
    "TG": 16,
}


# Class for SPADE user client
class SPADEUser:
    def __init__(self, host, port):
        self.host = host  # Server host address
        self.port = port  # Server port num
        self.user_id = None  # User ID assigned after registration
        self.private_key = None  # User private key
        self.public_key = None  # User public key

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

    # Function for registering the user on the SPADE server
    def register(self):
        request = {"action": "register_user"}  # Request for registration
        response = self.send_request(request)  # Send request and receive response
        self.user_id = response.get("user_id")  # Retrieve user ID
        self.private_key = response.get("alpha_j")  # Retrieve private key
        self.public_key = response.get("g_alpha_j")  # Retrieve public key

        # If being run inside the client and not perftest, print User ID and private key
        if __name__ == "__main__":
            print(
                f"Registered as User ID {self.user_id}, Private Key: {self.private_key}"
            )

    # Function for requesting public parameters for data length n
    def get_public_parameters(self, n):
        request = {"action": "get_public_parameters", "n": n}  # Form request
        response = self.send_request(request)  # Send request and receive response

        # Return public parameters from response
        return response.get("q"), response.get("g"), response.get("mpk")

    # Function for encrypting dna data from a file and sending resulting information to server
    def encrypt_genome(self, filename):
        data = []
        try:
            with open(filename, "r") as file:
                # Read the dna data from file and convert dinucleotides to integers.
                content = file.read().replace("\n", "")
                for i in range(0, len(content), 2):
                    num_value = DINUCLEOTIDE_VALUE_TABLE[content[i : i + 2]]
                    data.append(num_value)

        except FileNotFoundError:
            print(f"Could not find file '{filename}'.")

        n = len(data)  # Number of data points
        q, g, mpk = self.get_public_parameters(n)  # Retrieve public params
        cipher = SPADE.SPADE(n, q, g, mpk)  # Create SPADE cipher instance

        # Print information about encryption if being ran in client and not perftests
        if __name__ == "__main__":
            print(f"Encrypting {n} datapoints.")
        h, c = cipher.encrypt(data, self.private_key)  # Encrypt the data

        # Write the encrypted data to a new file
        with open(filename + ".encrypted", "w") as enc_f:
            for datapoint in h:
                enc_f.write(str(datapoint) + "\n")

            enc_f.write(":\n")

            for datapoint in c:
                enc_f.write(str(datapoint) + "\n")

        # Send information about the encrypted data to server
        request = {
            "action": "store_data",
            "id": self.user_id,
            "encrypted_data": "file:" + filename + ".encrypted",
            "n": n,
        }

        self.send_request(request)  # Send request

    # Function for encrypting hypnogram data from a file and sending resulting information to server
    def encrypt_hypnogram(self, filename):
        data = []
        try:
            with open(filename, "r") as file:
                # Read and save data from hypnogram file
                for line in file:
                    data.append(int(line))

        except FileNotFoundError:
            print(f"Could not find file '{filename}'.")
            return

        n = len(data)  # Number of data points
        q, g, mpk = self.get_public_parameters(n)  # Retrieve public params
        cipher = SPADE.SPADE(n, q, g, mpk)  # Create SPADE cipher instance

        # Print information about encryption if being ran in client and not perftests
        if __name__ == "__main__":
            print(f"Encrypting {n} datapoints.")
        h, c = cipher.encrypt(data, self.private_key)  # Encrypt the data

        # Write the encrypted data to a new file
        with open(filename + ".encrypted", "w") as enc_f:
            for datapoint in h:
                enc_f.write(str(datapoint) + "\n")

            enc_f.write(":\n")

            for datapoint in c:
                enc_f.write(str(datapoint) + "\n")

        # Send information about the encrypted data to server
        request = {
            "action": "store_data",
            "id": self.user_id,
            "encrypted_data": "file:" + filename + ".encrypted",
            "n": n,
        }

        self.send_request(request)  # Send request


# CLI interface for hypnogram encryption
def hypnogram_interface(client):
    print("Type 'help' for commands.")
    while True:
        cmd = input("\n> ").strip().split(" ")
        print("")

        if cmd[0] == "quit":
            break
        elif cmd[0] == "help":
            print("Available commands:")
            print("     > encrypt /path/to/file | Encrypts the specified file.")
            print("     > quit                  | Quits out of the program.")
            print("     > help                  | Prints this information.")
        elif cmd[0] == "encrypt":
            try:
                filename = cmd[1]
            except:
                print("Missing arguments.")
                continue
            client.encrypt_hypnogram(filename)
        else:
            print("Unknown command.")


# CLI interface for dna encryption
def dna_interface(client):
    print("Type 'help' for commands.")
    while True:
        cmd = input("\n> ").strip().split(" ")
        print("")

        if cmd[0] == "quit":
            break
        elif cmd[0] == "help":
            print("Available commands:")
            print("     > encrypt /path/to/file | Encrypts the specified file.")
            print("     > quit                  | Quits out of the program.")
            print("     > help                  | Prints this information.")
        elif cmd[0] == "encrypt":
            try:
                filename = cmd[1]
            except:
                print("Missing arguments.")
                continue
            client.encrypt_genome(filename)
        else:
            print("Unknown command.")


# Main program entry point
if __name__ == "__main__":
    if len(argv) == 3:
        # Create a SPADE user client with provided host and port
        client = SPADEUser(host=argv[1], port=int(argv[2]))
        client.register()  # Register the user on the SPADE server

        # Menu for choosing hypnogram or dna interface
        print("Connection successful.")
        print("Would you like to use (h)ypnogram or (d)na records?")
        while True:
            usr_input = input("> ").strip().lower()
            if usr_input == "h":
                hypnogram_interface(client)
                break
            elif usr_input == "d":
                dna_interface(client)
                break
            elif usr_input == "quit":
                break

    else:
        # Print usage instructions if incorrect arguments are provided
        print("Invalid number of arguments. Usage:")
        print("     python user_client.py <host> <port>")
        print("Example:")
        print("     python user_client.py localhost 5000")
