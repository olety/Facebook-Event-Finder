import dateutil.parser
import sys
from geopy.geocoders import Nominatim
import time
import json
import requests
from models import db, Place, Event


class Scanner:
    LAT_PER_100M = 0.001622 / 1.8
    LONG_PER_100M = 0.005083 / 5.5

    @staticmethod
    def lat_from_met(met):
        return Scanner.LAT_PER_100M * met / 100.0

    @staticmethod
    def long_from_met(met):
        return Scanner.LONG_PER_100M * met / 100

    def __init__(self, client_id, client_secret, scan_radius, city, radius, **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scan_radius = scan_radius
        self.city = city
        self.radius = radius
        self.keyword = kwargs.get('keyword', '')
        self.pages_max = kwargs.get('pages_max', '')
        self.limit = kwargs.get('limit', '')
        self.token = self.generate_token()

    def generate_coordinates(self, center_point_lat, center_point_lng):
        top = center_point_lat + Scanner.lat_from_met(self.radius)
        left = center_point_lng - Scanner.long_from_met(self.radius)

        bottom = center_point_lat - Scanner.lat_from_met(self.radius)
        right = center_point_lng + Scanner.long_from_met(self.radius)

        scan_radius_step = (Scanner.lat_from_met(self.scan_radius),
                            Scanner.long_from_met(self.scan_radius))
        lat = top
        lng = left
        while lat > bottom:
            while lng < right:
                yield (lat, lng)
                lng += scan_radius_step[1]
            lng = left
            lat -= scan_radius_step[0]

    def get_page_ids(self, lat, lon):
        pages_id = requests.get(
            'https://graph.facebook.com/v2.8/search?type=place' +
            '&q={0}&center={1},{2}&distance={3}&limit={4}&fields=id&access_token={5}'.format(
                self.keyword,
                lat, lon,
                self.scan_radius,
                self.limit,
                self.token)).json()
        pages_id_list = [i['id'] for i in pages_id['data']]
        while 'paging' in pages_id and 'next' in pages_id['paging']:
            pages_id = requests.get(pages_id['paging']['next']).json()
            for page in pages_id['data']:
                pages_id_list.append(page.get('id', None))
        return pages_id_list

    def events_from_page_id(self, page_id):
        try:
            params = {
                'ids': page_id,
                'fields': 'events.fields(id,name,start_time,description,place,type,category,ticket_uri,cover.' +
                          'fields(id,source),picture.type(large),attending_count,declined_count,maybe_count,' +
                          'noreply_count).since({0}),id,name,cover.fields(id,source),picture.type(large),location'.format(
                              int(time.time())),
                'access_token': self.token,
            }
            events = requests.get('https://graph.facebook.com/v2.8/', params=params)
            return events.json()
        except Exception as e:
            print(e)
            return None

    def event_to_model(self, event_dict):
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

    def generate_token(self):
        return requests.get(
            'https://graph.facebook.com/v2.8/oauth/access_token?' +
            'client_id={0}&client_secret={1}&&grant_type=client_credentials'
            .format(self.client_id, self.client_secret)).json()['access_token']

    def get_coords(self):
        geolocator = Nominatim()
        location = geolocator.geocode(self.city)
        return location.latitude, location.longitude  # lat/lon

    def process_events(self):
        i = 0
        for point in self.generate_coordinates(*self.get_coords()):
            for page_id in self.get_page_ids(point[0], point[1]):
                if page_id:
                    page_events = self.events_from_page_id(page_id)[page_id]
                    if page_events and 'events' in page_events:
                        for event in page_events['events']['data']:
                            self.event_to_model(event)
                        i += 1
                    print('Processed {} pages with events...'.format(i))
                if i >= self.pages_max:
                    print('processed >=max pages, stopping...')
                    print(db.session.new)
                    db.session.commit()
                    self._exit()

        db.session.commit()

    def _exit(self):
        sys.exit(0)

if __name__ == '__main__':
    with open('config.json', 'r') as f:
        args = json.load(f)
    s = Scanner(args['client_id'], args['client_secret'], args['scan_radius'], args['city'], args['radius'],
                keyword=args['keyword'], pages_max=args['pages_max'], limit=args['limit'])
    s.process_events()
