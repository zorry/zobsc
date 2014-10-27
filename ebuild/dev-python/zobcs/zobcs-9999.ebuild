# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"
PYTHON_COMPAT=( python{2_7,3_3,3_4})
SUPPORT_PYTHON_ABIS="1"

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

PYTHON_MODNAME="zobcs"

src_prepare() {
	einfo "Copying needed files from portage"
	cp /usr/lib64/portage/pym/_emerge/actions.py ${S}/zobcs/pym
	cp /usr/lib64/portage/pym/_emerge/main.py ${S}/zobcs/pym
	cp /usr/lib64/portage/pym/_emerge/Scheduler.py ${S}/zobcs/pym
	einfo "Done."
	epatch "${FILESDIR}/zobcs_portage_actions.patch"
	epatch "${FILESDIR}/zobcs_portage_main.patch"
	epatch "${FILESDIR}/zobcs_portage_Scheduler.patch"
}

src_install() {
	dodir /var/lib/zobcs || die
	dodir etc/zobcs || die
	insinto /etc/zobcs
	doins ${FILESDIR}/zobcs.conf || die
	dosbin ${S}/zobcs/bin/zobcs_host_jobs || die
	dosbin  ${S}/zobcs/bin/zobcs_guest_jobs || die
	#dodoc ${S}/zobcs/sql/zobcs.sql || die
	dodoc  ${S}/zobcs/doc/Setup.txt || die

	distutils-r1_src_install
}	
