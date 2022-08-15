# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys
from time import strftime

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from datetime import date
from models import Venue, Artist, Show, db


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    areas = []
    groupedarea = Venue.query.distinct('state', 'city').order_by('state').all()
    for venue in groupedarea:
        venuecity = venue.city
        venuestate = venue.state
        data = {
            'city': venue.city,
            'state': venue.state,
            'venues': []
        }
        areas.append(data)

        insidevenues = venue.query.filter_by(state=venuestate, city=venuecity)
        for singlevenue in insidevenues:
            query = singlevenue.query.join('shows').filter(Venue.id == singlevenue.id, Show.start_time > date.today())
            num_upcoming_shows = query.count()
            singlevenue = {
                'id': singlevenue.id,
                'name': singlevenue.name,
                'num_upcoming_shows': num_upcoming_shows,
            }
            data['venues'].append(singlevenue)

    return render_template('pages/venues.html', areas=areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    search = f"%{search_term}%"
    search_query = Venue.query.filter(Venue.name.ilike(search))
    search_count = search_query.count()

    response = {
        "count": search_count,
        "data": search_query
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    venue_show = Show.query.filter_by(venue_id=venue_id).all()
    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "address": venue.address,
        "state": venue.state,
        "phone": venue.phone,
        "image_link": venue.image_link,
        "website": venue.website,
        "genres": venue.genres,
        "facebook_link": venue.facebook_link,
        "seeking_description": venue.seeking_description,
        "seeking_talent": venue.seeking_talent,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    if venue_show:
        for show in venue_show:
            if show.start_time > datetime.now():
                artist = Artist.query.get(show.artist_id)
                upcoming = {
                    "artist_id": show.artist_id,
                    "artist_name": artist.name,
                    "artist_image_link": artist.image_link,
                    "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                data["upcoming_shows"].append(upcoming)
                data["upcoming_shows_count"] = +1

            else:
                artist = Artist.query.get(show.artist_id)
                past = {
                    'artist_id': show.artist_id,
                    'artist_name': artist.name,
                    'artist_image_link': artist.image_link,
                    'start_time': show.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                data["past_shows"].append(past)
                data["past_shows_count"] = +1

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    error = False
    form = VenueForm(request.form)
    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=request.form.getlist('genres'),
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('Sorry. Venue ' + request.form['name'] + ' is not posted.')
    else:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    search = f"%{search_term}%"
    search_query = Artist.query.filter(Artist.name.ilike(search))
    search_count = search_query.count()

    response = {
        "count": search_count,
        "data": search_query
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    artist_show = Show.query.filter_by(artist_id=artist_id).all()
    data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "image_link": artist.image_link,
        "genres": artist.genres,
        "facebook_link": artist.facebook_link,
        "website": artist.website_link,
        "seeking_description": artist.seeking_description,
        "seeking_venue": artist.seeking_venue,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    if artist_show:
        for show in artist_show:
            if show.start_time > datetime.now():
                venue = Venue.query.get(show.venue_id)
                upcoming = {
                    "venue_id": show.venue_id,
                    "venue_name": venue.name,
                    "venue_image_link": venue.image_link,
                    "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                data["upcoming_shows"].append(upcoming)
                data["upcoming_shows_count"] = +1

            else:
                venue = Venue.query.get(show.venue_id)
                past = {
                    "venue_id": show.venue_id,
                    "venue_name": venue.name,
                    "venue_image_link": venue.image_link,
                    "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                data["past_shows"].append(past)
                data["past_shows_count"] = +1
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(
        name=artist.name,
        genres=artist.genres,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        website_link=artist.website_link,
        facebook_link=artist.facebook_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        image_link=artist.image_link
    )
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form)
    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = request.form.getlist("genres")
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website_link = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' is not be updated.')
    else:
        flash('Artist ' + request.form['name'] +
              ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue = Venue.query.get(venue_id)
    form = VenueForm(
        name=venue.name,
        genres=venue.genres,
        address=venue.address,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        website=venue.website,
        facebook_link=venue.facebook_link,
        seeking_talent=venue.seeking_talent,
        seeking_description=venue.seeking_description,
        image_link=venue.image_link
    )
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form)

    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.address = form.address.data
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. venue ' +
              request.form['name'] + ' is not be updated.')
    else:
        flash('venue ' + request.form['name'] +
              ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)
    error = False
    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=request.form.getlist("genres"),
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('Sorry. artist ' + request.form['name'] + ' is not posted.')
    else:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. artist ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    venues_shows = Venue.query.join('shows')
    for venue in venues_shows:
        for show in venue.shows:
            artist = Artist.query.get(show.artist_id)
            showdata = {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")

            }
            data.append(showdata)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    try:
        show = Show(
            artist_id=request.form['artist_id'],
            venue_id=request.form['venue_id'],
            start_time=request.form['start_time']
        )
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('Sorry. Show ' + 'New show' + ' is not posted.')
    else:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash(' New Show ' + ' was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
