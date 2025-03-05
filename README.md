# PySPADE-demo
Proof of concept python implementation of the functional encryption algorithm SPADE which allows for partial and selective decryption of encrypted contents.
## Notice
This code is only meant to be a proof of concept and as such should not be considered secure for use. Client code is missing important features and should only be used for testing purposes.
## Usage
Server client must be ran on the same machine as user and analyst clients as no encrypted data is transferred, only file locations of encrypted files are saved to the server. The server client displays information for time and data costs of each transaction. 

Multiple users can save encrypted data to the server. User client has no login implementation and instead registers a new user to the server each time it is ran. The user client is used to encrypt and save encrypted data to the server.

Analyst client allows for the partial and selective decryption of a requested user's data by requesting a partial decryption key from the server.
## Demo
A demonstration video of the code running can be found at: https://youtu.be/Syv-TaXJmaE
