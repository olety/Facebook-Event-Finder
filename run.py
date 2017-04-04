from flask import jsonify
from __init__ import app, db
from models import Event, Place
import json

@app.route('/events')
def show_events():
    events = Event.query.all()
    event_list = []
    for event in events:
        event = event.__dict__
        event.pop('_sa_instance_state', 'None')
        event_list.append(event)
    return jsonify(event_list)


@app.route('/places')
def show_places():
    places = Place.query.all()
    place_list = []
    for place in places:
        place = place.__dict__
        place.pop('_sa_instance_state', 'None')
        place_list.append(place)
    return jsonify(place_list)


if __name__ == '__main__':
    app.run()
