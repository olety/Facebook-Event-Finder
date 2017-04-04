import dateutil.parser
import time
import json
import requests
from models import Event, Place
from __init__ import db

LAT_PER_100M = 0.001622 / 1.8
LONG_PER_100M = 0.005083 / 5.5


def lat_from_met(met):
    return LAT_PER_100M * met / 100.0


def long_from_met(met):
    return LONG_PER_100M * met / 100


def generate_coordinates(center_point_lat, center_point_lng, radius=10000,
                         scan_radius=750):
    top = center_point_lat + lat_from_met(radius)
    left = center_point_lng - long_from_met(radius)

    bottom = center_point_lat - lat_from_met(radius)
    right = center_point_lng + long_from_met(radius)

    scan_radius_step = (lat_from_met(scan_radius),
                        long_from_met(scan_radius))
    lat = top
    lng = left
    while lat > bottom:
        while lng < right:
            yield (lat, lng)
            lng += scan_radius_step[1]
        lng = left
        lat -= scan_radius_step[0]


def get_page_ids(lat, lon):
    pages_id = requests.get(
        "https://graph.facebook.com/v2.8/search?type=place&q={0}&center={1},{2}&distance={3}&limit={4}&fields=id&access_token={5}".format(
            args["keyword"],
            lat, lon,
            args["distance"],
            args["limit"],
            token)).json()
    pages_id_list = [i['id'] for i in pages_id['data']]
    while 'paging' in pages_id and 'next' in pages_id['paging']:
        pages_id = requests.get(pages_id["paging"]['next']).json()
        for page in pages_id['data']:
            pages_id_list.append(page.get('id', None))
    return pages_id_list


def events_from_page_id(page_id):
    try:
        params = {
            "ids": page_id,
            "fields": "events.fields(id,name,start_time,description,place,type,category,ticket_uri,cover.fields(id,source),picture.type(large),attending_count,declined_count,maybe_count,noreply_count).since({0}),id,name,cover.fields(id,source),picture.type(large),location".format(
                int(time.time())),
            "access_token": token,
        }
        events = requests.get("https://graph.facebook.com/v2.8/", params=params)
        return events.json()
    except Exception as e:
        print(e)
        return None


def event_to_model(event_dict):
    place_dict = event_dict.get('place', {})
    if not Place.query.filter_by(id=place_dict.get('id', '0')).all():
        place_loc = place_dict.get('location', {})
        place = Place(id=place_dict.get('id', '0'), name=place_dict.get('name', 'Unnamed'),
                      city=place_loc.get('city', 'Wroclaw'), country=place_loc.get('country', 'Poland'),
                      lat=place_loc.get('latitude', 0.0), lon=place_loc.get('longitude', 0.0),
                      street=place_loc.get('street', 'Unknown'), zip=place_loc.get('zip', '00-000'))
        db.session.add(place)
    if not Event.query.filter_by(id=event_dict.get('id', '0')).all():
        event = Event(id=event_dict.get('id', '0'), desc=event_dict.get('description', 'None'),
                  name=event_dict.get('name', 'Unnamed'),
                  pic_url=event_dict.get('picture', {}).get('data', {}).get('url', ''),
                  tick_url=event_dict.get('ticket_uri', ''), place_id=place_dict.get('id', '0'),
                  start_time=dateutil.parser.parse(event_dict.get('start_time', '2017-04-07T16:00:00+0200')))
        db.session.add(event)


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        args = json.load(f)

    token = requests.get(
        "https://graph.facebook.com/v2.8/oauth/access_token?client_id={0}&client_secret={1}&&grant_type=client_credentials".format(
            args["client_id"], args["client_secret"])).json()['access_token']
    coords = (51.109940, 17.033767, 1000) # lat/lon and radius
    i = 0
    for point in generate_coordinates(*coords, scan_radius=args["distance"]):
        for page_id in get_page_ids(point[0], point[1]):
            if page_id:
                page_events = events_from_page_id(page_id)[page_id]
                if page_events and 'events' in page_events:
                    for event in page_events['events']['data']:
                        event_to_model(event)
                i += 1
                print('Processed {} pages...'.format(i))
            if i >= 10:
                print('processed >10 pages, stopping...')
                break
    db.session.commit()
