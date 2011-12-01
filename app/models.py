from google.appengine.ext import db
from pyeviscape.oauth import OAuthToken
from pyeviscape.eviscape import Members, Nodes

# Create your models here.
def gql(cls, clause, *args, **kwds):
    """Return a query object, from the cache if possible.
    Args:
        cls: a db.Model subclass.
        clause: a query clause, e.g. 'WHERE draft = TRUE'.
        *args, **kwds: positional and keyword arguments to be bound to the query.

    Returns:
      A db.GqlQuery instance corresponding to the query with *args and
      **kwds bound to the query.
    """
    query_string = 'SELECT * FROM %s %s' % (cls.kind(), clause)
    query = _query_cache.get(query_string)
    if query is None:
        _query_cache[query_string] = query = db.GqlQuery(query_string)
    query.bind(*args, **kwds)
    return query

class User(db.Model):
    mem_id = db.IntegerProperty(required=True)
    mem_name = db.StringProperty(required=True)
    nod_id_primary = db.IntegerProperty(required=True)
    nod_name_primary = db.StringProperty()
    nod_logo_image = db.StringProperty()
    mem_oauth_token = db.StringProperty(required=True)
    mem_oauth_secret = db.StringProperty(required=True)
    created_on = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def get_or_push(cls, member, access_token):
        key = member.mem_name
        assert key
        return cls.get_or_insert(key, mem_id=member.id, mem_name=member.mem_name,\
                                 mem_oauth_token=access_token.key,\
                                 mem_oauth_secret=access_token.secret,\
                                 nod_id_primary=member.primary_node.id,\
                                 nod_name_primary = member.primary_node.nod_name,\
                                 nod_logo_image = member.primary_node.nod_logo_image)
      
    def get_token(cls):
        return OAuthToken(cls.mem_oauth_token, cls.mem_oauth_secret)
        
    @classmethod    
    def get_user(cls, mem_name):
        return cls.get_by_key_name(mem_name)
    
class Token(db.Model):
    token_key = db.StringProperty(required=True)
    token_secret = db.StringProperty(required=True)
    created_on = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def get_or_push(cls, token):
        key = token.key
        secret = token.secret
        assert key
        assert secret
        return cls.get_or_insert(key, token_key=key, token_secret=secret)
    
    @classmethod
    def get_token_by_key(cls, key):
        assert key
        obj = cls.get_by_key_name(key)
        return OAuthToken(obj.token_key, obj.token_secret)
        
    @classmethod
    def delete_token(cls, token):
        obj = cls.get_by_key_name(token.key)
        obj.delete()
        
        
    
    