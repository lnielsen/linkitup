"""

Module:    views.py
Author:    Rinke Hoekstra
Created:   24 October 2012

Copyright (c) 2012, Rinke Hoekstra, VU University Amsterdam 
http://github.com/Data2Semantics/linkitup

The Django Views module for Linkitup

This module responds to the HTTP requests to URLs matching the patterns specified in the :mod:`urls` module.

"""

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
import requests
from oauth_hook import OAuthHook
from requests_oauthlib import OAuth1
import json
import yaml


from util.figshare import get_auth_url, validate_oauth_verifier, get_articles, update_article
from util.rdf import get_rdf



PLUGINS_FILE = "/Users/hoekstra/projects/data2semantics/linkitup/src/plugins.yaml"
# PLUGINS_FILE = "/var/www/linkitup.data2semantics.org/src/plugins.yaml"

def index(request):
    """This function generates the landing page for Linkitup (it is called for requests to the base URL of the application)"""
    
    return render_to_response('landing.html')
    
def dashboard(request):
    """If this session has not yet been initialized (i.e. we don't yet have an oauth_token from Figshare), 
    it starts up the three-legged authentication procedure for OAuth v1.
    
    Otherwise, it initializes the session variable with the article details of the Figshare author
    
    """
    if request.session.get('oauth_token',None) == None :
        """We do not yet have an oauth_token, so redirect to the authorization page"""
        
        return HttpResponseRedirect('/authorize')
    else :
        """
        This is where we do two things:
        
        1.    Intialize the plugins specified in `plugins.yaml`.
        
        2.    Once we went through the three legged authorization process, we do have an oauth_token, 
        and use it to retrieve all articles of the Figshare author who provided the authentication.
        """
        
        try :
            plugins = yaml.load(open(PLUGINS_FILE,'r'))
            
            map(__import__, plugins.keys())
        except Exception as e :
            return render_to_response('error.html',{'message': e.message })
        
        try :
            results = get_articles(request)
        except Exception as e :
            return render_to_response('error.html',{'message': e.message })
        

        return render_to_response('articles.html',{'raw': str(results),'results': results, 'plugins': plugins.values()},context_instance=RequestContext(request))
 
def authorize(request):
    """ Gets the oauth request authorization URL from the figshare API,
    and renders the form for filling in the PIN code (the oauth verifier)
        
    NB: do not confuse the oauth_token with the oauth_request_token! The request token is needed to request the actual oauth_token.
    """
    try:
        oauth_request_auth_url = get_auth_url(request)
    
        return render_to_response('allow_application.html',{'authorize_url': oauth_request_auth_url},context_instance=RequestContext(request))
    except Exception as e:
        return render_to_response('error.html',{'message': e.message })
        
    
def validate(request):
    """ Validates the PIN code provided by the user in the authorization web form,
    and gets the oauth token and secret."""
    
    oauth_verifier = request.POST['pin']
     
    try:
        validate_oauth_verifier(request, oauth_verifier)
        return HttpResponseRedirect('/dashboard')
    except Exception as e:
        return render_to_response('error.html',{'message': e.message })
    



def process(request, article_id):
    if request.POST['task'] == "Download RDF" :
        print "Going to download RDF"
        return rdf(request,article_id)
    elif request.POST['task'] == "Add to Figshare":
        print "Adding to Figshare"
        return update(request,article_id)
    else:
        return render_to_response('error.html',{'message': "No idea what you meant ..." })





def rdf(request, article_id):
    checked_urls = request.POST.getlist('url')
    
    g = get_rdf(request, article_id, checked_urls)

    graph = g.serialize(format='turtle')
    response = HttpResponse(graph, content_type = 'text/turtle')
    response['Content-Disposition'] = 'attachment; filename={}.ttl'.format(article_id)
    return response




def update(request, article_id):
    checked_urls = request.POST.getlist('url')
    article_urls = request.session.get(article_id,[])
    
    update_article(request, article_id, article_urls, checked_urls)
            
    # Reset the URLs generated by the application
    request.session[article_id] = []
    request.session.modified = True
    
    return HttpResponseRedirect('/')




    

    
def clear(request):
    request.session.clear()
    
    return render_to_response('warning.html',{'message':'Session data cleared!'})
