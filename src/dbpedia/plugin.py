'''
Created on 2 Oct 2012

@author: hoekstra
'''

from SPARQLWrapper import SPARQLWrapper, JSON
from django.shortcuts import render_to_response
import re


def linkup(request, article_id):
    # print article_id
    items = request.session['items']
    # print items
    
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    
    urls = []

    
    for i in items :
        if str(i['article_id']) == str(article_id):
            
            tags_and_categories = i['tags'] + i['categories']
            for tag in tags_and_categories :
                # print tag
                
                t_id = tag['id']
                t_label = tag['name'].strip()
                t_qname = 'FS{}'.format(t_id)

                if t_label.lower().startswith('inchikey=') :
                    t_match = re.findall('^.*?\=(.*)$',t_label)[0]
                    # print t_match
                    
                    q = """
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX dbpprop: <http://dbpedia.org/property/> 
                        SELECT ?s
                        WHERE { 
                            ?s dbpprop:inchikey ?label .
                            ?label bif:contains '\""""+t_match+"""\"' .
                            FILTER (regex(str(?label), '^"""+t_match+"""$', 'i')).
                            FILTER (regex(str(?s), '^http://dbpedia.org/resource')).
                            FILTER (!regex(str(?s), '^http://dbpedia.org/resource/Category:')). 
                            FILTER (!regex(str(?s), '^http://dbpedia.org/resource/List')).
                            FILTER (!regex(str(?s), '^http://sw.opencyc.org/')). 
                        }
                    """
                else :
                    t_match = t_label
                    q = """
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        SELECT ?s
                        WHERE { 
                            ?s rdfs:label ?label .
                            ?label bif:contains '\""""+t_match+"""\"' .
                            FILTER (regex(str(?label), '^"""+t_match+"""$', 'i')).
                            FILTER (regex(str(?s), '^http://dbpedia.org/resource')).
                            FILTER (!regex(str(?s), '^http://dbpedia.org/resource/Category:')). 
                            FILTER (!regex(str(?s), '^http://dbpedia.org/resource/List')).
                            FILTER (!regex(str(?s), '^http://sw.opencyc.org/')). 
                        }
                    """
                sparql.setQuery(q)

                results = sparql.query().convert()
                # print "DBpedia done"
                for result in results["results"]["bindings"]:
                    match_uri = result["s"]["value"]
                    # print match_uri
                    
                    wikipedia_uri = re.sub('dbpedia.org/resource','en.wikipedia.org/wiki',match_uri)
                    
                    short = re.sub('http://dbpedia.org/resource/','',match_uri)
                    # print wikipedia_uri
                    
                    if len(wikipedia_uri) > 61 :
                        show = wikipedia_uri[:29] + "..." + wikipedia_uri[-29:]
                    else :
                        show = wikipedia_uri
                    
                    urls.append({'uri': match_uri, 'web': wikipedia_uri, 'show': show, 'short': short, 'original': t_qname})
                    

    
    
    request.session[article_id] = urls
    
    if urls == [] :
        urls = None 
        
    return render_to_response('urls.html',{'article_id': article_id, 'results':[{'title':'Wikipedia','urls': urls}]})