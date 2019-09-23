import sys
import socket
import struct
import pickle
import numpy as np


class EmbSocketClient:
    """EmbSocketClient."""
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((self.address, self.port))
        self.payload_size = struct.calcsize('L')
        self.data = b''

    def request_vector(self, message):
        # app.logger.info('Requesting array for ' + message)
        self.socket.send(message.encode('ascii'))

    def receive_vector(self):
        while len(self.data) < self.payload_size:
            self.data += self.socket.recv(4096)

        packed_msg_size = self.data[:self.payload_size]
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        # Retrieve all data based on message size
        while len(self.data) < msg_size:
            self.data += self.conn.recv(4096)

        arr_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        # Extract frame
        vector = pickle.loads(arr_data)
        return vector

    def query(self, word):
        self.request_vector(word)
        response = self.receive_vector()
        return response

    def __del__(self):
        """
        Deleting socket instance
        """
        self.socket.close()
