import json

from flask import Flask, request

import fbd

app = Flask(__name__)
s = fbd.storage.Storage()


@app.route('/places', methods=['GET'])
def show_places():
    if request.args.get('id', None):
        return s.get_place(request.args['id']).to_json()
    elif request.args.get('lat', None) and request.args.get('lon', None) and request.args.get('dist', None):
        return json.dumps([_.to_dict() for _ in
                           s.get_places_coords(float(request.args['lat']),
                                               float(request.args['lon']),
                                               distance=float(request.args['dist']))],
                          default=fbd.tools.default_json_serializer)
    else:
        return json.dumps(s.get_all_place_ids(), default=fbd.tools.default_json_serializer)


@app.route('/events', methods=['GET'])
def show_events():
    if request.args.get('id', None):
        return s.get_event(request.args['id']).to_json()
    elif request.args.get('lat', None) and request.args.get('lon', None) and request.args.get('dist', None):
        return json.dumps([_.to_dict() for _ in s.get_events_coords(request.args['lat'],
                                                                    request.args['lon'],
                                                                    distance=request.args['dist'])],
                          default=fbd.tools.default_json_serializer)
    else:
        return json.dumps(s.get_all_event_ids(), default=fbd.tools.default_json_serializer)


if __name__ == '__main__':
    app.run()
