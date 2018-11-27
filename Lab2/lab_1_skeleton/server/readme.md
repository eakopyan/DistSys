File server.py

Implement the Leader Election algorithm there.
All required functions should be call in the main() before the call to the app.

Implemented functions:
- send_id(): appends the ID of the current node to the provided data dictionary, and sends the new data to the next node
- elect_leader(): once every node knows the random id of everyone else, each of them elects the new leader
