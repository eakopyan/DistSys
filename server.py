# coding=utf-8

# ------------------------------------------------------------------------------------------------------

# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID

# Students:
# - Edoardo Puggioni
# - Jean-Nicolas Winter

# ------------------------------------------------------------------------------------------------------

import traceback
import sys
import time
import json
import argparse
from threading import Thread

from bottle import Bottle, run, request, template
import requests

# ------------------------------------------------------------------------------------------------------

try:
    app = Bottle()

    # Dictionary to store all entries of the blackboard.
    board = {}

    # Variable to know the next ID to use for each new entry.
    next = 0

    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------

    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):

        global board, node_id
        success = False

        try:
            # Simply add new element to the dictionary using entry_sequence as index.
            board[entry_sequence] = element
            success = True

        except Exception as e:
            print e

        return success


    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call=False):

        global board, node_id
        success = False

        try:
            # Modify dictionary element using entry_sequence as index.
            board[entry_sequence] = modified_element
            success = True

        except Exception as e:
            print e

        return success


    def delete_element_from_store(entry_sequence, is_propagated_call=False):

        global board, node_id
        success = False

        try:
            # Delete dictionary element using entry_sequence as index.
            del board[entry_sequence]
            success = True

        except Exception as e:
            print e

        return success


    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success


    def propagate_to_vessels(path, payload=None, req='POST'):
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id:  # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                if not success:
                    print "\n\nCould not contact vessel {}\n\n".format(vessel_id)


    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------

    @app.route('/')
    def index():
        global board, node_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id),
                        board_dict=sorted(board.iteritems()), members_name_string='YOUR NAME')


    @app.get('/board')
    def get_board():
        global board, node_id
        print board
        return template('server/boardcontents_template.tpl', board_title='Vessel {}'.format(node_id),
                        board_dict=sorted(board.iteritems()))

    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():

        # Adds a new element to the board
        # Called directly when a user is doing a POST request on /board

        global board, node_id, next

        try:

            new_entry = request.forms.get('entry')

            # We add new element to dictionary using next as entry sequence.
            add_new_element_to_store(str(next), new_entry)

            # Build path to propagate, using key word "add" and next as element_id.
            path = "/propagate/add/" + str(next)

            # Increment next for the next use of this function.
            next += 1

            # Start thread so the server doesn't make the client wait.
            thread = Thread(target=propagate_to_vessels, args=(path, new_entry,))
            thread.deamon = True
            thread.start()
            return True

        except Exception as e:
            print e

        return False


    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):

        # Modify or delete an element in the board
        # Called directly when a user is doing a POST request on /board/<element_id:int>/

        # Retrieving the ID of the action, which can be either 0 or 1.
        # 0 is received when the user clicks on "modify".
        # 1 is received when the user clicks on "delete".
        delete = request.forms.get('delete')

        if delete == "0":
            # User wants to modify entry with ID given by element_id.
            new_entry = request.forms.get('entry')
            modify_element_in_store(str(element_id), new_entry)

            # Build path to propagate using keyword "mod" which stands for "modify".
            path = "/propagate/mod/" + str(element_id)

            thread = Thread(target=propagate_to_vessels, args=(path, new_entry,))
            thread.deamon = True
            thread.start()

        elif delete == "1":
            # User wants to delete entry with ID given by element_id.
            delete_element_from_store(entry_sequence=str(element_id))

            # Build path to propagate using keyword "del" which stands for "delete".
            path = "/propagate/del/" + str(element_id)

            thread = Thread(target=propagate_to_vessels, args=(path, "nothing",))
            thread.deamon = True
            thread.start()

        pass


    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):

        global next

        # Propagate action. An action is distinguished using one of the three keywords "add", "mod" and "del", which
        # stand for add, modify and delete respectively. After identifying the action, we identify the entry to
        # add/modify/delete by using the variable element_id, and also in the case of add and modify, the new entry can
        # be retrieved from the body of the POST request.

        if action == "add":
            # We retrieve the new entry from the body of the POST request.
            entry = request.body.read()
            add_new_element_to_store(element_id, entry)
            next += 1

        if action == "mod":
            # We retrieve the new entry from the body of the POST request.
            entry = request.body.read()
            modify_element_in_store(element_id, entry)

        if action == "del":
            delete_element_from_store(entry_sequence=element_id)

        pass


    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app

        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int,
                            help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            print e


    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()

except Exception as e:
    traceback.print_exc()
    while True:
        time.sleep(60.)
