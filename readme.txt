
timezones.csv is a dataset that, to the best of our knowledge, describes the spatial extent of the various time zones of the world.

The columns of this file are:
TimeZone - The Olson database compatible time zone name (see https://en.wikipedia.org/wiki/Tz_database) *
DSTStart - The date/time in the most recent year processed where Daylight Savings Time begins (set to NULL if not applicable.)
DSTEnd - The date/time in the most recent year processed where Daylight Savings Time ends (set to NULL if not applicable.)
StandardOffset - The number of hours offset from UTC (Coordinated Universal Time) when Daylight Savings is NOT in effect.
DSTOffset - The number of hours offset from UTC (Coordinated Universal Time) when Daylight Savings IS in effect.
Geometry - A Well-Known-Text string (see https://en.wikipedia.org/wiki/Well-known_text) describing the geometry of the time zone polygon.

This file was created by downloading http://efele.net/maps/tz/world/tz_world_mp.zip from http://efele.net/maps/tz/world/, and associating the time zone names with the corresponding UTC and DST offsets found in the 
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
