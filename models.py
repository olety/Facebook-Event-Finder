from __init__ import db


class Place(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(25))
    country = db.Column(db.String(25))
    lat = db.Column(db.Float())
    lon = db.Column(db.Float())
    street = db.Column(db.String(100))
    zip = db.Column(db.String(6))

    def __init__(self, id, name, city, country, lat, lon, street, zip):
        self.id = id
        self.name = name
        self.city = city
        self.country = country
        self.lat = lat
        self.lon = lon
        self.street = street
        self.zip = zip

    def __repr__(self):
        return '<Place {} - {}>'.format(self.id, self.name)

    def __str__(self):
        return '<Place {} - {}>'.format(self.id, self.name)


class Event(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    description = db.Column(db.String(10000))
    name = db.Column(db.String(100))
    picture_url = db.Column(db.String(150))
    ticket_url = db.Column(db.String(150))
    start_time = db.Column(db.DateTime)

    place_id = db.Column(db.String(50), db.ForeignKey('place.id'))
    category = db.relationship('Place', backref=db.backref('events', lazy='dynamic'))

    def __init__(self, id, desc, name, pic_url, tick_url, start_time, place_id):
        self.id = id
        self.description = desc
        self.name = name
        self.picture_url = pic_url
        self.ticket_url = tick_url
        self.start_time = start_time
        self.place_id = place_id

    def __repr__(self):
        return '<Event {} - {}>'.format(self.id, self.name)

    def __str__(self):
        return '<Event {} - {}>'.format(self.id, self.name)
