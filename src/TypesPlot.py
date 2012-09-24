# coding=utf-8

from collections import defaultdict
import os
import os.path
import re
import sys
import numpy as np
from lxml.builder import E
from lxml import etree

LABEL_SEP = 0.06
LABEL_AREA = (0.03, 0.97)
AXIS_PAD = 0.02
XSEP = 0.04
THRESHOLD = 0.005

DEFAULT_GROUP = "default"

OKCHAR = re.compile(r'[-+.a-zA-Z0-9]+')

def lim(maxval):
    return (-AXIS_PAD * maxval, (1.0 + AXIS_PAD) * maxval)

def fixname(s):
    r = []
    for ok in OKCHAR.finditer(s):
        r.append(ok.group().lower())
    if r == '':
        return 'x'
    else:
        return '-'.join(r)

SEP = u" · "

def add_sep(l, sep=SEP):
    # [1,2,3] -> [1,sep,2,sep,3]
    return [x for y in l for x in (y, sep)][:-1]

def write_html(f, doc):
    f.write('<!DOCTYPE html>\n')
    f.write(etree.tostring(doc, method='html', pretty_print=True))


class LabelPlacement:
    def __init__(self):
        self.freelist = set()
        self.freelist.add(LABEL_AREA)

    def place(self, y):
        closest = None
        bestdist = None
        bestplace = None
        for free in self.freelist:
            a, b = free
            if y < a:
                dist = a - y
                place = a
            elif a <= y <= b:
                dist = 0.0
                place = y
            elif b < y:
                dist = y - b
                place = b
            else:
                assert False
            if bestdist is None or bestdist > dist or (bestdist == dist and free < closest):
                closest = free
                bestdist = dist
                bestplace = place
        if closest is None:
            return None
        self.freelist.remove(closest)
        y1, y4 = closest
        y2 = bestplace - LABEL_SEP
        y3 = bestplace + LABEL_SEP
        if y1 < y2:
            self.freelist.add((y1, y2))
        if y3 < y4:
            self.freelist.add((y3, y4))
        return bestplace

class CPoint:
    def __init__(self, ec, fc, lw):
        self.ec = ec
        self.fc = fc
        self.lw = lw

