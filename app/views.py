import random
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from models import *
from pyeviscape.eviscape import *
from pyeviscape.utils import get_unauthorised_request_token, get_authorisation_url, exchange_request_token_for_access_token
from pyeviscape.bitly import BitLy

YOTSUBA = [
    'yotsuba.jpg',
    'yotsuba_berkely.jpg',
    'yotsuba_candy.jpg',
    'yotsuba_city_hall.jpg',
    'yotsuba_dunce_hat.jpg',
    'yotsuba_flower.jpg',
    'yotsuba_icecream.jpg',
    'yotsuba_in_ca.jpg',
    'yotsuba_loving.jpg',
    'yotsuba_meditating.jpg',
    'yotsuba_slice.jpg',
    'yotsuba_the_great.jpg',
    'yotsuba_tomato.jpg',
    'yotsuba_serving.jpg',
    'yotsuba_on_pot.jpg',
    'yotsuba_trek.jpg',
    'yotsuba_tiddles.jpg',
    'yotsuba_three.jpg',
]

def login_required(func):
    """Decorator that redirects to the login page if you're not logged in."""
    def login_wrapper(request, *args, **kwds):
        if request.session.get("member") is None:
            return HttpResponseRedirect("/")
        return func(request, *args, **kwds)
    return login_wrapper

def redirect_if_login(func):
    """Decorator that redirects to the login page if you're not logged in."""
    def login_wrapper(request, *args, **kwds):
        if request.session.get("member"):
            return HttpResponseRedirect("/dashboard")
        return func(request, *args, **kwds)
    return login_wrapper

def respond(request, template, params=None):
    """Helper function for rendering output with common context"""
    params['request'] = request
    params['product'] = 'eviscapelite'
    params['revision'] = '0.1'
    params['stage'] = 'alpha'
    try:
        return render_to_response(template, params)
    #except DeadlineExceededError:
    #    return HttpResponse("DeadlineExceededError")
    except MemoryError:
        logging.exception("MemoryError")
        return HttpResponse("MemoryError")
    except AssertionError:
        logging.exception("Assertion Error")
        return HttpResponse("AssertionError")
        

@redirect_if_login
def auth_request(request):
    unauth = get_unauthorised_request_token()
    token = Token.get_or_push(unauth)
    return HttpResponseRedirect(get_authorisation_url(unauth))

@login_required
def dashboard(request):
    member = request.session.get("member")
    member = User.get_user(member)
    access_token = member.get_token()
    mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
    evis = Evis.timeline(mem, mem.primary_node, access_token)
    return respond(request, "dashboard.html", {'user':member, 'evis':evis, 'listeners':request.session["nod_listener_count"]})


def search(request):
    query = request.GET.get('q', None)
    page = request.GET.get('start', 0)
    if query:
        evis = Evis.search(query, None, 20, page+1)
        rendered = render_to_string('widget_evis.html', { 'evis': evis })
        return HttpResponse(rendered)
    return HttpResponse("fail")
    
@redirect_if_login
def home(request):
    request.session['test'] = "worked"
    request.session.save()
    return respond(request, "home.html", {'image': random.choice(YOTSUBA)})

@login_required
def post(request):
    if request.method == "POST":
        if not request.POST.get("status", False) or not len(request.POST.get("status")):
            return HttpResponse("fail")
        member = request.session.get("member")
        member = User.get_user(member)
        access_token = member.get_token()
        mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
        evis = Evis.post(request.POST.get("status"), request.POST.get("status"),\
                         "chatter", mem, mem.primary_node,\
                         ["eviscapelite"], access_token)
        if evis.id:
            return HttpResponse("ok")
    return HttpResponse("fail")
    
@login_required
def comment_post(request, evi_id):
    if request.method == "POST":
        if not request.POST.get("comment", False) or not len(request.POST.get("comment")):
            return HttpResponse("fail")
        member = request.session.get("member")
        member = User.get_user(member)
        access_token = member.get_token()
        mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
        comment = Comments.post(mem.primary_node, mem, Evis(evi_id, mem.primary_node), request.POST.get("comment"), access_token)
        if comment.id:
            return HttpResponse("ok")
    return HttpResponse("fail")
    
@login_required
def timeline_proxy(request, page):
    member = request.session.get("member")
    member = User.get_user(member)
    access_token = member.get_token()
    mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
    if request.GET.has_key("replies"):
        evis = Evis.timeline(mem, mem.primary_node, access_token, 30, page)
        replies = evis
        evis = []
        for evi in replies:
            if "@%s" % member.nod_name_primary in evi.evi_subject:
                evis.append(evi)
    elif request.GET.has_key("sent"):
        evis = Evis.sent(mem.primary_node, access_token, 10, page)
    else:
        evis = Evis.timeline(mem, mem.primary_node, access_token, 10, page)
    rendered = render_to_string('widget_evis.html', { 'evis': evis })
    return HttpResponse(rendered)
    
    
@login_required
def comment_proxy(request, evi_id):
    member = request.session.get("member")
    member = User.get_user(member)
    access_token = member.get_token()
    mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
    comments = Comments.get(mem.primary_node, Evis(evi_id, mem.primary_node), access_token)
    rendered = render_to_string('widget_comment.html', { 'comments': comments, 'evi_id':evi_id })
    return HttpResponse(rendered)
    

def logout(request):
    request.session.flush()
    return HttpResponseRedirect("/")
    
    
def auth_callback(request):
    oauth_key = request.GET.get('oauth_token', None)
    oauth_verifier = request.GET.get('oauth_verifier', None)
    if oauth_key and oauth_verifier:
        token = Token.get_token_by_key(oauth_key)
        access_token = exchange_request_token_for_access_token(token, oauth_verifier)
        member = Members.get_by_token(access_token)
        user = User.get_or_push(member, access_token)
        user.mem_oauth_token = access_token.key
        user.mem_oauth_secret = access_token.secret
        user.put()
        request.session["member"] = member.mem_name
        request.session["mem_id"] = member.id
        request.session["nod_id_primary"] = member.primary_node.id
        request.session["nod_listener_count"] = member.primary_node.nod_listener_count
        request.session.save()
        return HttpResponseRedirect("/dashboard")
    else:
        return respond(request, "error.html")
        
def api_post(request):
    if request.POST.has_key('jid') and request.POST.has_key('status'):
        jid = request.POST.get('jid').split('-')
        try:
            user, secret_key = tuple(jid)
        except ValueError:
            return HttpResponse('fail')
        member = User.get_user(user)
        if member.mem_oauth_secret == secret_key:
            mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
            evis = Evis.post(request.POST.get("status"), request.POST.get("status"),\
                         "chatter", mem, mem.primary_node,\
                         ["eviscapelite"], access_token = member.get_token())
            if evis.id:
                return HttpResponse("ok")
    return HttpResponse("fail")

def api_timeline(request):
    if request.POST.has_key('jid'):
        jid = request.POST.get('jid').split('-')
        try:
            user, secret_key = tuple(jid)
        except ValueError:
            return HttpResponse('fail')
        member = User.get_user(user)
        if member.mem_oauth_secret == secret_key:
            access_token = member.get_token()
            mem = Members(member.mem_id, member.mem_name, primary_node=Nodes(member.nod_id_primary))
            evis = Evis.timeline(mem, mem.primary_node, access_token)[:5]
            bitly = BitLy()
            rep = ""
            for e in evis:
                rep += e.evi_subject + ' ' + bitly.shorten(e.evi_permalink)+ "\n"
            if rep == "":
                rep = "Nothing Could be Found"
            return HttpResponse(rep)
    return HttpResponse("fail")
    
    