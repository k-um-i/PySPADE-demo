from sys import argv
import socket
import struct
import random
import pickle
import time

###-----CONFIG-----###

# DEFAULT HOST AND PORT
HOST = "localhost"  # Default hostname
PORT = 5000  # Default port num

# VALUES
Q = 65537  # Prime modulus
G = 3  # Generator of group of order q


# Class for hosting SPADE instances for different sizes of n.
class SPADEInstance:
    def __init__(self, n, q, g):
        self.n = n
        self.q = q
        self.g = g

        # Generating Master secret key MSK and deriving Master public key MPK
        self.msk = [random.randint(1, q - 1) for _ in range(n)]
        self.mpk = [pow(g, s, q) for s in self.msk]


# Class for the main SPADE server instance.
class SPADEServer:
    def __init__(self, q, g, host, port):
        self.q = q  # Prime modulus
        self.g = g  # Generator
        self.host = host  # Host address
        self.port = port  # Port number
        self.users = {}  # Dict for user information
        self.encrypted_data = {}  # Dict for user encrypted data information
        self.instances = {}  # Dict for SPADE instances

    # Function for handling incoming client requests
    def handle_request(self, conn):
        try:
            start = time.time()  # Starting timer for transaction

            # Receive a header for the length of the incoming data
            raw_length = conn.recv(4)
            if not raw_length:
                raise EOFError("No data length header received.")
            data_length = struct.unpack("!I", raw_length)[0]

            # Receiving the actual data in chunks and stopping after received data length is reached.
            data = b""
            while len(data) < data_length:
                packet = conn.recv(16384)
                if not packet:
                    raise EOFError("Connection closed before all data received.")
                data += packet

            received_size = len(data)  # Total size of received data
            print(f"\n---Received {received_size} bytes from client.")
            if data:
                # Deserializing the data and processing the request.
                request = pickle.loads(data)
                response = self.process_request(request)

                # Serializing generated response and sending it back to the client.
                response_data = pickle.dumps(response)
                sent_size = len(response_data)
                conn.sendall(struct.pack("!I", sent_size))  # Send data length header
                conn.sendall(response_data)  # Send actual response data

                # Calculating total transaction time and printing information about the transaction.
                transaction_time = time.time() - start
                print(f"---Sent {sent_size} bytes to client.")
                print(f"---Transaction time: {transaction_time:.5f} seconds.")

        except Exception as err:
            print(f"Error: {err}")
        finally:
            conn.close()  # Close the connection

    # Function for processing client requests
    def process_request(self, request):
        action = request.get("action")  # Get action from client request.

        if action == "register_user":
            # Register new user and return user details to client.
            return self.register_user()

        elif action == "derive_key":
            # Derive and return functional key for user data and value
            v = request.get("v")
            user_id = request.get("user_id")
            return self.derive_key(user_id, v)

        elif action == "get_public_parameters":
            # Provide public parameters to the client
            print("A client is requesting public parameters.")
            n = request.get("n")
            if n not in self.instances:
                # Create a new SPADE instance if one does not exist for data length n
                print("     No SPADE instance for requested data length.")
                print(f"     Creating new SPADE instance for n of {n}.")
                inst = SPADEInstance(n, self.q, self.g)
                self.instances[n] = inst

            print("    Sending public parameters.")
            # Return public parameters for SPADE instance.
            return {"q": self.q, "g": self.g, "mpk": self.instances[n].mpk}

        elif action == "store_data":
            # Store encrypted data submitted by the client
            print("A client is requesting to store data.")
            user_id = request.get("id")
            encrypted_data = request.get("encrypted_data")
            data_len = request.get("n")
            user_data = [encrypted_data, data_len]
            self.encrypted_data[user_id] = (
                user_data  # Store the data with user_id as key
            )

            print(f"User ID: {user_id}")

        return {"error": "Unknown action"}  # Handle unreqcognized actions

    # Function for registering a new user and generating their keys
    def register_user(self):
        alpha_j = random.randint(1, self.q - 1)  # Generate user private key
        g_alpha_j = pow(self.g, alpha_j, self.q)  # Compute user public key
        user_id = len(self.users) + 1  # Assing a unique ID for the user
        self.users[user_id] = {
            "alpha_j": alpha_j,
            "g_alpha_j": g_alpha_j,
        }  # Store user information
        print("A new user has registered.")
        print(f"    user_id: {user_id}")
        # Return the registration details to client
        return {"user_id": user_id, "alpha_j": alpha_j, "g_alpha_j": g_alpha_j}

    # Function for deriving functional key dk
    def derive_key(self, user_id, v):
        print("A client is requesting a key and data.")
        if user_id not in self.users:  # Ensure that the user exists
            print("Error: User not found.")
            return {"error": "User not found."}

        alpha_j = self.users[user_id]["alpha_j"]  # Retrieve user private key
        data_len = self.encrypted_data[user_id][1]  # Retrieve data length
        instance_msk = self.instances[data_len].msk  # Retrieve msk of SPADE instance

        # Compute the derived key based on given parameters.
        dk = [
            pow(self.g, alpha_j * (v - instance_msk[i]), self.q)
            for i in range(data_len)
        ]
        # Return derived key and data length to client
        return {"dk": dk, "encrypted_data": self.encrypted_data[user_id], "n": data_len}

    # Function for starting the server instance
    def run(self):
        print(f"Starting SPADE server on {self.host}:{self.port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))  # Bind the server to host and port
            server.listen(5)  # Listen for incoming connections
            print(f"Listening on {self.host}:{self.port}")
            while True:
                conn, _ = server.accept()  # Accept connection
                self.handle_request(conn)  # Handle client request


if __name__ == "__main__":
    if len(argv) == 3:
        # Use CLI args for host and port if provided
        server = SPADEServer(q=Q, g=G, host=argv[1], port=int(argv[2]))
    else:
        # Else use default host and port values
        server = SPADEServer(q=Q, g=G, host=HOST, port=PORT)
    server.run()  # Start the server
