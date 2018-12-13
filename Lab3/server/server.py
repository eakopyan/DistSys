# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 3
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

    board = {} # All messages are stored in the board array
    modify_hist = {} # Stores all history of elements to be modified
    delete_hist = [] # Stores all history of elements to be deleted

    # Unlike in lab1, the ID to use is represented by a sequence
    my_seq = '0'

    start_time = 0
    end_time = 0
    consistency_slot = 0 # Time by which consistency is achieved

    first_transmission = True # Used to start the clock




    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    '''
    Function times_up
    Once a certain number of messages have been exchanged, we stop the clock
    Returns the end time
    '''
    def times_up():
        global board, vessel_list, end_time

        nb_message = len(board)
        final_nb = len(vessel_list)*20 # We arbitrarily stop the clock after this number of messages

        if nb_message == final_nb:
            end_time = clock.time()

        return end_time


    '''
    Function get_time
    Calculates the time spent since the beginning of the simulation
    '''
    def get_time():
        global start_time

        current_time = clock.time() - start_time
        print "The current time is", str(current_time)
        return current_time


    '''
    Function get_consistency_slot
    Calculates the needed time to achieve consistency
    '''
    def get_consistency_slot():
        global start_time, end_time, consistency_slot

        consistency_slot = end_time - start_time
        print "Consistency reached in", str(consistency_slot)
        return consistency_slot


    '''
    Function add_new_element_to_store
    Returns the sequence number of the added element
    param entry_sequence: index of the board dictionary where the new element is to be added
    param element: new message to be added
    param is_propagated_call: the action comes (not) from another vessel
    '''
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
        global board, node_id, my_seq, start_time, end_time, consistency_slot

        return_seq = entry_sequence

        try:
            if is_propagated_call: # Update from another vessel
                entry_seq_no = entry_sequence.split(':')[0]
                entry_from = entry_sequence.split(':')[1] # ID of the sender
                if int(entry_seq_no) > int(my_seq):
                    my_seq = entry_seq_no

            else: # We only update our own board
                if len(board) == 0: # Initialize the board if needed
                    entry_sequence = '0'
                    my_seq = entry_sequence
                else:
                    my_seq = str(int(my_seq)+1) # Increment the sequence number
                return_seq = str(my_seq) + ':' + str(node_id)

            # Add new element to the array
            board[return_seq] = element

            times_up()
            if end_time != 0: # The simulation has reached its end
                get_consistency_slot()
            else:
                get_time()

        except Exception as e:
            print e

        return str(return_seq)


    '''
    Function modify_element_in_store
    param id: index of the board dictionary where the element is to be modified
    param entry_sequence: sequence number of the message to be modified
    param modified_element: new message to be uploaded instead of the previous one
    param is_propagated_call: the action comes (not) from another vessel
    '''
    def modify_element_in_store(id, entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id, my_seq, modify_hist

        success = False

        try:
            if id in board:
                # Modify the element at the specified index
                board[id] = modified_element

                if not is_propagated_call:
                    my_seq = str(int(my_seq)+1)

                success = True

            else:
                if id in modify_hist: # Only take the last update
                    if modify_hist[id][0] <= entry_sequence: # Overwrite the history of this sequence if necessary
                        modify_hist[id][0] = entry_sequence
                        modify_hist[id][1] = modified_element

                else: # Add sequence to history
                    modify_hist[id][0] = entry_sequence
                    modify_hist[id][1] = modified_element


        except Exception as e:
            print e

        return success


    '''
    Function delete_element_from_store
    param entry_sequence: index of the board dictionary where the element is to be deleted
    param is_propagated_call: the action comes (not) from another vessel
    '''
    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id
        success = False

        try:
            if entry_sequence in board:
                del board[entry_sequence] # Delete the element at the specified index
                success = True

            else: # In case the element doesn't exit in local board
                delete_hist.append(entry_sequence)

        except Exception as e:
            print e

        return success


    '''
    Function compare (useful in the sorting algorithm of the board)
    param element: tuple of sequence number and node ID
    '''
    def compare(element):
        a = element[0].split(':')[0] # my_seq of the element
        b = element[0].split(':')[1] # node_id of the element
        return float(float(a)+float(b)/1000) # Assume that the number of messages with the same seq_no is less than 1000



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
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems(), key = lambda x: int(x[0].split(':')[0])), members_name_string='Evelyne AKOPYAN, Alexandre LONGHI')


    @app.get('/board')
    def get_board():
        global board, modify_hist, delete_hist, node_id

        ''' OR print modify_hist '''
        print board
        modify_list = []

        for id in modify_hist: # Update the elements in 'modify_hist'
            success = modify_element_in_store(id, modify_hist[id][0], modify_hist[id][1], True)
            if success:
                modify_list.append(id)
                path = '/propagate/mod/'+id
                payload = {'sequence':modify_hist[id][0], 'value':modify_hist[id][1]}

                thread=Thread(target=propagate_to_vessels, args=(path, payload,))
                thread.deamon=True
                thread.start()

        for id in modify_list: # Delete the modified element from history
            del modify_hist[id]

        for id in delete_hist:
            delete_element_from_store(id)
            path = '/propagate/del/'+id

            thread=Thread(target=propagate_to_vessels, args=(path))
            thread.deamon=True
            thread.start()

            if success:
                del delete_hist[id]

        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems(), key = compare))

    # ------------------------------------------------------------------------------------------------------

    @app.post('/board')
    def client_add_received():
        '''
        Adds a new element to the board
        Called directly when a user is doing a POST request on /board
        '''

        global board, node_id, start_time, first_transmission

        try:
            if first_transmission:
                start_time = clock.time()
                first_transmission = False

            new_entry = request.forms.get('entry')
            add_seq = add_new_element_to_store(None, new_entry)
            path = '/propagate/add/'+add_seq
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

        if delete == "0": # modification
            new_entry = request.forms.get('entry')
            modify_element_in_store(str(element_id), my_seq, new_entry)

            path = "/propagate/mod/" + str(element_id)
            payload = {'sequence': my_seq, 'value': new_entry}

            thread = Thread(target=propagate_to_vessels, args=(path, payload,))
            thread.deamon = True
            thread.start()

        elif delete == "1": # deletion
            delete_element_from_store(entry_sequence=str(element_id))
            path = "/propagate/del/" + str(element_id)

            thread = Thread(target=propagate_to_vessels, args=(path))
            thread.deamon = True
            thread.start()

        pass


    @app.post('/propagate/<action>/<element_id>')
    def propagation_received(action, element_id):
        '''
        Decides on the function to call depending on the action requested
        '''

        if action=="add":
            # Get the message to add from the body of the request
            entry=request.body.read()
            add_new_element_to_store(element_id, entry, True)

        if action=="mod":
            # Get the message to modify from the body of the request
            entry_seq = request.forms.get('sequence')
            entry_val=request.forms.get('value')
            modify_element_in_store(element_id, entry_seq, entry_val)

        if action=="del":
            delete_element_from_store(element_id, True)

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
        for i in range(1, args.nbv+1):
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
