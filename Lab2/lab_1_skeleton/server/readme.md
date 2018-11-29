**File server.py**

Implement the Leader Election algorithm there.

Implemented functions:
- send_id(): appends the ID of the current node to the provided data dictionary, and sends the new data to the next node
- elect_leader(): if the data has been propagated to everyone, each of the nodes elects the new leader
- long_live_the_leader(): if this is the leader, propagate its ID to everyone (not the random one!!) via the /propagate/coordinate route

Function propagate_to_vessels() also works differently depending on who's using it (leader or lambda): if it's a lambda, the message is only sent to the leader. If it's the leader, the message is sent to everyone.

Implemented routes:
- /propagate/elect/<random_id>: this route receives the new payload and leads to the elect_leader() function
- /propagate/coordinate: this route shares the ID of the leader with everyone
