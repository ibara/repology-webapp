# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import shlex
import string
import sys
import urllib.parse
from typing import Any, Callable, ClassVar, Dict, Mapping, Optional, Sequence, Union

from repologyapp.package import PackageDataDetailed

__all__ = ['PackageFormatter']


def _safe_int(arg: str) -> int:
    try:
        return int(arg)
    except ValueError:
        return 0


class PackageFormatter(string.Formatter):
    _all_filters: ClassVar[Dict[str, Callable[[str], str]]] = {
        'lowercase': lambda x: x.lower(),
        'firstletter': lambda x: x.lower()[0],
        'libfirstletter': lambda x: x.lower()[:4] if x.lower().startswith('lib') else x.lower()[0],
        'stripdmo': lambda x: x[:-4] if x.endswith('-dmo') else x,
        'basename': lambda x: x.rsplit('/', 1)[-1],
        'dirname': lambda x: x.rsplit('/', 1)[0],
        'dec': lambda x: str(_safe_int(x) - 1),
        'inc': lambda x: str(_safe_int(x) + 1),
    }

    _escape_mode: Optional[str]

    def __init__(self, escape_mode: Optional[str] = None):
        self._escape_mode = escape_mode

    def get_value(self, key: Union[int, str], args: Sequence[Any], kwargs: Mapping[Any, Any]) -> str:
        # XXX: after Problems are refactored, switch to strong typing here
        pkgdata = args[0].__dict__ if isinstance(args[0], PackageDataDetailed) else args[0]
        key, *filters = str(key).split('|')

        value: Optional[str] = None

        if key == 'name':
            value = pkgdata['name']
        elif key == 'srcname':
            value = pkgdata['srcname']
        elif key == 'binname':
            value = pkgdata['binname']
        elif key == 'subrepo':
            value = pkgdata['subrepo']
        elif key == 'version':
            value = pkgdata['version']
        elif key == 'origversion':
            value = pkgdata['origversion']
        elif key == 'rawversion':
            value = pkgdata['rawversion']
        elif key == 'category':
            value = pkgdata['category'] if pkgdata['category'] is not None else ''
        elif key == 'archrepo':
            value = 'community' if pkgdata['subrepo'].startswith('community') else 'packages'
        elif key in pkgdata['extrafields']:
            value = pkgdata['extrafields'][key]

        if value is None:
            # XXX: need a proper logging facility, but using stderr for now
            print('PackageFormatter failure: key={} repo={} names={}'.format(key, pkgdata['repo'], '|'.join(pkgdata[key] for key in ['name', 'srcname', 'binname'] if pkgdata[key])), file=sys.stderr)
            return ''

        for filtername in filters:
            if filtername in PackageFormatter._all_filters:
                value = PackageFormatter._all_filters[filtername](value)

        if self._escape_mode == 'url':
            value = urllib.parse.quote(value)
        elif self._escape_mode == 'shell':
            # XXX: not entirely readable, but a safe default
            value = shlex.quote(value)
        elif self._escape_mode is not None:
            raise RuntimeError('unknown PackageFormatter escape mode {}'.format(self._escape_mode))

        return value