SEL   = CPoint( (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 1.5 )
UNSEL = CPoint( (0.6, 0.6, 0.6), (1.0, 1.0, 1.0), 0.5 )

class Point:
    def __init__(self, collectioncode, y, x, above, below, total):
        self.collectioncode = collectioncode
        self.y = y
        self.x = x
        if above < below:
            self.side = 'above'
            self.pvalue = float(above)/float(total)
        else:
            self.side = 'below'
            self.pvalue = float(below)/float(total)

        self.ms = 7
        self.marker = 'o'

        if self.side is None:
            pass
        elif self.pvalue > 0.1:
            pass
        elif self.side == 'above':
            self.ms = 10
            self.marker = '^'
        elif self.side == 'below':
            self.ms = 10
            self.marker = 'v'

        self.ec = (0.0, 0.0, 0.0)
        self.fc = (1.0, 1.0, 1.0)
        self.lw = 1.0

        if self.pvalue is None:
            pass
        elif self.pvalue < 0.000001:
            self.fc = (1.0,  0.75, 0.75)
        elif self.pvalue < 0.00001:
            self.fc = (1.0,  0.8,  0.8)
        elif self.pvalue < 0.0001:
            self.fc = (1.0,  0.85, 0.85)
        elif self.pvalue < 0.001:
            self.fc = (1.0,  0.90, 0.90)
        elif self.pvalue < 0.01:
            self.fc = (1.0,  0.95, 0.95)
        else:
            self.ec = (0.2,  0.2,  0.2)


class Curve:
    def __init__(self, dirdict,
                 corpuscode, corpus_descr,
                 statcode, xlabel, ylabel,
                 datasetcode, dataset_descr):
        self.dirdict = dirdict
        self.corpuscode = corpuscode
        self.corpus_descr = corpus_descr
        self.statcode = statcode
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.datasetcode = datasetcode
        self.dataset_descr = dataset_descr
        self.timestamp = None
        self.collection_descr = dict()
        self.group_by_collection = dict()
        self.point_by_collection = dict()
        self.points_by_group = dict()
        self.groups = []
        self.group_set = set()
        self.timestamp_by_group = dict()
        self.polys = []
        self.maxx = 0
        self.maxy = 0
        self.group_seen(None)

    def group_seen(self, groupcode):
        if groupcode not in self.group_set:
            self.points_by_group[groupcode] = []
            self.groups.append(groupcode)
            self.group_set.add(groupcode)
            self.points_by_group[groupcode] = []

    def add_timestamp(self, timestamp):
        if self.timestamp is None:
            self.timestamp = timestamp
        else:
            self.timestamp = max(self.timestamp, timestamp)

    def add_timestamp_group(self, timestamp, groupcode):
        if groupcode not in self.timestamp_by_group:
            self.timestamp_by_group[groupcode] = timestamp
        else:
            self.timestamp_by_group[groupcode] = max(self.timestamp_by_group[groupcode], timestamp)

    def add_poly(self, level, upper, lower):
        poly = np.concatenate((upper, np.flipud(lower)))
        maxs = np.amax(poly, axis=0)
        self.polys.append(poly)
        self.maxx = max(self.maxx, maxs[0])
        self.maxy = max(self.maxy, maxs[1])

    def add_collection(self, groupcode, collectioncode, description):
        if groupcode is None:
            groupcode = DEFAULT_GROUP
        self.group_by_collection[collectioncode] = groupcode
        self.collection_descr[collectioncode] = description

    def add_point(self, p, timestamp):
        assert p.collectioncode not in self.point_by_collection
        self.point_by_collection[p.collectioncode] = p
        groupcode = self.group_by_collection[p.collectioncode]
        self.group_seen(groupcode)
        self.points_by_group[groupcode].append(p)
        self.add_timestamp_group(timestamp, groupcode)

    def get_suffixes(self, p=None):
        if p is None:
            return ['pdf', 'svg']
        else:
            return ['svg']

    def get_basename(self, groupcode):
        b = [self.statcode, self.datasetcode]
        if groupcode is not None:
            b.append(groupcode)
        return "-".join([fixname(n) for n in b])

    def get_pointname(self, suffix, groupcode, p=None):
        n = self.get_basename(groupcode)
        if p is not None:
            n = n + "--" + fixname(p.collectioncode)
        n = n + "." + suffix
        return n

    def get_pointname_from_root(self, suffix, groupcode, p=None):
        return fixname(self.corpuscode) + "/" + self.get_pointname(suffix, groupcode, p)

    def get_pointname_relative(self, other, suffix, groupcode, collectioncode=None):
        changed = False
        if groupcode is not None and groupcode not in self.group_set:
            groupcode = None
            changed = True
        if groupcode is None and collectioncode is not None:
            collectioncode = None
            changed = True
        if collectioncode is not None and collectioncode not in self.point_by_collection:
            collectioncode = None
            changed = True
        if collectioncode is not None:
            exp = self.group_by_collection[collectioncode]
            if exp != groupcode:
                changed = True
                collectioncode = None
        if collectioncode is not None:
            p = self.point_by_collection[collectioncode]
        else:
            p = None
        name = self.get_pointname(suffix, groupcode, p)
        if self.corpuscode == other.corpuscode:
            full = name
        else:
            full = "../" + fixname(self.corpuscode) + "/" + name
        return full, changed

    def get_directory(self, suffix):
        return os.path.join(self.dirdict[suffix], fixname(self.corpuscode))

    def get_filename(self, suffix, groupcode, p=None):
        return os.path.join(self.get_directory(suffix), self.get_pointname(suffix, groupcode, p))

    def get_directories(self):
        return [ self.get_directory(suffix) for suffix in self.get_suffixes() ]

    def get_filenames(self, groupcode, p=None):
        return [ self.get_filename(suffix, groupcode, p) for suffix in self.get_suffixes(p) ]

    def is_outdated(self, groupcode):
        for filename in self.get_filenames(groupcode):
            if not os.path.exists(filename):
                return True
            mtime = os.path.getmtime(filename)
            if mtime < self.timestamp:
                return True
            if groupcode in self.timestamp_by_group and mtime < self.timestamp_by_group[groupcode]:
                return True
        return False

    def get_outdated(self):
        outdated = []
        for groupcode in sorted(self.points_by_group.keys()):
            if self.is_outdated(groupcode):
                outdated.append(groupcode)
        return outdated

    def plot_group(self, matplotlib, groupcode):
        self.plot_group_points(matplotlib, groupcode, None)
        for point in self.points_by_group[groupcode]:
            self.plot_group_points(matplotlib, groupcode, point)

    def plot_group_points(self, matplotlib, groupcode, point):
        points = sorted(self.points_by_group[groupcode], key=lambda p: p.x, reverse=True)
        SPP = matplotlib.figure.SubplotParams(left=0.1, right=0.85, bottom=0.1, top=0.98)
        fig = matplotlib.pyplot.figure(figsize=(9,6), subplotpars=SPP)
        ax = fig.add_subplot(111, xlim=lim(self.maxx), ylim=lim(self.maxy))
        self.plot_polys(ax)
        self.plot_points(ax, points, groupcode, point)
        self.plot_labels(ax)
        for suffix in self.get_suffixes(point):
            filename = self.get_filename(suffix, groupcode, point)
            fig.savefig(filename)
            if suffix == 'svg':
                self.fix_svg(filename)

    def plot_polys(self, ax):
        for i, poly in enumerate(self.polys):
            f = i/(len(self.polys)-1.0)
            edge = (0.0, 0.0, 1.0)
            fill = (1.0-0.35*f, 1.0-0.25*f, 1.0)
            ax.fill(poly[:,0], poly[:,1], fc=fill, ec=edge, linewidth=0.4, zorder=100 + f)

    def plot_points(self, ax, points, groupcode, point):
        placement = LabelPlacement()
        for i, p in enumerate(points):
            scx, scy = float(p.x)/self.maxx, float(p.y)/self.maxy
            stx = scx + XSEP
            sty = placement.place(scy)
            url = self.get_pointname('html', groupcode, p)
            if point is None:
                cp = p
            elif point == p:
                cp = SEL
            else:
                cp = UNSEL
            if sty is not None:
                tx = stx * self.maxx
                ty = sty * self.maxy
                ax.plot(
                    [p.x, p.x, tx],
                    [p.y, ty,  ty],
                    color=cp.ec,
                    linewidth=cp.lw,
                    clip_on=False,
                    zorder=200
                )
            ax.scatter(
                p.x, p.y,
                marker=p.marker,
                edgecolor=cp.ec,
                facecolor=cp.fc,
                linewidth=cp.lw,
                s=p.ms**2,
                zorder=202,
                urls=[url],
            )
            if sty is not None:
                ax.text(
                    tx, ty,
                    p.collectioncode,
                    color=cp.ec,
                    va='center',
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        fc=cp.fc,
                        ec=cp.ec,
                        linewidth=cp.lw,
                    ),
                    zorder=201,
                )

    def plot_labels(self, ax):
        ax.set_xlabel(self.xlabel, labelpad=10)
        ax.set_ylabel(self.ylabel, labelpad=15)

    def fix_svg(self, filename):
        with open(filename) as f:
            data = f.read()
        data = data.replace('<a xlink:href=', '<a target="_top" xlink:href=')
        with open(filename, 'w') as f:
            f.write(data)

    def generate_html(self, ac):
        for groupcode in sorted(self.points_by_group.keys()):
            for p in [None] + self.points_by_group[groupcode]:
                filename = self.get_filename('html', groupcode, p)
                with open(filename, 'w') as f:
                    self.generate_html_one(f, groupcode, p, ac)

    def generate_html_one(self, f, groupcode, point, ac):
        collectioncode = point.collectioncode if point is not None else None

        headblocks = []
        bodyblocks = []

        t = [ self.corpuscode, self.datasetcode, groupcode, collectioncode, self.statcode ]
        t = u" — ".join([a for a in t if a is not None])
        headblocks.append(E.title(t))
        headblocks.append(E.link(rel="stylesheet", href="../types.css", type="text/css"))

        def add_menu(title, cl, gl, xl, labelhook, titlelink=None):
            result = []
            for c in cl:
                for g in gl:
                    for x in xl:
                        label, desc = labelhook(c, g, x)
                        attr = dict()
                        if c == self and g is groupcode and x is collectioncode:
                            attr["class"] = "menuitem menusel"
                            e = E.span(label, **attr)
                        else:
                            href, changed = c.get_pointname_relative(self, 'html', g, x)
                            if desc is not None:
                                attr["title"] = desc
                            attr["class"] = "menuitem menuother" if changed else "menuitem menusame"
                            e = E.a(label, href=href, **attr)
                        result.append(e)
            t = title + ":"
            if titlelink is None:
                t = E.span(t, **{"class": "menutitle"})
            else:
                t = E.a(t, href=titlelink, **{"class": "menutitle"})
            menu = E.p(*add_sep([t] + result, " "), **{"class": "menurow"})
            menublocks.append(menu)

        menublocks = []
        add_menu(
            "Corpus",
            ac.by_dataset_stat_fallback[(self.datasetcode, self.statcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (c.corpuscode, c.corpus_descr),
            titlelink="../index.html"
        )
        menublocks.append(E.p(self.corpus_descr, **{"class": "menudesc"}))
        add_menu(
            "Dataset",
            ac.by_corpus_stat[(self.corpuscode, self.statcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (c.datasetcode, c.dataset_descr)
        )
        menublocks.append(E.p(self.dataset_descr, **{"class": "menudesc"}))
        add_menu(
            "Points",
            [ self ],
            self.groups,
            [ collectioncode ],
            lambda c, g, x: ("none", None) if g is None else (g, None)
        )
        add_menu(
            "Axes",
            ac.by_corpus_dataset[(self.corpuscode, self.datasetcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (c.statcode, "y = %s, x = %s" % (c.ylabel.lower(), c.xlabel.lower()))
        )
        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))

        fig = E.p(E.object(
            data=self.get_pointname('svg', groupcode, point),
            type="image/svg+xml"
        ), **{"class": "plot"})
        bodyblocks.append(fig)

        menublocks = []
        add_menu(
            "Collection",
            [ self ],
            [ groupcode ],
            [ None ] + [ p.collectioncode for p in self.points_by_group[groupcode] ],
            lambda c, g, x: ("none", None) if x is None else (x, self.collection_descr[x])
        )
        if collectioncode is not None:
            if self.collection_descr[collectioncode] is not None:
                menublocks.append(E.p(self.collection_descr[collectioncode], **{"class": "menudesc"}))
            stat = [
                u"%s %s" % (point.x, self.xlabel.lower()),
                u"%d %s" % (point.y, self.ylabel.lower()),
                u"%f %s" % (point.pvalue, point.side),
            ]
            t = E.span("Statistics:", **{"class": "menutitle"})
            stat = [ E.span(v, **{"class": "menuitem"}) for v in stat ]
            menu = E.p(*add_sep([t] + stat, " "), **{"class": "menurow"})
            menublocks.append(menu)
        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))            

        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        write_html(f, doc)

