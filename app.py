import os
import re
import openai
import json
import ast
import random
import math
from openai import OpenAI
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime
# from secret import secret_key


from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, text, func
 
from models import db, connect_db, User, Story, StorySentence, Scores
from forms import NewUserForm, NewStoryForm, Login

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgresql:///translate_db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "I'LL NEVER TELL!!"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# Having the Debug Toolbar show redirects explicitly is often useful;
# however, if you want to turn it off, you can uncomment above line.
debug = DebugToolbarExtension(app)

app.app_context().push()
# ACCESS FLASK WITHIN IPYTHON AND HAVE SESSIONS

connect_db(app)
db.create_all()
if app.config["ENV"] == "development":
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

client = OpenAI(
    api_key = (secret_key)
)

openai.api_key = secret_key

 
#########################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If the user is logged in, then add current user to Flask global.
    The before request checks the session and assigns it the to global variable g, BEFORE and request methods are used."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

###########################################################
# View routes for login/signup/logout

@app.route('/')
def home_page():
    """ Show list of stories or login page. """

    if g.user:
        stories = Story.query.all()
        return render_template('home.html', stories= stories)
    else:
        return render_template('home-anon.html')

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    """Handle user signup. 
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If there are issues with submission present form with flash message to correct errors."""

    form = NewUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        new_user = User.signup(username = username.upper(), email = email, password = password)
        
        db.session.commit()
        do_login(new_user)

        flash(f"New user {new_user.username} registered!", "success")
        return redirect('/')
    
    return render_template('form_signup.html', form=form)

@app.route('/login', methods = ['POST', 'GET'])
def login_user():
    """Directs to a for for login OR if valid submission processes the login."""
    do_logout()
    form = Login()

    if form.validate_on_submit():
        username = form.username.data
        user = User.authenticate(username = username.upper(), password = form.password.data)

        if user: 
            do_login(user)
            flash(f"Welcome back, {user.username}", "success")
            return redirect('/')
        
        flash(f"Invalid credentials", "danger")

    return render_template('form_login.html', form =form)

@app.route('/logout')
def logout_user():
    """Handle user logout."""
    do_logout()
    flash("Success! You have been logged out.", "success")
    return redirect('/')

#############################################################
# View Routes with render template.

@app.route('/story/<int:id>', methods = ['GET'])
def load_story_to_solve(id):
    """GET: Load the story translation page.
    POST: Change the story translation page with AJAX through app.js"""

    if not g.user:
        flash("Please Sign In To Access Website Content.", "danger")
        return redirect('/') 
        
    session['current_story'] = id
    story = Story.query.get_or_404(id)

    return render_template('solve-story.html', story=story)

@app.route('/story/new', methods = ['GET', 'POST'])
def create_new_story():
    """Create a new story translation for the platform. Enter your base text, and send the API request to google to translate. Store the story and translation in the database. """
    
    if not g.user:
        flash("Please Sign In To Access Website Content.", "danger")
        return redirect('/') 
    
    form = NewStoryForm()
    if form.validate_on_submit():
        title = form.title.data
        translate_text = form.translate_text.data
        foreign_lang = form.foreign_lang.data
        base_lang = form.base_lang.data
        # user_id = g.user.id

        new_story = Story(
            user_id = g.user.id,
            base_language = base_lang,
            foreign_language = foreign_lang,
            title = title,
        )
        db.session.add(new_story)
        db.session.commit()        

        create_story_sentences(translate_text, base_lang, foreign_lang, new_story.id)

        return redirect(f'/story/{new_story.id}')

    return render_template('form_new_story.html', form=form)

@app.route('/users/<int:id>')
def load_user_page(id):
    user = User.query.get_or_404(id)
    return render_template('user_page.html', user = user)

@app.route('/users/<int:id>/stats')
def view_user_stats(id):
    """See user stats"""
    # stories = Story.query.join(Scores).filter(Scores.user_id == id).all()
    stories = Scores.query.join(Story).filter(Scores.user_id ==id).all()

    return render_template('user_stats.html', stories = stories)

