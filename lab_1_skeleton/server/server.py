# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Students: Evelyne Akopyan, Alexandre Longhi
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

    # All entries are stored in the board array
    board = {}

    # Represents the next ID to use
    next=0


    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------

    '''
    Function add_new_element_to_store
    param entry_sequence: index of the board dictionary where the new element is to be added
    param element: new message to be added
    '''
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
        global board, node_id
        success = False

        try:
            # Add new element to the array
            board[entry_sequence] = element
            success = True

        except Exception as e:
            print e

        return success


    '''
    Function modify_element_in_store
    param entry_sequence: index of the board dictionary where the element is to be modified
    param modified_element: new message to be uploaded instead of the previous one
    '''
    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id
        success = False

        try:
            # Modify the element at the specified index
            board[entry_sequence] = modified_element
            success = True

        except Exception as e:
            print e

        return success


    '''
    Function delete_element_from_store
    param entry_sequence: index of the board dictionary where the element is to be deleted
    '''
    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id
        success = False

        try:
            # Delete the element at the specified index
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

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
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
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='YOUR NAME')


    @app.get('/board')
    def get_board():
        global board, node_id
        print board
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))

    # ------------------------------------------------------------------------------------------------------

    @app.post('/board')
    def client_add_received():
        '''
        Adds a new element to the board
        Called directly when a user is doing a POST request on /board
        '''

        global board, node_id, next

        try:
            new_entry = request.forms.get('entry')

            # Use next to add the new element to the dictionary
            add_new_element_to_store(str(next), new_entry)

            # Propagate the update where <action>=add and <element_id>=next
            path="/propagate/add/"+str(next)

            # Increment for later use of this function
            next+=1

            # Open thread as a deamon to enable multiple access
            thread=Thread(target=propagate_to_vessels, args=(path, new_entry,))
            thread.deamon=True
            thread.start()

            return True

        except Exception as e:
            print e

        return False


    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        '''
        Either modify or delete an element of the board from a POST request
        From boardcontents_template.tpl we know that the ID of the action can be:
        0 when the user clicks on "modify"
        1 when the user clicks on "x" (meaning delete)
        '''

        delete = request.forms.get('delete')

        if delete == "0":
            # modification
            new_entry = request.forms.get('entry')
            modify_element_in_store(str(element_id), new_entry)

            path = "/propagate/mod/" + str(element_id)

            thread = Thread(target=propagate_to_vessels, args=(path, new_entry,))
            thread.deamon = True
            thread.start()

        elif delete == "1":
            # deletion
            delete_element_from_store(entry_sequence=str(element_id))

            path = "/propagate/del/" + str(element_id)

            thread = Thread(target=propagate_to_vessels, args=(path, "nothing",))
            thread.deamon = True
            thread.start()
        pass


    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        '''
        Decides on the function to call depending on the action requested
        '''
        global next

        if action=="add":
            # Get the message to add from the body of the request
            entry=request.body.read()
            add_new_element_to_store(element_id, entry)
            next+=1

        if action=="mod":
            # Get the message to modify from the body of the request
            entry=request.body.read()
            modify_element_in_store(element_id, entry)

        if action=="del":
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
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
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
