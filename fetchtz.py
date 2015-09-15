#!/usr/bin/env python

#stdlib imports
import urllib2
import os.path
import zipfile
import urlparse
import sys
from datetime import datetime,timedelta
import ConfigParser
import ftplib
import shutil

#third party imports
import pytz
import fiona
from shapely.geometry import shape as myshape
from shapely import wkt

TIMEFMT = '%Y-%m-%dT%H:%M:%S'

NULLSTRING = 'NULL'

CONFIG_DESC = '''
[INPUT]
shapefile_url = http://efele.net/maps/tz/world/tz_world_mp.zip
web_page_url = http://efele.net/maps/tz/world/

[OUTPUT]
ftp = ftp://hazards.cr.usgs.gov/web/hazdev-geoserve-ws/timezones/
'''

README = '''
timezones.csv is a dataset that, to the best of our knowledge, describes the spatial extent of the various time zones of the world.

The columns of this file are:
TimeZone - The Olson database compatible time zone name (see https://en.wikipedia.org/wiki/Tz_database) *
DSTStart - The date/time in the most recent year processed where Daylight Savings Time begins (set to NULL if not applicable.)
DSTEnd - The date/time in the most recent year processed where Daylight Savings Time ends (set to NULL if not applicable.)
StandardOffset - The number of hours offset from UTC (Coordinated Universal Time) when Daylight Savings is NOT in effect.
DSTOffset - The number of hours offset from UTC (Coordinated Universal Time) when Daylight Savings IS in effect.
Geometry - A Well-Known-Text string (see https://en.wikipedia.org/wiki/Well-known_text) describing the geometry of the time zone polygon.

This file was created by downloading %s from %s, and associating the time zone names with the corresponding UTC and DST offsets found in the 
Python pytz module (see http://pytz.sourceforge.net/).

The author of the original data set has attributed a Public Domain license 
(see http://creativecommons.org/publicdomain/zero/1.0/) to the input data. 

The license for this data:

This data is in the public domain because it contains materials
that originally came from the United States Geological Survey, an
agency of the United States Department of Interior. For more
information, see the official USGS copyright policy at
http://www.usgs.gov/visual-id/credit_usgs.html#copyright

*There is one non-Olson database compliant time zone "inhabited" in this data set.  These polygons represent the Antarctic continent
and a number of high-latitude islands in the southern hemisphere.  The UTC offsets for this "time zone" are 0 hours for standard and DST.

The code that created this data set can be found at:  https://github.com/mhearne-usgs/fetchtz
'''

def sendFile(filename,ftpurl):
    filehome,fname = os.path.split(filename)
    current = os.getcwd()
    if len(filehome):
        os.chdir(filehome)
    urlparts = urlparse.urlparse(ftpurl)
    ftp = ftplib.FTP(urlparts.netloc)
    ftp.login()
    dirparts = urlparts.path.strip('/').split('/')
    for d in dirparts:
        try:
            ftp.cwd(d)
        except ftplib.error_perm,msg:
            raise Exception,msg
    if not os.path.isfile(fname):
        raise IOError("%s is not a valid file.")
    cmd = "STOR " + fname
    ftp.storbinary(cmd,open(fname,"rb"),1024) #actually send the file
    os.chdir(current)
    return urlparse.urljoin(ftpurl,fname)

if __name__ == '__main__':
    configfile = os.path.join(os.path.expanduser('~'),'.timezone','config.ini')
    if not os.path.isfile(configfile):
        print 'Missing config file at %s.  Config file contents should look like this:\n%s' % (configfile,CONFIG_DESC)
        sys.exit(1)
    config = ConfigParser.ConfigParser()
    config.readfp(open(configfile))
    TZURL = config.get('INPUT','shapefile_url')
    TZPAGE = config.get('INPUT','web_page_url')
    ftpurl = config.get('OUTPUT','ftp')
    upath,zipname = os.path.split(urlparse.urlparse(TZURL).path)
    try:
        fh = urllib2.urlopen(TZURL)
        data = fh.read()
        f = open(zipname,'wb')
        f.write(data)
        f.close()
        fh.close()
    except:
        print 'Could not fetch data at url "%s".  Check "%s" and look for the tz_world shapefile link.' % (TZURL,TZPAGE)
        sys.exit(1)

    myzip = zipfile.ZipFile(zipname,'r')
    shape_pieces = myzip.namelist()
    myzip.extractall()

    shpfile = None
    for piece in shape_pieces:
        if piece.endswith('.shp'):
            shpfile = piece
            break

    if shpfile is None:
        print 'Could not find a shapefile in the data set you downloaded from "%s"' % TZURL
        sys.exit(1)

    shapes = fiona.open(shpfile,'r')
    nshapes = len(shapes)
    ndst = 0
    fname = 'timezones.csv'
    f = open(fname,'wt')
    f.write('TimeZone,DSTStart,DSTEnd,StandardOffset,DSTOffset,Geometry\n')
    for shape in shapes:
        tzid = shape['properties']['TZID']
        shp = myshape(shape['geometry'])
        wktstr = wkt.dumps(shp)
        hasTimeZone = True
        startdst = None
        enddst = None
        #this is a polygon consisting of Antarctica and a bunch of high latitude southern hemisphere
        #islands.  I'm setting them all to UTC.
        if tzid == 'uninhabited': 
            startstr = 'NULL'
            endstr = 'NULL'
            standard = 0
            dst = 0
        else:
            tz = pytz.timezone(tzid)
            current_year = datetime.utcnow().year
            startidx = 0
            startdst = None
            enddst = None
            try:
                for d in tz._utc_transition_times:
                    if d.year == current_year:
                        if startdst is None:
                            startdst = d
                        else:
                            enddst = d
                            break
                    startidx += 1
                if startdst is not None:
                    ndst += 1
            except:
                pass

            if startdst is not None:
                standard_offset = tz.utcoffset(startdst-timedelta(days=1))
                dst_offset = tz.utcoffset(startdst+timedelta(days=1))
            else:
                standard_offset = tz.utcoffset(datetime(current_year,1,1))
                dst_offset = tz.utcoffset(datetime(current_year,1,1))
            standard = (standard_offset.days*24) + (standard_offset.seconds/3600)
            dst = (dst_offset.days*24) + (dst_offset.seconds/3600)
            if startdst is None:
                startstr = 'NULL'
            else:
                startstr = startdst.strftime(TIMEFMT)
            if enddst is None:
                endstr = 'NULL'
            else:
                endstr = enddst.strftime(TIMEFMT)
        f.write('%s,%s,%s,%i,%i,"%s"\n' % (tzid,startstr,endstr,standard,dst,wktstr))
        #print '%s,%s,%s,%i,%i' % (tzid,startstr,endstr,standard,dst)
            
    shapes.close()
    readmefile = 'readme.txt'
    readme = open(readmefile,'wt')
    readme.write(README % (TZURL,TZPAGE))
    readme.close()
    fileurl = sendFile(fname,ftpurl)
    readmeurl = sendFile(readmefile,ftpurl)
    print 'Sent csv file to %s' % fileurl
    print 'Sent README file to %s' % readmeurl
    print 'DST info for %i polygons out of %i' % (ndst,nshapes)
    #delete everything we downloaded, including zip file and world/ folder
    os.remove(fname)
    os.remove(zipname)
    for piece in shape_pieces:
        fbase,fname = os.path.split(piece)
        if os.path.isdir(fbase):
            shutil.rmtree(fbase)
        if os.path.isfile(piece):
            os.remove(piece)
    
    