@app.route('/users/<int:id>/my_stories')
def load_all_user_stories(id):
    """Return the stories you've created - eventually add editing feature"""
    stories = Story.query.filter_by(user_id = id).all()

    return render_template('/user_stories.html', stories = stories)

@app.route('/users/<int:id>/update')
def update_user_information(id):
    """Update user information."""
    user = User.query.get_or_404(id)
    user_token_sum = (
        db.session.query(func.sum(StorySentence.tokens).label('total_tokens'))
        .join(Story)
        .join(User)
        .filter(User.id == user.id)
        .all()
    )

    return render_template('/user_update.html', user=user, tokens = user_token_sum)


#############################################################
# AJAX for creating and completing story game

@app.route('/load_sentences')
def load_sentence_object_for_AJAX_manipulation():
    """Sends app.js a json response with data needed to populate the story translation."""
    story_sent_list = StorySentence.query.filter(StorySentence.story_id == session['current_story']).order_by(StorySentence.id)
    foreign_lang = story_sent_list[0].foreign_language

    sentences_list = [{'base_sentence': s.base_sentence, 
                  'translated_sentence_list':   create_list_of_words_from_sentence(
                      s.translated_sentence),
                  'random_translated_sentence_list': randomize_word_list(create_list_of_words_from_sentence(
                      s.translated_sentence.lower())
                  ),
                  'translated_sentence' : s.translated_sentence
                  } for s in story_sent_list]
    
    session['points'] = 0
    session['total_points'] = 0 
    session['current_sentence'] = 0
    session['current_word'] = 0  
    session['sentences_list'] = sentences_list
    session['story_id'] = session['current_story']
    session['foreign_language'] = foreign_lang

    return jsonify({'sentences_list' :sentences_list,
                    'total_points' : 0})

@app.route('/check_correctness', methods = ['POST'])
def check_that_the_correct_word_is_selected():
    """Check if the correct word span was selected."""
    sentences_list = session['sentences_list']
    current_word = int(session['current_word'])
    data = request.json
    guess = data.get('guess')
    sentence = int(data.get('sentence'))
    word = sentences_list[sentence]['translated_sentence_list'][current_word]
    word_lower = word.lower()
    points_earned = session['points']
    total_points = session['total_points']

    if word_lower == guess:
        try:
            word_next = sentences_list[sentence]['translated_sentence_list'][current_word + 1]
            session['current_word'] = current_word + 1
            session['points'] = points_earned + 1
            session['total_points'] = total_points + 1

            return jsonify({'sentence_end': False,
                            'next_sentence_id' : sentence,
                            'word_correct': True,
                            'word_id' : current_word,
                            'word_text' : word,
                            'points' :session['points'],
                            'total_points' : session['total_points']
                            })
        except:
            try:
                sentence_next = sentences_list[sentence+1]
                session['current_sentence'] = sentence + 1
                session['current_word'] = 0
                session['points'] = points_earned + 1
                session['total_points'] = total_points + 1

                return jsonify({'sentence_end': True,
                                'next_sentence_id' : sentence + 1,
                                'word_correct': True,
                                'word_id' : current_word,
                                'word_text' : word,
                                'points' :session['points'],
                                'total_points' : session['total_points']
                                })
            except:
                session['points'] = points_earned + 1
                session['total_points'] = total_points + 1                
                return jsonify({'sentence_end' : True,
                               'next_sentence_id' : False,
                               'word_correct' : True,
                               'word_id' : current_word,
                               'word_text': word,
                               'points' :session['points'],
                               'total_points': session['total_points']})  
    
    session['points'] = points_earned + 1

    return jsonify({'sentence_end': False,
                    'next_sentence_id' : sentence,
                    'word_correct': False,
                    'word_id' : False,
                    'word_text' : word,
                    'points' : session['points'],
                    'total_points' :session['total_points']
                    })

@app.route('/save_score', methods = ['POST'])
def save_the_user_story_score():
    score =session['points']
    total_points = session['total_points']
    user_id = g.user.id
    created_at = datetime.now()
    story_id = session['story_id']  
    try:
        score_decimal = round(total_points/score, 4)
        score_percent = (score_decimal*100)

    except:
        score_percent = 0

    new_score = Scores(user_id = user_id, 
                       story_id = story_id,
                       score = score_percent,
                       created_at = created_at)
    
    db.session.add(new_score)
    db.session.commit()

    return jsonify({'score': score_percent})

