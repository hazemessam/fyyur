#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format,locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  """ Get all venues """
  areas_query = Venue.query.with_entities(Venue.city, Venue.state).order_by(Venue.city).all()
  areas = set(areas_query)
  data = []
  for area in areas:
    venues = Venue.query.filter(Venue.city == area[0]).filter(Venue.state == area[1]).all()
    data.append({
      "city": area[0],
      "state": area[1],
      "venues": [{"id": venue.id, "name": venue.name} for venue in venues]
    })
  
  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  """ Search for venues using search term """

  search_term = request.form.get('search_term', '')
  search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(search_result),
    "data": [{"id": venue.id, "name": venue.name} for venue in search_result]
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  """ Get a spesific venue by its id """
  
  venue = Venue.query.get(venue_id)

  if not venue: 
    return render_template('errors/404.html')

  past_shows_query = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time < datetime.now()).all()
  past_shows = []
  for show in past_shows_query:
    artist = Artist.query.get(show.artist_id)
    past_shows.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_shows_query = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    artist = Artist.query.get(show.artist_id)
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "image_link": venue.image_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  """ Get create venue form """

  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  """ Create new venue """

  error = False
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_talent = bool(request.form.get('seeking_talent', False))
    seeking_description = request.form['seeking_description']
    
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()

  if error: 
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  else: 
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  """ Delete a venue using its id """

  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(e)
  finally:
    db.session.close()

  if error: 
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  if not error: 
    flash(f'Venue {venue_id} was successfully deleted.')
  
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
  """ Get all artists """

  data = Artist.query.order_by(Artist.name).all()

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  """" Search for artists using search term """
  

  search_term = request.form.get('search_term', '')
  search_result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(search_result),
    "data": [{"id": artist.id, "name": artist.name} for artist in search_result]
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  """ Get artist by its id """

  artist = Artist.query.get(artist_id)

  if not artist: 
    return render_template('errors/404.html')

  past_shows_query = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time < datetime.now()).all()
  past_shows = []
  for show in past_shows_query:
    venue = Venue.query.get(show.venue_id)
    past_shows.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_shows_query = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    venue = Venue.query.get(show.venue_id)
    upcoming_shows.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  """" Get edit artist form """
  
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  """ Edit artist information by its id """

  error = False  
  try: 
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = bool(request.form.get('seeking_venue', False)) 
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()

  if error: 
    flash('An error occurred. Artist could not be changed.')
  else: 
    flash('Artist was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  """ Get edit venue form """

  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  """ Edit venue information by its id"""

  error = False  
  try: 
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = bool(request.form.get('seeking_talent', False))
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()

  if error: 
    flash(f'An error occurred. Venue could not be changed.')
  else: 
    flash(f'Venue was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  """ Get craete artist form """
  

  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  """ Create new artist """

  error = False
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_venue = bool(request.form.get('seeking_venue', False))
    seeking_description = request.form['seeking_description']

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()

  if error: 
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  else: 
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  """ Get all shows """

  shows_query = Show.query.all()

  data = []
  for show in shows_query: 
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    data.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name, 
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  """ Get create show form """
  

  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """ Create new show """

  error = False
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except Exception as e: 
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()

  if error: 
    flash('An error occurred. Show could not be listed.')
  else: 
    flash('Show was successfully listed')
  return render_template('pages/home.html')
    

@app.errorhandler(404)
def not_found_error(error):
  """ Handle 404 error """
  
  return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
  """ Handle 500 Error """

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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run()
