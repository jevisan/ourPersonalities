import os
import socket
import numpy as np
import pickle
import struct
import gensim

EMB_MODEL = 'Word2Vec/vecStand.COW_ESP_14_LIMP.txt'

#========================================================#
# Based on ekbanasolutions' numpy-using-socket project   #
# https://github.com/ekbanasolutions/numpy-using-socket  #
#========================================================#

class EmbdSocketServer:
    """
    SocketServer
    Receives queries as strings
    Returns numpy arrays of embeddings
    """
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.address, self.port))
        self.embeddings_file = os.path.join(EMB_MODEL)
        self.emb_model = gensim.models.KeyedVectors.load_word2vec_format(self.embeddings_file)

    def receive_request(self):
        """
        Server listens in socket
        """
        self.socket.listen(1)
        self.client_socket, self.client_addr = self.socket.accept()
        print('connected to', self.client_addr)
        cummdata = ''
        while True:
            # RECEIVE QUERY STRING FROM CLIENT
            data = self.client_socket.recv(1024)
            if data:
                print("received querie for", data)
                cummdata = data.decode('ascii')
                # NECESARY PROCESS OF QUERYNG EMBEDDINGS AND RETURNING RESULTS TO CLIENT
                try:
                    vector = self.get_np_array(cummdata)
                    if vector.any():
                        self.send_np_array(vector)
                except Exception as e:
                    self.send_np_array(None)
            if not data:
                break


    def get_np_array(self, w):
        """
        Gets vector of word w
        """
        # DUMMY DATA - RANDOM NP ARRAY WITH 300 VALUES
        print("Getting word vector")
        # arr = np.random.rand(1, 300)
        try:
            vector = np.array(self.emb_model[w])
        except Exception as e:
            return None
        return vector


    def send_np_array(self, np_array):
        """
        Sends numpy array of w2v representation
        to listening socket
        """
        data = pickle.dumps(np_array)
        # GET MESSAGE LENGTH
        m_size = struct.pack("L", len(data))
        # SEND DATA
        print("sending object of size", len(data), "back to client")
        self.client_socket.sendall(m_size + data)


    def __del__(self):
        """
        Deleting socket instance
        """
        self.socket.close()


if __name__ == '__main__':
    np_server = EmbdSocketServer('127.0.0.1', 9090)
    print("Socket server set up in: ", np_server.address, " on port: ", np_server.port)

    while True:
        print("Accepting requests")
        np_server.receive_request()
