%define name boss-standard-workflow
%define version 0.30.0
%define release 1
%define bossreq python3-boss-skynet >= 0.6.0, python3-ruote-amqp >= 2.4.1, boss-standard-workflow-common
%define skynetreq python3-boss-skynet >= 0.3.3-1
%define svdir %{_sysconfdir}/supervisor/conf.d/

Summary: Implement the BOSS standard workflow
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: GPLv2+
Group: Development/Languages/Python
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-standard-workflow

BuildRequires: python3-Sphinx, python3-ruote-amqp >= 2.3.6, python3-boss-skynet
# these are required for running the unit tests, which have been
# turned off until python3-mock and python3-coverage are available
#BuildRequires: python3-nose, python3-mock, python3-coverage, python3-debian
BuildRequires: python3-buildservice, python3-Cheetah3, python3-boss-skynet
Requires(post): %{skynetreq}

%description
This package provides the workflow definitions and tools to enable projects to use them.

%prep
%setup -q -n %{name}-%{version}

%build
echo 'Unit tests not available' > test_results.txt
echo 'Coverage not available' > code_coverage.txt
pushd modules
%python3_build
popd
make

%install
rm -rf $RPM_BUILD_ROOT
pushd modules
%python3_install
popd
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/var/log/supervisor

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%dir /srv/BOSS
%dir %{_sysconfdir}/supervisor
%dir %{svdir}
%dir /var/log/supervisor
/srv/BOSS/processes
/srv/BOSS/kickstarts
/srv/BOSS/templates
/usr/bin/boss_swf_enable
/usr/bin/platform_setup
/usr/bin/launcher.py


%package common
Summary: Common files used by Standard workflow for BOSS
Requires(pre): pwdutils
Requires(post): %{skynetreq}

%description common
This package provides the common files used by the standard workflow definitions and the participants used in it.

%pre common
getent group skynetadm >/dev/null || groupadd -r skynetadm
getent passwd bossmaintainer >/dev/null || \
    useradd -r -g skynetadm -d /home/bossmaintainer -s /sbin/nologin -m \
    -c "user for participants that need to access shared oscrc" bossmaintainer
exit 0

%post common
if [ $1 -ge 1 ] ; then
    echo "Please modify /etc/skynet/oscrc.conf to match the bot user you
          have created in your OBS"
fi

%files common
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/skynet/conf.d/bsw-common.conf
%dir %{_sysconfdir}/skynet/conf.d
%attr(600, bossmaintainer, skynetadm) %config(noreplace) %{_sysconfdir}/skynet/oscrc.conf


%package -n boss-participant-bugzilla
Summary: BOSS participant for Bugzilla
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires: python3-boss-common
Requires: python3-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-bugzilla
BOSS participant for Bugzilla

%post -n boss-participant-bugzilla
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload bugzilla || true
fi

%files -n boss-participant-bugzilla
%defattr(-,root,root)
%{_datadir}/boss-skynet/bz.py
%config(noreplace) %{_sysconfdir}/skynet/bugzilla.conf
%config(noreplace) %{svdir}/bugzilla.conf


%package -n boss-participant-qa 
Summary: BOSS participants that do qa related things
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires: python3-boss-common
Requires: python3-requests
Requires(post): %{skynetreq}

%description -n boss-participant-qa
BOSS participants that do qa related things

%post -n boss-participant-qa
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload select_test_packages || true
    skynet reload filter_test_packages || true
    skynet reload qareports || true
    skynet reload qa_vote || true
fi

%files -n boss-participant-qa
%defattr(-,root,root)
%{_datadir}/boss-skynet/select_test_packages.py
%{_datadir}/boss-skynet/filter_test_packages.py
%{_datadir}/boss-skynet/qareports.py
%{_datadir}/boss-skynet/qa_vote.py
%config(noreplace) %{svdir}/select_test_packages.conf
%config(noreplace) %{svdir}/filter_test_packages.conf
%config(noreplace) %{svdir}/qareports.conf
%config(noreplace) %{svdir}/qa_vote.conf
%config(noreplace) %{_sysconfdir}/skynet/qareports.conf
%config(noreplace) %{_sysconfdir}/skynet/qa_vote.conf


%package -n boss-participant-getbuildlog 
Summary: BOSS participant to download package build logs
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires: python3-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-getbuildlog 
BOSS participant to download package build logs

%post -n boss-participant-getbuildlog 
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload getbuildlog || true
fi

%files -n boss-participant-getbuildlog
%defattr(-,root,root)
%{_datadir}/boss-skynet/getbuildlog.py
%config(noreplace) %{_sysconfdir}/skynet/getbuildlog.conf
%config(noreplace) %{svdir}/getbuildlog.conf


