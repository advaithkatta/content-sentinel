from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import random
from cryptography.fernet import Fernet


# --- QKD Simulation (BB84-like) ---
def simulate_qkd(num_bits=16):
    # Alice generates random bits and bases
    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(['X', 'Z']) for _ in range(num_bits)]

    # Bob randomly picks bases
    bob_bases = [random.choice(['X', 'Z']) for _ in range(num_bits)]
    bob_results = []

    sim = AerSimulator()  # Use AerSimulator from qiskit_aer

    # Simulate measurement
    for bit, a_base, b_base in zip(alice_bits, alice_bases, bob_bases):
        qc = QuantumCircuit(1, 1)

        # Prepare qubit
        if bit == 1:
            qc.x(0)
        if a_base == 'X':
            qc.h(0)

        # Measure in Bob's basis
        if b_base == 'X':
            qc.h(0)
        qc.measure(0, 0)

        # Transpile and run
        transpiled_qc = transpile(qc, sim)
        job = sim.run(transpiled_qc, shots=1)
        result = job.result()
        measured = int(list(result.get_counts().keys())[0])
        bob_results.append(measured)

    # Keep only matching bases
    shared_key_bits = [
        a_bit for a_bit, a_base, b_base, b_bit in zip(alice_bits, alice_bases, bob_bases, bob_results)
        if a_base == b_base and a_bit == b_bit
    ]

    # Convert bits to Fernet-compatible 32-byte key
    key_bytes = bytes(shared_key_bits)
    while len(key_bytes) < 32:
        key_bytes += b'0'
    key_bytes = key_bytes[:32]

    # For demo purposes, return a proper Fernet key
    return Fernet.generate_key()


# --- Moderators using shared key ---
class Moderator:
    def __init__(self, name, key):
        self.name = name
        self.cipher = Fernet(key)

    def send_message(self, msg, recipient):
        encrypted = self.cipher.encrypt(msg.encode())
        print(f"{self.name} → {recipient.name} (encrypted):", encrypted.decode())
        recipient.receive_message(encrypted, self)

    def receive_message(self, encrypted, sender):
        decrypted = self.cipher.decrypt(encrypted).decode()
        print(f"{self.name} received from {sender.name}: {decrypted}")


if __name__ == "__main__":
    print("🔑 Simulating QKD...")
    shared_key = simulate_qkd()
    print("Shared secret key established!\n")

    alice = Moderator("Alice", shared_key)
    bob = Moderator("Bob", shared_key)

    alice.send_message("I think this post should be removed.", bob)
    bob.send_message("Agreed, let’s vote remove.", alice)