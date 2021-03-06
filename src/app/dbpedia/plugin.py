"""

Module:    plugin.py
Author:    Rinke Hoekstra
Created:   2 October 2012

Copyright (c) 2012, Rinke Hoekstra, VU University Amsterdam 
http://github.com/Data2Semantics/linkitup

"""
from flask import render_template, session
from flask.ext.login import login_required

import re

from app import app
from app.util.baseplugin import SPARQLPlugin

@app.route('/dbpedia/<article_id>')
@login_required
def link_to_wikipedia(article_id):
    app.logger.debug("Running DBPedia plugin for article {}".format(article_id))


    # Retrieve the article from the session
    article = session['items'][article_id]
    
    # Rewrite the tags and categories of the article in a form understood by utils.baseplugin.SPARQLPlugin
    article_items = article['tags'] + article['categories']
    match_items = [{'id': item['id'], 
                    'label': re.findall('^.*?\=(.*)$',item['name'])[0] if item['name'].lower().startswith('inchikey=') else item['name']} 
                   for item in article_items]
    
    try :
        # Initialize the plugin
        plugin = SPARQLPlugin(endpoint = "http://dbpedia.org/sparql",
                          template = "dbpedia.query",
                          rewrite_function = lambda x: re.sub('dbpedia.org/resource','en.wikipedia.org/wiki',x),
                          id_function = lambda x: re.sub('http://dbpedia.org/resource/','',x),
                          id_base = 'uri')
        
        # Run the plugin, and retrieve matches using the default label property (rdfs:label)
        matches = plugin.match(match_items)
        # Run the plugin with a specific property for the InchiKeys (namespace is defined in the dbpedia.query template)
        matches.extend(plugin.match(match_items, property="dbpprop:inchikey"))
        
        # Add the matches to the session
        session.setdefault(article_id,[]).extend(matches)
        session.modified = True
    
        if matches == [] :
            matches = None
        
        # Return the matches
        return render_template('urls.html',
                               article_id = article_id, 
                               results = [{'title':'Wikipedia','urls': matches}])
        
    except Exception as e:
        return render_template( 'message.html',
                                type = 'error', 
                                text = e.message )
    