%package -n boss-participant-getchangelog
Summary: Get package changelog BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-getchangelog
Get package changelog BOSS Skynet participant

%post -n boss-participant-getchangelog
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload get_changelog get_relevant_changelog || true
fi

%files -n boss-participant-getchangelog
%defattr(-,root,root)
%{_datadir}/boss-skynet/get_relevant_changelog.py
%{_datadir}/boss-skynet/get_changelog.py
%config(noreplace) %{svdir}/get_changelog.conf
%config(noreplace) %{svdir}/get_relevant_changelog.conf


%package -n boss-participant-notify
Summary: Notify BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-notify
BOSS SkyNet participant for sending notifications about build results

%post -n boss-participant-notify
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload notify get_notify_recipients_obs || true
fi

%files -n boss-participant-notify
%defattr(-,root,root)
%config(noreplace) /etc/skynet/notify.conf
%{_datadir}/boss-skynet/notify.py
%{_datadir}/boss-skynet/get_notify_recipients_obs.py
%config(noreplace) %{svdir}/notify.conf
%config(noreplace) %{svdir}/get_notify_recipients_obs.conf


%package -n boss-participant-mark-project
Summary: Project marking participant
Vendor: Aleksi Suomalainen <aleksi.suomalainen@nomovok.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.1
Requires(post): %{skynetreq}

%description -n boss-participant-mark-project
Project marking participant, used for eg. nightly builds.

%post -n boss-participant-mark-project
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload mark_project || true
fi

%files -n boss-participant-mark-project
%defattr(-,root,root)
%{_datadir}/boss-skynet/mark_project.py
%config(noreplace) %{svdir}/mark_project.conf


%package -n boss-participant-obsticket
Summary: Obsticket BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-obsticket
Obsticket BOSS participant, used to do locking in a process.

