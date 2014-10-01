# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/dev-python/mysql-python/mysql-python-1.2.3.ebuild,v 1.10 2012/09/30 16:55:11 armin76 Exp $

EAPI="2"
PYTHON_DEPEND="2:2.5 3:3.1"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="*-jython"

inherit distutils

DESCRIPTION="Python interface to MySQL"
HOMEPAGE=" http://dev.mysql.com/doc/connector-python/en/index.html"
SRC_URI="http://dev.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.1.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64"
IUSE=""

RDEPEND=""
DEPEND="${RDEPEND}
	dev-python/setuptools"

#DOCS="HISTORY doc/FAQ.txt doc/MySQLdb.txt"
PYTHON_MODNAME="mysql"
