"""
images: override for evoke/Page/Page.py

implements:
 - image addition
 - tags

written by Ian Howie Mackenzie 2016 onwards
"""

from evoke.Page import Page as basePage
from evoke.lib import *
from evoke.render import html

from copy import copy
import os, time, datetime, urllib.request, urllib.parse, urllib.error

class Page(basePage):
  ""
  contextkinds=['file'] #override - "image" removed from here


  # level depth

  toplevel=6
  toplevel=7
  toplevel=9

  # view override ####################

  @html
  def view_image(self,req):
    ""
    #req.wrapper=None

  @html
  def view_tagcloud(self,req):
    ""
    #req.wrapper=None

  def view(self,req):
    ""
    if self.uid and self.uid==2: # additions
      return self.additions(req)
    elif self.uid and self.uid<=self.maxlevel(): # levels
      return self.view_tagcloud(req)
    elif self.kind=="image": # images
      return self.view_image(req)
    return basePage.view(self,req) # root

  def latest(self, req):
    "overridden to include only child images, and to allow for additions"
    lim=page(req)
    where=f"{self.parentclause()} and rating>={self.minrating()}"
    req.pages = self.list(kind='image',where=where,orderby="uid desc",limit=lim)
    req.title="latest"
    req.page='latest' # for paging
    return self.listing(req)

  def additions(self, req):
    "fetch new images (from page 2) and list them"
    # set minrating to 0 (ie ?)
    self.set_minrating(0)
    # add new files from "image additions" folder
    self.add_images()
    # return thumbnail listing
    lim=page(req)
#    where='rating>=%s and lineage like "%s%%"' % (self.minrating(),self.lineage+str(self.uid)+'.')
    where='rating>=%s' % self.minrating()
    req.pages = self.list(kind='image',parent=2,where=where,orderby="uid desc",limit=lim)
    req.title="latest"
    req.page='additions' # for paging
    req.root=2 # for navigation
    if req.pages:
      return self.listing(req)
    # fallback if no pages found
    req.warning= "no additions found"
    return self.get(1).view(req)


  # edit override
  
  def edit(self,req):
    "page edit"
    return self.edit_form(req)

  def save_text(self,req):
    "override of evoke version - this is called by Page_edit_form.evo"
    self.update(req)
    self.flush_page(req)
    self.clear_form(req)
    return self.edit_return(req)

  def edit_return(self,req,view=""):
    """common return for edit options 
     - redirect to optional view function 
     - or else the default is "", ie view() 
     - preserves req.tag, req.root, if they exist
    """
    extras={}
