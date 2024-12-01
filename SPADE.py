import random


# Class for the SPADE functional encryption algorithm
class SPADE:
    def __init__(self, n, q, g, mpk):
        self.n = n  # Data length
        self.q = q  # Prime modulus
        self.g = g  # Generator
        self.mpk = mpk  # Master public key

    # Function for encrypting integer data using the SPADE algorithm
    def encrypt(self, x, alpha_j):
        # Generate random noise for encryption
        r = [random.choice(range(1, self.q, 2)) for _ in range(self.n)]  # Noise

        # Compute helping information used for partial decryption
        h = [pow(self.g, alpha_j + r[i], self.q) for i in range(self.n)]

        # Compute the ciphertext for the data
        c = [
            pow(self.mpk[i], alpha_j, self.q)
            * pow(self.g, r[i] * x[i], self.q)
            % self.q
            for i in range(self.n)
        ]

        # Return helping information and ciphertext
        return h, c

    # Function for partially decrypting data using the SPADE algorithm
    def decrypt(self, dk, c, h, v):
        # Initialize the result vector
        y = []

        # Iterate over each element in the ciphertext and compute it's value
        for i in range(self.n):
            part1 = c[i]  # Ciphertext component
            part2 = pow(h[i], -v, self.q)
            part3 = dk[i]  # Decryption key component

            # Compute the decrypted value and append it to the result vector
            yi = (part1 * part2 * part3) % self.q
            y.append(yi)

        # Return the result vector
        return y


# Print information if someone tries to run the script on it's own.
def main():
    print("This script is not meant to be ran on it's own.")


if __name__ == "__main__":
    main()
