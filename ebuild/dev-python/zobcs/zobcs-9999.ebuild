# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"
PYTHON_COMPAT=( python{2_7,3_3,3_4})

inherit distutils-r1 git-2

DESCRIPTION="ZOBCS"
HOMEPAGE="https://github.com/zorry/zobsc.git"
SRC_URI=""
LICENSE="GPL-2"
KEYWORDS="~amd64"
SLOT="0"
IUSE="+mysql"

RDEPEND="sys-apps/portage
	dev-python/sqlalchemy
	mysql? ( dev-python/mysql-connector-python )"

DEPEND="${RDEPEND}
	dev-python/setuptools"

EGIT_REPO_URI="https://github.com/zorry/zobsc.git"

python_prepare_all() {
	einfo "Copying needed files from portage"
	cp /usr/lib64/python2.7/site-packages/_emerge/actions.py ${S}/backend/zobcs/pym
	cp /usr/lib64/python2.7/site-packages/_emerge/main.py ${S}/backend/zobcs/pym
	cp /usr/lib64/python2.7/site-packages/_emerge/Scheduler.py ${S}/backend/zobcs/pym
	einfo "Done."
	epatch "${FILESDIR}/portage.patch"
	distutils-r1_python_prepare_all
}

src_install() {
	dodir etc/zobcs
	insinto /etc/zobcs
	doins ${FILESDIR}/zobcs.conf
	dosbin ${S}/backend/zobcs/bin/zobcs_host_jobs
	dosbin  ${S}/backend/zobcs/bin/zobcs_guest_jobs
	#dodoc ${S}/zobcs/sql/zobcs.sql || die
	#dodoc  ${S}/zobcs/doc/Setup.txt || die

	distutils-r1_src_install
}	