%post -n boss-participant-obsticket
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload obsticket || true
    if [ -d /var/run/obsticket ] ; then
      mv /var/run/obsticket/* /var/lib/obsticket
    fi
fi

%files -n boss-participant-obsticket
%defattr(-,root,root)
%attr(755,bossmaintainer,skynetadm) /var/lib/obsticket
%{_datadir}/boss-skynet/obsticket.py
%config(noreplace) %{_sysconfdir}/skynet/obsticket.conf
%config(noreplace) %{svdir}/obsticket.conf


%package -n boss-participant-ots
Summary: OTS BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires: python3-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-ots
OTS BOSS participant

%post -n boss-participant-ots
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload test_image || true
fi

%files -n boss-participant-ots
%defattr(-,root,root)
%{_datadir}/boss-skynet/test_image.py
%config(noreplace) %{_sysconfdir}/skynet/test_image.conf
%config(noreplace) %{svdir}/test_image.conf
%{python3_sitelib}/ots


%package -n boss-participant-prechecks
Summary: Prechecks BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires: python3-boss-common
Requires: python3-rpm
Requires: python3-debian
Requires(post): %{skynetreq}

%description -n boss-participant-prechecks
Prechecks BOSS Skynet participant

%post -n boss-participant-prechecks
if [ $1 -ge 1 ] ; then
        skynet apply || true
        PARTS="check_already_testing
            check_has_valid_repo
            check_multiple_destinations
            check_no_changes
            check_package_built_at_source
            check_package_is_complete
            check_spec
            check_submitter_maintainer
            get_submitter_email
            get_request
            get_userdata
            get_package_boss_conf
            check_has_relevant_changelog
            check_is_from_devel
            check_mentions_bug
            check_valid_changes"

        skynet reload $PARTS || true

fi

%files -n boss-participant-prechecks
%defattr(-,root,root)
%{_datadir}/boss-skynet/check_already_testing.py
%{_datadir}/boss-skynet/check_has_valid_repo.py
%{_datadir}/boss-skynet/check_multiple_destinations.py
%{_datadir}/boss-skynet/check_no_changes.py
%{_datadir}/boss-skynet/check_package_built_at_source.py
%{_datadir}/boss-skynet/check_package_is_complete.py
%{_datadir}/boss-skynet/check_spec.py
%{_datadir}/boss-skynet/check_submitter_maintainer.py
%{_datadir}/boss-skynet/get_submitter_email.py
%{_datadir}/boss-skynet/get_request.py
%{_datadir}/boss-skynet/get_userdata.py
%{_datadir}/boss-skynet/get_package_boss_conf.py
%{_datadir}/boss-skynet/check_has_relevant_changelog.py
%{_datadir}/boss-skynet/check_is_from_devel.py
%{_datadir}/boss-skynet/check_mentions_bug.py
%{_datadir}/boss-skynet/check_valid_changes.py
%config(noreplace) %{svdir}/check_already_testing.conf
%config(noreplace) %{svdir}/check_has_valid_repo.conf
%config(noreplace) %{svdir}/check_multiple_destinations.conf
%config(noreplace) %{svdir}/check_no_changes.conf
%config(noreplace) %{svdir}/check_package_built_at_source.conf
%config(noreplace) %{svdir}/check_package_is_complete.conf
%config(noreplace) %{svdir}/check_spec.conf
%config(noreplace) %{svdir}/check_submitter_maintainer.conf
%config(noreplace) %{svdir}/get_submitter_email.conf
%config(noreplace) %{svdir}/get_request.conf
%config(noreplace) %{svdir}/get_userdata.conf
%config(noreplace) %{svdir}/get_package_boss_conf.conf
%config(noreplace) %{svdir}/check_has_relevant_changelog.conf
%config(noreplace) %{svdir}/check_is_from_devel.conf
%config(noreplace) %{svdir}/check_mentions_bug.conf
%config(noreplace) %{svdir}/check_valid_changes.conf


%package -n boss-participant-resolverequest
Summary: Resolve request BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5, python3-lxml
Requires(post): %{skynetreq}

%description -n boss-participant-resolverequest
Resolve request BOSS Skynet participant

%post -n boss-participant-resolverequest
if [ $1 -ge 1 ] ; then
    skynet apply || true
    PARTS="change_request_state
        do_revert_trial
        get_build_trial_results
        is_repo_published
        setup_build_trial
        remove_build_trial
        get_build_results
        get_versions
        trigger_broken"
        skynet reload $PARTS || true
fi

%files -n boss-participant-resolverequest
%defattr(-,root,root)
%{_datadir}/boss-skynet/change_request_state.py
%{_datadir}/boss-skynet/do_revert_trial.py
%{_datadir}/boss-skynet/get_build_trial_results.py
%{_datadir}/boss-skynet/get_build_results.py
%{_datadir}/boss-skynet/get_versions.py
%{_datadir}/boss-skynet/trigger_broken.py
%{_datadir}/boss-skynet/is_repo_published.py
%{_datadir}/boss-skynet/setup_build_trial.py
%{_datadir}/boss-skynet/remove_build_trial.py
%config(noreplace) %{svdir}/change_request_state.conf
%config(noreplace) %{svdir}/do_revert_trial.conf
%config(noreplace) %{svdir}/get_build_trial_results.conf
%config(noreplace) %{svdir}/get_build_results.conf
%config(noreplace) %{svdir}/get_versions.conf
%config(noreplace) %{svdir}/trigger_broken.conf
%config(noreplace) %{svdir}/is_repo_published.conf
%config(noreplace) %{svdir}/setup_build_trial.conf
%config(noreplace) %{svdir}/remove_build_trial.conf

%package -n boss-participant-standard-workflow
Summary: Standard workflow BOSS SkyNET participants
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires(post): %{skynetreq}
%description -n boss-participant-standard-workflow

Standard workflow BOSS SkyNET participant

%post -n boss-participant-standard-workflow
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload built_notice request_notice notify_irc || true
fi

%files -n boss-participant-standard-workflow
%defattr(-,root,root)
%{_datadir}/boss-skynet/built_notice.py
%{_datadir}/boss-skynet/request_notice.py
%{_datadir}/boss-skynet/notify_irc.py
%config(noreplace) %{_sysconfdir}/skynet/notify_irc.conf
%config(noreplace) %{svdir}/built_notice.conf
%config(noreplace) %{svdir}/request_notice.conf
%config(noreplace) %{svdir}/notify_irc.conf

%package -n boss-participant-update-patterns
Summary: OBS Pattern updating participant
Vendor: Aleksi Suomalainen <aleksi.suomalainen@nomovok.com>

Requires: python3 >= 3.6
Requires: python3-buildservice >= 0.3.13
Requires: python3-boss-common >= %{version}
Requires: %{bossreq}
Requires(post): %{skynetreq}

%description -n boss-participant-update-patterns
OBS Pattern updating participant

%post -n boss-participant-update-patterns
if [ $1 -ge 1 ] ; then
        skynet apply || true
        skynet reload update_patterns get_provides || true
        skynet reload update_meta get_provides || true
fi

%files -n boss-participant-update-patterns
%defattr(-,root,root)
%{_datadir}/boss-skynet/update_meta.py
%{_datadir}/boss-skynet/update_patterns.py
%{_datadir}/boss-skynet/get_provides.py
%config(noreplace) %{svdir}/update_patterns.conf
%config(noreplace) %{svdir}/get_provides.conf
%config(noreplace) %{svdir}/update_meta.conf


%package -n boss-participant-get-kickstarts
Summary: Participant for downloading kickstart files
Vendor: Pami Ketolainen <ext-pami.o.ketolainen@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-boss-common >= %{version}
Requires(post): %{skynetreq}

%description -n boss-participant-get-kickstarts
This participant fetches the image configuration RPM and extracts kickstart
files from it.

%post -n boss-participant-get-kickstarts
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload get_kickstarts || true
fi

%files -n boss-participant-get-kickstarts
%defattr(-,root,root)
%{_datadir}/boss-skynet/get_kickstarts.py
%config(noreplace) %{svdir}/get_kickstarts.conf


%package -n boss-launcher-robogrator
Summary: Robogrator BOSS SkyNET launcher
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires(post): %{skynetreq}

%description -n boss-launcher-robogrator
Robogrator BOSS SkyNET launcher

%post -n boss-launcher-robogrator
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload robogrator || true
fi

%files -n boss-launcher-robogrator
%defattr(-,root,root)
%{_datadir}/boss-skynet/robogrator.py
%config(noreplace) %{_sysconfdir}/skynet/robogrator.conf
%config(noreplace) %{svdir}/robogrator.conf


%package -n python3-boss-common
Summary: Common python libraries for BOSS
Vendor: Pami Ketolainen <ext-pami.o.ketolainen@nokia.com>

Requires: python3 >= 3.6
Requires: python3-ruote-amqp
Requires: python3-buildservice
Requires: python3-rpm >= 4.10.0
# yum
Requires: python3-urlgrabber
Requires: python3-curl
Requires: python3-yum-metadata-parser
Requires: cpio

%description -n python3-boss-common
Common python libraries used in BOSS participants

%files -n python3-boss-common
%defattr(-,root,root)
%{python3_sitelib}/boss
%{python3_sitelib}/rpmUtils
%{python3_sitelib}/yum
%{python3_sitelib}/*.egg-info

%package -n boss-participant-repodiff
Summary: BOSS participants that do repo diff related things
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-repodiff
BOSS participants that do repodiff related things

%post -n boss-participant-repodiff
if [ $1 -ge 1 ] ; then
    skynet apply || true
    skynet reload obs_repodiff || true
fi

%files -n boss-participant-repodiff
%defattr(-,root,root)
%{_datadir}/boss-skynet/obs_repodiff.py
%{_datadir}/boss-skynet/create_request.py
%config(noreplace) %{_sysconfdir}/skynet/obs_repodiff.conf
%config(noreplace) %{svdir}/obs_repodiff.conf
%config(noreplace) %{svdir}/create_request.conf
%{_bindir}/repodiff.py
%{python3_sitelib}/repo_diff.py
%{python3_sitelib}/__pycache__/repo_diff*

%package -n boss-participant-l10n
Summary: BOSS participant that update translation files
Vendor: Dmitry Rozhkov <dmitry.rozhkov@jolla.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice
Requires: python3-requests
Requires: git-core
Requires: python3-requests
Requires(post): %{skynetreq}

%description -n boss-participant-l10n
BOSS participant that update translation files for Pootle

%files -n boss-participant-l10n
%defattr(-,root,root)
%{_datadir}/boss-skynet/l10n_update_ts.py
%{_datadir}/boss-skynet/check_l10n_update.py
%config(noreplace) %{svdir}/check_l10n_update.conf
%config(noreplace) %{svdir}/l10n_update_ts.conf
%config(noreplace) %{_sysconfdir}/skynet/l10n_update_ts.conf


%package -n boss-participant-autodoc
Summary: BOSS participant that deploys documentation files
Vendor: Islam Amer <islam.amer@jolla.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice
Requires: python3-requests
Requires: python3-boss-common >= %{version}
Requires(post): %{skynetreq}

%description -n boss-participant-autodoc
BOSS participant that deploys documentation files for an HTTP server

%files -n boss-participant-autodoc
%defattr(-,root,root)
%{_datadir}/boss-skynet/autodoc_deploy.py
%config(noreplace) %{svdir}/autodoc_deploy.conf
%config(noreplace) %{_sysconfdir}/skynet/autodoc_deploy.conf

%package -n boss-participant-autoks
Summary: BOSS participant that deploys documentation files
Vendor: Islam Amer <islam.amer@jolla.com>

Requires: python3 >= 3.6
Requires: %{bossreq}
Requires: python3-buildservice
Requires: python3-boss-common >= %{version}
Requires(post): %{skynetreq}

%description -n boss-participant-autoks
BOSS participant that deploys ks files for an HTTP server

%files -n boss-participant-autoks
%defattr(-,root,root)
%{_datadir}/boss-skynet/autoks_deploy.py
%config(noreplace) %{svdir}/autoks_deploy.conf
%config(noreplace) %{_sysconfdir}/skynet/autoks_deploy.conf