#    for k in ('tag','root'):
#      if (k in req) and req[k]:
#        extras[k]=req[k]
#    return req.redirect(self.url(view,**extras))
    return req.redirect(self.url(view,tag=req.tag,root=req.root))

  # autostyle of image

  def autostyle(self,scale=100):
    "return a CSS style to autosize the image for use in evo template"
    d=self.get_stage_data()
    w=safeint(d["full_width"])
    h=safeint(d["full_height"])
    if (w and h) and (w>h):
      return "height:%d%%" % (h*scale//w,)
    else:
      return "height:%s%%" % scale

  # adding images ########################

  def add_images(self):
    '''
    fetch new images from image_additions folder, and allocate tags based on image folder name (if any)

    - assume that self.Config.additions_folder (default = "image_additions") will hold (in a tree) any new image files to be added
    - for each one:
      - add a new image page
      - fetch (move) the image file to the data folder
      - add tags based on dot-separated values in parent folder name
    '''
    # fetch some key data objects..
    # get a list of filepaths, extract image files, create image pages for them, moving the files to the ~/data folder
    root=True #use this to identify if we are in the root - ie the additions - folder
    for path,dirs,files in os.walk(self.Config.additions_folder):
      dirname=path.replace('\\','/').split("/")[-1] # (fix MS brain-dead slashes, and strip off path)
#      print "processing: ", dirname  # path ,dirs, files
      for name in files:
        filepath=os.path.join(path,name)
        # get extension: ext
        exts=name.rsplit(".",1)
        if (len(exts)==2):
          ext=exts[1].lower()
        else:
          ext=""
        if ext in ('jpg','jpeg','gif','png'):
          # create a new image page
          image=self.new()
          image.parent=2 #parent is always additions page (2)
          image.kind='image'
          image.seq=image.uid
          image.stage='right full' #rest of stage data will be added on the fly later by get_stage_data() 
#          image.update(req)
          image.set_lineage()
          image.text=os.path.join(dirname,name)
#          print "text=",image.text
          image.code="%s.%s" % (image.uid,ext)
          image.when=DATE(datetime.datetime.fromtimestamp(os.path.getmtime(filepath)))
#          print "modified:", image.when
          image.flush() #store the image page
##          image.renumber_siblings_by_kind()#keep them in order
          # move the image file
          os.renames(filepath,image.file_loc(image.code)) #BEWARE: this will remove the image_additions folder itself if it is now empty...
          # add tags (unless we are at the root of the file tree)
          if not root:
            for tag in dirname.split("."):
              image.add_tag(tag)
      root=False;
    return True

  # TAGS ################################
  # 
  # listing of tag results ##############

  def selecttag(self,req):
    " add to tag selection list for viewing"
    tags=[]
    if req.tag:
      tags=req.tag.split(".")
    if req.addtag:
      if req.addtag in tags: # negate it
        tags[tags.index(req.addtag)]="~"+req.addtag
      elif ("~"+req.addtag) in tags: # negate it
        tags[tags.index("~"+req.addtag)]=req.addtag
      else: # add the tag
        tags.append(req.addtag)
    if req.deltag and req.deltag in tags:
      tags.remove(req.deltag)
    req.tag=".".join(tags)
    return self.redirect(req,"?tag=%s" % req.tag)

  def latest_pages(self,limit):
    "returns a list of image pages in descending uid order"
    where=f"{self.parentclause()} and rating>={self.minrating()}"
    return self.list(kind='image',where=where,orderby="uid desc",limit=limit)

  def latest(self, req):
    "overridden to include only child images, and to allow for additions"
    req.pages = self.latest_pages(limit=page(req))
    req.title="latest"
    req.page='latest' # for paging
    return self.listing(req)

  def tagged(self,req,pagemax=50):
    " returns a listing of all images with given req.tag, in descending uid order"
    if not req.tag:
      return self.latest(req)
    if req.tag=="UNTAGGED":
      return self.untagged(req,pagemax)
    limit=page(req,pagemax)
    req.pages=self.children_by_tag(tag=req.tag,order="uid desc",limit=limit)
    req.title=f'images tagged {req.tag}'
    req.page='tagged' # for paging
    return self.listing(req)

  def untagged(self,req,pagemax=50):
    " returns a listing of all pages with no tag "
    limit=page(req,pagemax)
    req.pages=self.children_untagged(order="uid desc",limit=limit)
    req.title='untagged images'
    req.page='tagged' # for paging
    return self.listing(req)

  def next_page(self,req):
    " return the next page for given req.tag and req.root"
    p=self.get(req.root) if req.root else self.get_pob()
    if req.tag:
      pages=p.children_by_tag(tag=req.tag,order="uid desc",limit="1",below=self.uid)
      if pages:
        return pages[0]
      req._method='tagged'
      return p
    else: # no tag, so return next image by UID (descending)
      where=f"{p.parentclause()} and uid<{self.uid} and rating>={self.minrating()}"
      pages=self.list(kind="image",where=where,limit=1,orderby='uid desc')
      if pages:
        return pages[0]
#      if req.root==1: # return to additions page
#        req._method='additions'
#      else:
#        req._method=''
      return p

  def next(self,req):
    " return the view (or req._method) of the next page for given req.tag and req.root "
    p=self.next_page(req)
    return p.edit_return(req,req._method)

  # slideshow #############

  @html
  def show(self,req):
    "slideshow" 

  def slideshow(self,req):
    "start a slideshow for given req.tag and req.root"
    if req.tag:
      first=self.children_by_tag(tag=req.tag,order="uid desc",limit=1)
    else:
      first=self.latest_pages(limit=1)
    if first:
      return first[0].show(req)
    req.warning="no results found"
    return self.view(req)


  # tags utilities #####################

  def get_tags(self):
    "return a list of tag names for this page (or if none, the pseudo-tag 'UNTAGGED')"
    tags=[i.name for i in self.Tag.list(page=self.uid, orderby='uid')]
    return tags or ["UNTAGGED"]

#  def get_related_tags(self):
#    "return a list of tag names related to this page's tags"
#    primetag=??????????????
#    [t["name"] for t in self.list(asObjects=False,sql="select distinct name from %s.tags where page in (select page from tags where name='%s')" % (self.Config.database,primetag))]

  def get_recent_tags(self):
    "return a list of tag names recently used"
    return [i.name for i in self.Tag.list(orderby="uid desc",limit="20")]

  def get_tagnames(self):
    "return a list of currently used tagnames"
    return [str(i.get('name')) for i in self.Tag.list(asObjects=False,what="distinct name", orderby="name")]

  def get_sized_tagnames(self):
    "return a complete list of (tagname,textsize) tuples, where textsize indicates usage"
#    taggings=self.Tag.count()
#    print "taggings=",taggings
    db=self.Config.database
    sql="""select tags.name, count(pages.uid) as subtotal
           from `%s`.pages as pages
           inner join `%s`.tags as tags
           on page = pages.uid
           where %s
           and rating >= %s
           group by tags.name
           order by tags.name
        """ % (db,db,self.parentclause(),self.minrating())
#    print sql
    data=[]
    tagcounts=self.list(sql=sql,asObjects=False)
    total=sum(t["subtotal"] for t in tagcounts)
    for t in tagcounts:
      z=total//t["subtotal"]
      textsize = "huge" if z<=8 else \
                 "big"  if z<=32 else \
                 "norm" if z<=256 else \
                 "wee"  if z<=4096 else \
                 "tiny"
      data.append((t["name"],textsize))
    return data

  def add_tag(self,tag):
    "add a new tag - returning its tag object"
    tob=self.Tag.new()
    tob.name=tag
    tob.page=self.uid
    tob.flush()
    return tob

  def update_tags(self,req):
    "edit update for tags"
    if 'tag1' in req:
      oldtags=self.Tag.list(page=self.uid)
      newtags=[]
      i=1
      while ('tag%s' % i) in req:
        t=req.get('tag%s' % i)
        i+=1
        if t:
          newtags.append(t)
      for t in newtags:
        self.add_tag(t)# add the tag
      for tob in oldtags:
        tob.delete()

  def tag(self,req):
    "add tag of req.name for self"
    if req.name:
      name=urllib.parse.unquote_plus(req.name)
      if name not in self.get_tags():
        self.add_tag(name)
    return req.redirect(self.url("",tag=req.tag,root=req.root))

  def untag(self,req):
    "remove tag of req.name from self"
    if req.name:
      name=urllib.parse.unquote_plus(req.name)
      for t in self.Tag.list(page=self.uid,name=name):
        t.delete()
    return req.redirect(self.url("",tag=req.tag,root=req.root))

  def parentclause(self):
    "returns sql WHERE clause operator and parameters, depending on self.uid and self.maxlevel"
    clause=(f"={self.uid}") if (self.uid>1) else (f"<={self.maxlevel()}")
    return f"pages.parent{clause}"

  def children_by_tag(self,tag="",order="uid",limit="",below=None):
    """ return a list of all child page objects with given tag
    - tag may be a single tag string, or a period-separated string of tags to combine
    - tags prefixed with ~ are interpreted as tags to exclude
    - "below" - if set - limits the results to uids below this value 
    """
    if (not tag) or (tag=="UNTAGGED"):
      return self.children_untagged(order=order,limit=limit,below=below)
    db=self.Config.database
    # allow for multiple tags and exclusion tags
    tags=tag.split(".")
    andclause='uid %sin (select distinct page from `%s`.tags where name="%s")'
    andclauses=[(andclause % ("not " if i[0]=="~" else "",db,i.lstrip("~"))) for i in tags]
    tagclause=" and ".join(andclauses)
    # allow for "below" parameter
    belowclause= f"and pages.uid<{below}" if below else ""
    sql=f"""select * from `{db}`.pages
           where {self.parentclause()}
           and kind="image"
           and rating>={self.minrating()}
           {belowclause}
           and {tagclause}
           order by {order}
        """
    if limit:
      sql+="limit %s" % limit
#    print ">>>>>>>>>>>>>", sql
    return self.list(sql=sql)


  def children_untagged(self,order="uid",limit="",below=None):
    """ returns a list of all child images with no tag
    - "below" - if set - limits the results to uids below this value
    """
    db=self.Config.database
    belowclause= f"and pages.uid<{below}" if below else ""
    sql=f"""select pages.* from `{db}`.pages
           left join `{db}`.tags
           on tags.page=pages.uid
           where {self.parentclause()}
           and pages.kind="image"
           and tags.page is NULL
           and rating>={self.minrating()}
           {belowclause}
           order by pages.{order}
        """
    if limit:
      sql+=f"limit {limit}"
#    print ">>>>>>>>>>>>>", sql
    return self.list(sql=sql)


  # end of tags

# deletion

  def delete_tags(self):
    "delete the tags associated with self"
    for t in self.Tag.list(page=self.uid):
      t.delete()
    
  def remove_image(self,req):
    "for images only - deletes self and the related image file"
    if self.kind=="image":
      # delete the file (O/S THIS SHOULD ONLY HAPPEN IF SELF HAS NOT YET BEEN ARCHIVED) and the database instance
      self.delete_image()
      # delete the associated tags
      self.delete_tags()  
      return req.redirect(self.get(1).url(""))
    req.error="not an image - cannot remove this"
    return req.redirect(self.url(""))  


# ratings + disable/enable ################
  ratedkinds=("page","image")  
  downratings=(-4,-4,-3,-2,-4,0,1)
  upratings=(0,-2,-1,-1,1,2,2)

  # access these via rating_symbol()
  ratingsymbols=('&times;','?','&radic;','&hearts;','?','&radic;','&hearts;')

  def rating_symbol(self,rating=None):
    "give symbol for rating"
    # rating should be in (-4,-3,-2,-1,0,1,2)
    r=min(6,max(0,(rating if rating is not None else self.rating)+4))
    return self.ratingsymbols[r]

  def set_rating(self,rating):
    "sets self.rating to rating"
    self.rating=rating
    self.flush() 

  def minrating(self):
    "returns minimum rating accepted by global filter"
    return self.get(1).rating

  def set_minrating(self,rating):
    "sets minrating (stored as root rating)"
    self.get(1).set_rating(rating)
#    return rating

  def set_global_filter(self,req):
    "sets root rating (used as a global filter) to req.rating"
    self.set_minrating(req.rating)
#    print ">>>",req
    return self.edit_return(req)

  def rate_up(self,req):
    "increase rating"
    try:
      self.rating=self.upratings[self.rating+4]
      self.flush()
    except:
      pass
    return self.edit_return(req)
      
  def rate_down(self,req):
    "decrease rating"
    try:
      self.rating=self.downratings[self.rating+4]
      self.flush()
    except:
      pass
    return self.edit_return(req)

  def toggle_disable(self,req):
    ""
    try:
      self.rating=(0,0,1,2,-3,-2,-1)[self.rating+4]
      self.flush()
    except:
      pass
    return self.edit_return(req)


# score

  @html
  def offer(self,req):
    """ offer two images to select from: self, and req.rival
    """

  def select(self,req):
    """ select self and req.rival, to make an offer
        - starting self should be that of the previous offer (or any preferred starting place)
        if req.tag is specified then the results will be filtered using the first given tag 
    """
#    db=self.Config.database
#    sql="""select pages.uid from `%s`.pages
#             inner join `%s`.tags
#             on tags.page=pages.uid
#             where pages.kind="image"
#             and tags.name<>"girl"
#             and rating>=0
#             and pages.uid>%s
#             order by pages.uid
#             limit 2
#        """ % (db,db,self.uid)
##    print sql
#    pages=[p["uid"] for p in self.list(sql=sql,asObjects=False)]

    # get self
    tag = req.tag.split(".",1)[0] if req.tag else ""
    andclause = f' and uid in (select distinct page from `{self.Config.database}`.tags where name="{tag}")' if tag else ""
    basic_where = "rating>=0"+andclause
    if self.kind == 'image': 
      where=basic_where+f" and uid>{self.uid}"
    else: # assume fist time
      where=basic_where
#    print("self",where) 
    selfs=self.list_int('uid',kind="image",where=where,orderby="uid",limit="1")
    # get rival
    if req.rival:
      where=basic_where+f" and uid<{req.rival}"
    else: # assume first time
      where=basic_where
#    print("rival",where) 
    rivals=self.list_int('uid',kind="image",where=where,orderby="uid desc",limit="1")
    # make and offer
    if selfs and rivals:
      return req.redirect(self.get(selfs[0]).url("offer",rival=rivals[0],tag=tag))
    # bomb out
    return req.redirect(self.get(1).url())

  def win(self,req):
    """ self has been chosen in preference to req.rival
        so adjust scores accordingly
    """
    rival=self.get(safeint(req.rival))
    # adjust scores - don't allow 0 to be re-used
    self.score+= (2 if self.score==-1 else 1)
    self.flush()
    rival.score-= (2 if rival.score==1 else 1)
    rival.flush()
    # return next offer
    return self.select(req)

  def lose(self,req):
    """ req.rival has been chosen in preference to self
        so adjust scores accordingly
    """
    rival=self.get(safeint(req.rival))
    # adjust scores - don't allow 0 to be re-used
    self.score-= (2 if self.score==1 else 1)
    self.flush()
    rival.score+= (2 if rival.score==-1 else 1)
    rival.flush()
    # return next offer
    return self.select(req)

# level


  # access these via level_symbol()
#  levelsymbols=('.','&clubs;','&spades;','&hearts;','&diams;')
  levelsymbols=('*','.','&infin;','&Psi;','&Delta;','&Omega;','&diams;','&spades;','&clubs;')

  def level_symbol(self,level=None):
    "give symbol for level"
    # level should be in (1,2,3,4,5,6,7,8,9)
    l=level or self.parent
    return self.levelsymbols[l-1]

  def set_level(self,req):
    "set level to req.level (or else set it to 2)"
    level=safeint(req.level) or 2
    self.move_to(level)
    return self.edit_return(req)

  def set_maxlevel(self,req):
    "sets root score to given req.level"
    root=self.get(1)
    root.score=safeint(req.level)
    root.flush()
    return req.redirect(self.url())

  def maxlevel(self):
    "max level being displayed - stored in root page score"
    return min(self.toplevel,self.get(1).score or 2)


# file info

  def filesize(self):
    "returns filesize in bytes"
    return os.path.getsize(self.file_loc())



# utilities

  def remove_rejects(self,req):
    "delete all rejected items"
    c=0
    for i in self.list(where="rating=-4"):
      i.delete_image()
      i.delete_tags()
      print("<deleted>",i.uid, i.text)
      c+=1
    return "%s rejected items deleted" % c


  def move_to(self,parent):
    "changes self.parent to parent"
    self.parent=parent
    self.set_lineage()
    self.flush()

  @classmethod
  def pare_data(self,req):
    """prunes all obsolete data from the data/image folder
       (adapted from similar routine in mp)

       Optional request parameter: ?source=<your data folder>

       1) moves all data to an "ximage" destination folder
       2) then moves valid data back to source
       3) thus obsolete data remains in the "ximage" folder, for manual deletion

    WARNING: Assumes a proper filesystem (ie not fat or exfat!)
    """
    # data folder
    source=req.source or "/home/howie/data/image/"
    # rename the source folder, and create dest folder (as the original source)
    print('moving "image" folder to "ximage"')
    dest=copy(source)
    source=source.replace("/image/","/ximage/") # DODGY - will break if /image/ is duplicated in the path..
    os.rename(dest,source)
    # move the valid files to the original folder
    print("moving back the valid files...")
    c=0
    for i in self.list(isin={'kind':('file','image')},orderby="uid"):
      c+=1
      fn="%s/%s" % (i.file_folder(),i.code)
      print("keeping ",fn)
      os.renames(source+fn,dest+fn)
    print("done: ",c, " files retained")
    return "pare completed: %s files retained" % c



# fixes

  def fix_parent(self,req):
    "change parent for self (or for pages selected by req.tag) to req.to"
    t=req.tag
    p=safeint(req.to)
    if t:
      c=0
      for page in self.children_by_tag(req.tag):
        c+=1
        page.move_to(p)
      return "%s pages moved to parent %s (%s)" % (c,p,self.get(p).name)
    elif p:
      self.move_to(p)
      return "page %s moved to parent %s (%s)" % (self.uid,p,self.get(p).name)
    return "?to=xxxx is required"

  def fix(self,req):
    ""
    c=0
    for tag in self.Tag.list(name="smoking"):
      for t in self.Tag.list(page=tag.page,name="people"):
        t.name="girl"
        t.flush()
      c+=1
    return "%s tags changed" % c