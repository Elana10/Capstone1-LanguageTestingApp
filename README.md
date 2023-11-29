Hello the student!

## **Overview**
This application is for *further* education for any language learners! It is a platform where users can signup and view story translations from a number of languages, currently English, Spanish, German, Arabic, French, Italian, Portuguese, Farsi, Japanese, Chinese. 

The stories are presented one sentence at a time in the "base language" with a randomized word bank for the "foreign language" presented as options. The user will click on the word bank to build the foreign language sentence. If the word is correct it will turn green and the foreign language sentence will start building above it with each successive correct word adding on to the sentence. 

Once a sentence has been correctly built in the foreign language and audio play button will appear to allow users to hear the sentence in the foreign language. If there is another sentence in the story it populates below and the user continues until there are no more sentences. 

Users complete translated stories submitted by other individuals or have the option to add their own stories to the database. 

## **FEATURES**
You can sort and filter stories by languages, length, scores, attepmts. 

As a user you can track all of your story translating attempts. 

The API for creating translations is Chat GPT which charges via tokens. Users can track how many tokens they've used to create their translated stories. Chat GPT does not currently return audio token usage. 

## **TECHNOLOGY STACK**
I tried to work in every language I have learned to date through the Springboard Bootcamp - as such the code is redundant in areas. 

For example, the inital load of the html home page when logged in creates information blocks based on flask and jinja2. When the sort or filter options are used on the table, I use javascript AJAX requests to python to fetch the information blocks and then javascript DOM Manipulation to load the fetched information blocks. Normally I would not want to create a duplication of effort to load the table - ie I would have javascript make all objects, but that would have eliminated an opportunity to display jinja2 capabilities. 

Knowing that not all of these coding languages were needed to write this application, I can still report using:
- python
- javascript
- html
- css
- bootstrap
- AJAX
- SQLAlchemy
- flask
- jinja2

## **FURTHER STUDY**
As this is a timed project there are some features that have been left for a later date. 
1) Testing files
2) Organization of the app.py file and parsing code to serparate files to reduce clutter
3) Add admin users as the only ones that can generate new stories with the Chat GPT requests. 
4) Add a grammar check library and form requirement to the story submission. 
5) Update the User profile pages for sorting and filtering. 
6) Allow editing of translated sentences (hopefully by vetted native speakers)

## **Setup**
Create the Python virtual environment:
  :class: console

  $ python3 -m venv venv
  $ source venv/bin/activate
  (venv) $ pip install -r requirements.txt