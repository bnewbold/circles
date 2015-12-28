#!/usr/bin/env python
"""

http://www.osec.doc.gov/webresources/accessibility/RuleEF.htm

"""
import os
import md5
import argparse
import json
from flask import Flask, render_template, send_from_directory, request, \
    url_for, abort, flash, session, g, redirect

app = Flask(__name__)
app.config.from_object(__name__)

archives = {
    'aaaaarg': dict(radius=84, center=[256, 256]),
    'libgen': dict(radius=516, center=[636, 636]),
}

# this gets populated in main()
md5_lists = {
    'libgen': [],
    'aaaaarg': [],
    'aaaaarg+libgen': [],
}

# this also populated in main()
aaaaarg_ids = dict()

def which_archives(coords):
    valid = []
    for name, v in archives.iteritems():
        distance2 = (v['center'][0]-coords[0])**2 + \
                    (v['center'][1]-coords[1])**2
        if distance2 < v['radius']**2:
            valid.append(name)
    return valid

def aaaaarg_direct_url(md5sum):
    idnum = aaaaarg_ids[md5sum]
    while len(idnum) < 6:
        idnum = '0' + idnum
    print idnum
    return "http://aaaaarg.fail/search?query=%s" % md5sum.lower()

def libgen_direct_url(md5sum):
    return "http://libgen.io/get_new.php?md5=%s&open=2" % md5sum

def closest_md5(key, l):
    """Takes a hash and a sorted list of hashes, tries to return the closest 
    book to that hash
    """
    if len(l) == 1:
        return l[0]
    middle = l[len(l)/2]
    if middle == key:
        return middle
    if middle > key:
        return closest_md5(key, l[:len(l)/2])
    else:
        return closest_md5(key, l[len(l)/2:])

def find_book(coords, archives):
    if len(archives) == 0:
        return None
    lname = '+'.join(sorted(archives))
    md5want = md5.md5(','.join(map(str,coords))).hexdigest().upper()
    md5got = closest_md5(md5want, md5_lists[lname])
    print "wanted: %s" % md5want
    print "got: %s" % md5got
    if 'libgen' in archives:
        # prefer to do libgen links
        return dict(url=libgen_direct_url(md5got), md5sum=md5got)
    elif 'aaaaarg' in archives:
        return dict(url=aaaaarg_direct_url(md5got), md5sum=md5got)
    else: 
        raise Exception("Don't know how to find URL for: %s" % archives)
    return None

@app.route('/', methods=['GET'])
def homepage():
    return render_template('home.html')

@app.route('/book/', methods=['GET'])
def bookpage():
    coords = []
    for k in request.args.keys():
        try:
            coords = map(int, k.split(','))
            assert len(coords) == 2
            break
        except Exception:
            coords = []
    print coords
    archives = which_archives(coords)
    print archives
    book = find_book(coords, archives)
    print book
    if book and True:
        # just temporary redirect...
        return redirect(book['url'])
    return render_template('book.html', book=book)

@app.route('/favicon.ico', methods=['GET'])
def favicon():
    """ Simple static redirect """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.route('/robots.txt', methods=['GET'])
def robots():
    """ "Just in case?" """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt',
                               mimetype='text/plain')

#############################################################################
def main():
    """Primary entry-point for torouterui.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
        action='store_true',
        help="enable debugging interface")
    parser.add_argument('--host',
        default="127.0.0.1",
        help="listen on this host/IP")
    parser.add_argument('--port',
        type=int,
        default=5050,
        help="listen on this port")
    args = parser.parse_args()

    with open('libgen_only.md5','r') as f:
        md5_lists['libgen'] = map(lambda s: s.strip(), f.readlines())
    #with open('aaaaarg_only.md5','r') as f:
    with open('aaaaarg_only_partial.md5','r') as f:
        md5_lists['aaaaarg'] = map(lambda s: s.strip(), f.readlines())
    with open('both.md5','r') as f:
        md5_lists['aaaaarg+libgen'] = map(lambda s: s.strip(), f.readlines())
    with open('aaaaarg.json','r') as f:
        bigs = ''.join(f.readlines())
        bigj = json.loads(bigs)
        for k, v in bigj.iteritems():
            aaaaarg_ids[v] = k
        # garbage collect plz?
        bigs = None
        bigj = None
        f.close()

    app.run(debug=args.debug, host=args.host, port=args.port)

if __name__ == '__main__':
    main()
