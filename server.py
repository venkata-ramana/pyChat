#!/usr/bin/python
# Tcp Chat server

import socket, select, json, sys
import client
################################################################################
# CURRENT CLIENTSIDE CONSTRAINTS:
#	1) usernames cannot have any non-alphabetical or non-numerical characters in them
################################################################################

# a client class, which contains a clients username and chat buffer
class Client():
    def __init__(self, username):
        self.buffer = ['welcome to the chat!']
        self.canvas_buffer = []
        self.username = username


def update_canvas_buffers(canvas_message):
    for client in CLIENTS:
        CLIENTS[client].canvas_buffer.append(canvas_message)


# updates all buffers with the recieved message
#
# @param message - the new message
# @return void
def update_buffers(message):
    for client in CLIENTS:
        CLIENTS[client].buffer.append(message)


# checks for clients with the username 'username'
#
# @param username - the username to check for
# @return true if there is such a user connected, false otherwise
def client_named(username):
    for client in CLIENTS:
        if CLIENTS[client].username == username:
            return True
    return False


# handles new client connection requests. If the first message sent by
# a client is not 'USERNAME xxxx' where xxxx is a unique username, the
# connection is terminated.
#
# @param server_socket - The server socket that recieved the connection request.
# @return void
def handle_connection(server_socket):
    print 'new connection'
    client_socket, addr = server_socket.accept()
    msg = client_socket.recv(RECV_BUFFER)
    if msg.split(':')[0] == 'USERNAME':
        username = msg.split(':')[1]
        if client_named(username):
            client_socket.send("username in use")
            client_socket.close()
        else:
            CONNECTIONS.append(client_socket)
            CLIENTS[client_socket] = Client(username)
            update_buffers(username + " entered room")
            client_socket.send("connected")
            print username + " connected"
    else:
        client_socket.send("bad handshake - no username provided")
        client_socket.close()


# handles messages recieved from clients. If the message does not follow
# the correct form, the message is discarded.
#
# @param client_socket - the socket the request came in on
# @return void
def handle_client(client_socket):
    # print 'handling client'
    username = CLIENTS[client_socket].username
    data = client_socket.recv(RECV_BUFFER)
    type = data.split(':')[0]
    if type == 'PUT':
        getMessage(username, data)
    elif type == 'CPUT':
        getCanvasMessage(username, data)
    elif type == 'GET':
        sendBuffer(client_socket)
    elif type == 'CGET':
        sendCanvasBuffer(client_socket)
    elif type == 'FILE':
        getMessage(username, data)
    elif type == 'USERS':
        sendUsers(client_socket)
    else:
        client_socket.send('bad request\nREQUEST: \n' + data)


# Handles a message that has been recieved.
#
# @param username - the user the message was recieved from.
# @param data - the data that came in from the socket.
# @return void
def getMessage(username, data):
    msg = username + ': ' + data.replace('PUT:', '', 1)
    print msg
    update_buffers(msg)


# Handles a canvas message that has been recieved.
#
# @param username - the user the message was recieved from.
# @param data - the data that came in from the socket.
# @return void
def getCanvasMessage(username, data):
    msg = data.replace('CPUT:', '', 1)
    update_canvas_buffers(msg)


# Send the buffer for the client socket to the client socket.
#
# @param client_socket - the socket that requested its buffer
# @return void
def sendBuffer(client_socket):
    buffer = CLIENTS[client_socket].buffer
    client_socket.send(json.dumps(buffer))
    CLIENTS[client_socket].buffer = []


# Send the canvas buffer for the client socket to the client socket.
#
# @param client_socket - the socket that requested its canvas buffer
# @return void
def sendCanvasBuffer(client_socket):
    canvas_buffer = CLIENTS[client_socket].canvas_buffer
    client_socket.send(json.dumps(canvas_buffer))
    CLIENTS[client_socket].canvas_buffer = []


# Send the users list to the client socket.
#
# @param client_socket - the socket that requested the userlist
# @return void
def sendUsers(client_socket):
    users = [client.username for client in CLIENTS.values()]
    client_socket.send(json.dumps(users))

# Main method
# if __name__ == "__main__":

# initialize global connection structures
CONNECTIONS = []
CLIENTS = {}

# server settings
RECV_BUFFER = 4096
PORT = 15011
HOST = "localhost"
MAX_CONNNECTIONS = 10


if __name__ == "__main__":
    # initialize server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allows socket to be reused in TIME_WAIT state. Do not use in production
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CONNNECTIONS)
    CONNECTIONS.append(server_socket)

    print "Chat server started on port " + str(PORT)
    # checking

    # listen for sockets ready to be 'recieved' from

    while 1:
        try:
            read_sockets, write_sockets, error_sockets = select.select(CONNECTIONS, [], [])
            for sock in read_sockets:
                if sock == server_socket:
                    handle_connection(sock)
                elif sock in CLIENTS.keys():
                    handle_client(sock)

        except socket.error:
            if "sock" in vars() and sock in CLIENTS.keys():
                update_buffers(CLIENTS[sock].username + " left the room")
                CONNECTIONS.remove(sock)
                del CLIENTS[sock]
                sock.close()

        except KeyboardInterrupt:
            # close server socket on ctrl + C
            print '\nclosing server'
            server_socket.close()
            print 'server closed'
            sys.exit()