###############################################################
#Supporting AJAX Functions for story game

def create_word_list(sentence):
    """Returns an in order words list of a sentence."""
    word_list = re.findall(r'\w+' , sentence)
    word_list = [(index,word) for index, word in enumerate(word_list)]
    return word_list

def randomize_word_list(word_list):
    random.shuffle(word_list)
    return word_list

def create_list_of_words_from_sentence(sentence):
    """Creates a list of words based on the sentence."""
    word_list = re.findall(r'\w+' , sentence)
    return word_list

############################################################
# CHATGPT API Requests

def translate_sentence_API_function(sentence, base_lang, foreign_lang):
    """ Send out a ChatGPT API request for sentence translations. """

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", 
            "content": f"Translate the 'user' role 'content' from {base_lang} to {foreign_lang} while ignoring multiple spaces."},
            {"role": "user", 
            "content": sentence}
        ]
    )
    tokens = completion.usage.total_tokens

    try:
        translated_sentence = json.loads('"' + completion.choices[0].message.content + '"')
    except json.decoder.JSONDecodeError as e:         
        string = completion.choices[0].message.content
        no_quotes = string.replace('"','`') 
        translated_sentence = json.loads('"' + no_quotes  + '"')       

    return (translated_sentence, tokens)

@app.route('/play_sentence', methods =['POST'])
def generate_and_play_audio():
    id = request.json.get('sentence_id', None)

    sentence = session['sentences_list'][int(id)]['translated_sentence']
    story_id = session['story_id']
    foreign_lang = session['foreign_language']

    audio_folder = Path(__file__).parent /"static/audio"
    speech_file_path = audio_folder / f"speech-story{story_id}sentence{id}.mp3"

    response = client.audio.speech.create(
        model = "tts-1",
        voice="alloy",
        input= sentence,
        speed=.9, 
    )

    response.stream_to_file(speech_file_path)

    return jsonify({'audio_url': f"/static/audio/speech-story{story_id}sentence{id}.mp3"})

#############################################################
# Supporting CHATGPT API functions for processing data for SQL Storage

def separate_to_sentences(translate_text):
    """ Takes the user input text and breaks it into sentences. """
    sentence_structure = r'(?<=[.!?])\s+'
    translate_text = translate_text.strip()

    return re.split(sentence_structure, translate_text)

def lower_case_and_no_punctuation(sentence):
    """Remove puncutation and caps for easy comparison and processing for list of sentences."""
    sentence = sentence.lower()
    sentence = sentence[:-1]
    sentence = f' {sentence} '
    result = re.sub('"', "", sentence)  
    result2 = re.sub("'","", result)  
    
    return result2

def lower_case_and_spacing_string(sentence):
    """ Remove punctuation and caps for easy comparison and processing for one string. """
    sentence = sentence.lower()
    sentence = f' {sentence} '
    result = re.sub('"', "", sentence)  
    result2 = re.sub("'","", result)  
    
    return result2

def create_story_sentences(translate_text, base_lang, foreign_lang, story_id):
    """ Make sentences in database - store base_sentence and translated_sentence """
    clean_text = re.sub(r'[\r\n\t\x00-\x1F\x7F-\x9F]', ' ', translate_text)
    # clean_translate_text = ''.join(char for char in translate_text if 32 <= ord(char) < 127)
    sentence_list = separate_to_sentences(clean_text)

    for sentence in sentence_list:
        # cleaned_sentence = re.sub(r'[\r\n\t\x00-\x1F\x7F-\x9F]', ' ', sentence)
        translated, token_count_sentence = translate_sentence_API_function(sentence, base_lang, foreign_lang)
        # base_tuple, foreign_tuple, token_count_words = create_direct_word_translations(sentence, translated, base_lang, foreign_lang)

        new_story_sentence = StorySentence(
            story_id = story_id,
            base_language = base_lang,
            foreign_language = foreign_lang,
            base_sentence = sentence,
            translated_sentence = translated,
            # base_tuple = json.dumps(base_tuple),
            # foreign_tuple = json.dumps(foreign_tuple),
            tokens = token_count_sentence,
        )

        db.session.add(new_story_sentence)
        db.session.commit()

