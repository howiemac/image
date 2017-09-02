"""
config file for app

"""

#meta_description="" #site description text for search engines
#meta_keywords="" #comma separated list of keywords for search engines

default_class="Page"
urlpath=""  # no /evoke in url


from evoke.data.schema import *  #for data definition

class Tag(Schema):
  table='tags'
  name=TAG,KEY
  page=INT,KEY



#class Test(Schema):
#  pass

#from evoke.config_base import User as BaseUser 
#
#class User(BaseUser):
#  pass


# include config.py files from class folders
from Page.config import *