###############################################################
#Home page AJAX functions to support table sorting and filtering

@app.route('/sort_table', methods = ['GET'])
def query_for_sorted_element():
    """Query SQL for story list sorting by 'method' add filtering by language."""
    base_lang = request.args.get('base_lang')
    foreign_lang = request.args.get('foreign_lang')
    already_sorted = request.args.get('already_sorted')
    sortBy = request.args.get('sortBy')
    column_sorted = getattr(Story, sortBy)

    if already_sorted:
        if base_lang == 'all' and foreign_lang == 'all':
            stories = Story.query.order_by(column_sorted).all()
            i = len(stories)
            stories_sort = []
            while(i):
                stories_sort.append(stories[i-1])
                i = i-1            
        elif base_lang == 'all':
            stories = Story.query.filter_by(foreign_language = foreign_lang).order_by(column_sorted).all()
            i = len(stories)
            stories_sort = []
            while(i):
                stories_sort.append(stories[i-1])
                i = i-1  
        elif foreign_lang == 'all':
            stories = Story.query.filter_by(base_language = base_lang).order_by(column_sorted).all()
            i = len(stories)
            stories_sort = []
            while(i):
                stories_sort.append(stories[i-1])
                i = i-1              
        else:
            stories = Story.query.filter_by(base_language = base_lang, foreign_language = foreign_lang).order_by(column_sorted).all()
            i = len(stories)
            stories_sort = []
            while(i):
                stories_sort.append(stories[i-1])
                i = i-1              

    else:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.order_by(column_sorted).all()
        elif base_lang == 'all':
            stories_sort = Story.query.filter_by(foreign_language = foreign_lang).order_by(column_sorted).all()
        elif foreign_lang == 'all':
            stories_sort = Story.query.filter_by(base_language = base_lang).order_by(column_sorted).all()     
        else:
            stories_sort = Story.query.filter_by(base_language = base_lang, foreign_language = foreign_lang).order_by(column_sorted).all()             

    serialized_stories = serialize_story_list(stories_sort)
    return jsonify({'stories':serialized_stories})  

@app.route('/load_table_all', methods = ['GET'])
def reload_the_whole_table():
    """Load the whole stories table and remove filtering and sorting."""
    stories = Story.query.all()
    serialized_stories = serialize_story_list(stories)
    return jsonify({'stories':serialized_stories})

@app.route('/filter_by_language', methods = ['GET'])
def fitler_stories_by_languages():
    """Return a filtered JSON list of languages. """
    base_lang = request.args.get('base_lang', False)
    foreign_lang = request.args.get('foreign_lang', False)

    if foreign_lang == 'all':
        stories_filtered = Story.query.filter_by(base_language = base_lang).all()
    elif base_lang == 'all':
        stories_filtered = Story.query.filter_by(foreign_language = foreign_lang).all()
    else:
        stories_filtered = Story.query.filter_by(base_language = base_lang, foreign_language = foreign_lang).all()

    serialized_stories = serialize_story_list(stories_filtered)
    return jsonify({'stories':serialized_stories}) 

@app.route('/orderby_sentence_count')
def filter_and_order_by_sentence_count():
    """Considers language filtering to create order by sentence count, asc or desc"""
    base_lang = request.args.get('base_lang')
    foreign_lang = request.args.get('foreign_lang')
    already_sorted = request.args.get('already_sorted')

    if already_sorted:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(StorySentence).group_by(Story.id).order_by(func.count((StorySentence.story_id)).desc()).all()
        
        elif base_lang == 'all':
            stories_sort = Story.query.join(StorySentence).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id)).desc()).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(StorySentence).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id)).desc()).all()

        else:
            stories_sort = Story.query.join(StorySentence).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id)).desc()).all()          

    else:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(StorySentence).group_by(Story.id).order_by(func.count((StorySentence.story_id))).all()

        elif base_lang == 'all':
            stories_sort = Story.query.join(StorySentence).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id))).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(StorySentence).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id))).all()  
        else:
            stories_sort = Story.query.join(StorySentence).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((StorySentence.story_id))).all()                

    serialized_stories = serialize_story_list(stories_sort)
    return jsonify({'stories':serialized_stories})  

@app.route('/orderby_attempts')
def story_list_sorted_by_Scores_joins_count_attempts():
    """Create story list by scores table joins count or max - asc or desc  """
    base_lang = request.args.get('base_lang')
    foreign_lang = request.args.get('foreign_lang')
    already_sorted = request.args.get('already_sorted')

    if already_sorted:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).group_by(Story.id).order_by(func.count((Scores.story_id)).desc() if Scores else None).all()
        
        elif base_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((Scores.story_id)).desc() if Scores else None).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.count((Scores.story_id)).desc() if Scores else None).all()

        else:
            stories_sort = Story.query.outerjoin(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count((Scores.story_id)).desc() if Scores else None).all()          

    else:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).group_by(Story.id).order_by(func.count(Scores.story_id) if Scores else None).all()

        elif base_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count(Scores.story_id) if Scores else None).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.outerjoin(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.count(Scores.story_id) if Scores else None).all()  
        else:
            stories_sort = Story.query.outerjoin(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.count(Scores.story_id) if Scores else None).all()                

    serialized_stories = serialize_story_list(stories_sort)
    return jsonify({'stories':serialized_stories})  

@app.route('/orderby_highest_score')
def order_table_by_score_values():
    """Returns sort list of highest scores overall or by logged in user, asc or desc"""
    base_lang = request.args.get('base_lang')
    foreign_lang = request.args.get('foreign_lang')
    already_sorted = request.args.get('already_sorted')

    if already_sorted:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()
        
        elif base_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()

        else:
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()          

    else:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).group_by(Story.id).order_by(func.max(Scores.score)).all()

        elif base_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()  
        else:
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()                

    serialized_stories = serialize_story_list(stories_sort)
    return jsonify({'stories':serialized_stories})  

@app.route('/orderby_user_score')
def order_table_by_users_scores():
    """Return a list of stories order by the user's high scores - desc and asc."""
    base_lang = request.args.get('base_lang')
    foreign_lang = request.args.get('foreign_lang')
    already_sorted = request.args.get('already_sorted')
    user = g.user.id

    if already_sorted:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Scores.user_id == user).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()
        
        elif base_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()

        else:
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score).desc()).all()          

    else:
        if base_lang == 'all' and foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Scores.user_id == user).group_by(Story.id).order_by(func.max(Scores.score)).all()

        elif base_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()

        elif foreign_lang == 'all':
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()  
        else:
            stories_sort = Story.query.join(Scores).filter(Story.base_language == base_lang, Story.foreign_language == foreign_lang).group_by(Story.id).order_by(func.max(Scores.score)).all()                

    serialized_stories = serialize_story_list(stories_sort)
    return jsonify({'stories':serialized_stories})  

################################################################
#Supporting AJAX Function for Home page sorting and filtering

def serialize_story_list(stories_sort):
    """Creates a JSON object to return to javascript from axios requests."""
    serialized_stories = []    
    for story in stories_sort:
        max_score = Scores.query.filter(Scores.story_id == story.id).order_by(Scores.score.desc()).first()
        user_max_score = Scores.query.filter(Scores.story_id == story.id, Scores.user_id == g.user.id).order_by(Scores.score.desc()).first()

        serialized_story = {'base_language':story.base_language,
                           'foreign_language':story.foreign_language,
                           'sentences':len(story.sentences),
                           'attempts':len(story.scores),
                           'max_score': (lambda: max_score.score if max_score else 0)(),
                           'user_max_score': (lambda: user_max_score.score if user_max_score else 0)(),
                           'id':story.id,
                           'title':story.title}
        
        serialized_stories.append(serialized_story)
    return serialized_stories
