%define name boss-standard-workflow
%define version 0.23.0
%define release 1
%define bossreq python-boss-skynet >= 0.2.2, python-ruote-amqp >= 2.1.1, boss-standard-workflow-common
%define skynetreq boss-skynet >= 0.3.3-1

Summary: Implement the BOSS standard workflow
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages/Python
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-standard-workflow

BuildRequires: python-sphinx, python-ruote-amqp >= 2.3.6, python-boss-skynet
# these are required for running the unit tests, which have been
# turned off until python-mock and python-coverage are available
#BuildRequires: python-nose, python-mock, python-coverage, python-debian
BuildRequires: python-buildservice, python-cheetah, python-boss-skynet
Requires(post): %{skynetreq}

%description
This package provides the workflow definitions and tools to enable projects to use them.

%prep
%setup -q -n %{name}-%{version}

%build
echo 'Unit tests not available' > test_results.txt
echo 'Coverage not available' > code_coverage.txt
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} PYSETUPOPT="--prefix=/usr" install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%dir /srv/BOSS
/srv/BOSS/processes
/srv/BOSS/kickstarts
/srv/BOSS/templates
/usr/bin/boss_swf_enable
/usr/bin/platform_setup


%package common
Summary: Common files used by Standard workflow for BOSS
Requires(pre): pwdutils

%description common
This package provides the common files used by the standard workflow definitions and the participants used in it.

%pre common
getent group skynetadm >/dev/null || groupadd -r skynetadm
getent passwd bossmaintainer >/dev/null || \
    useradd -r -g skynetadm -d /home/bossmaintainer -s /sbin/nologin \
    -c "user for participants that need to access shared oscrc" bossmaintainer
exit 0

%post common
if [ $1 -ge 1 ] ; then
    # Add an [obs] section to skynet.conf
    if ! grep oscrc /etc/skynet/skynet.conf >/dev/null 2>&1; then
	cat << EOF >> /etc/skynet/skynet.conf
[obs]
oscrc = /etc/skynet/oscrc.conf
EOF
    fi
    echo "Please ensure your OBS has a 'boss' maintainer user"
fi

%files common
%defattr(-,root,root)
%attr(600, bossmaintainer, skynetadm) %config(noreplace) %{_sysconfdir}/skynet/oscrc.conf
%{_datadir}/boss-skynet/__init__.py


%package -n boss-participant-bugzilla
Summary: BOSS participant for Bugzilla
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires: python-boss-common
Requires: python-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-bugzilla
BOSS participant for Bugzilla

%post -n boss-participant-bugzilla
if [ $1 -ge 1 ] ; then
        skynet install -u bossmaintainer -n bugzilla -p /usr/share/boss-skynet/bz.py
        skynet reload bugzilla || true
fi

%files -n boss-participant-bugzilla
%defattr(-,root,root)
%{_datadir}/boss-skynet/bz.py
%config(noreplace) %{_sysconfdir}/skynet/bugzilla.conf


%package -n boss-participant-defineimage 
Summary: BOSS participant to define testing images
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-defineimage 
BOSS participant to define testing images

%post -n boss-participant-defineimage 
if [ $1 -ge 1 ] ; then
        for i in \
            defineimage \
        ; do

        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true

    done
fi

%files -n boss-participant-defineimage
%defattr(-,root,root)
/usr/share/boss-skynet/defineimage.py
%config(noreplace) %{_sysconfdir}/skynet/defineimage.conf


%package -n boss-participant-getbuildlog 
Summary: BOSS participant to download package build logs
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires: python-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-getbuildlog 
BOSS participant to download package build logs

%post -n boss-participant-getbuildlog 
if [ $1 -ge 1 ] ; then
    for i in \
            getbuildlog \
    ; do
        
        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true

    done
    
fi

%files -n boss-participant-getbuildlog
%defattr(-,root,root)
%{_datadir}/boss-skynet/getbuildlog.py
%config(noreplace) %{_sysconfdir}/skynet/getbuildlog.conf


%package -n boss-participant-getchangelog
Summary: Get package changelog BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-getchangelog
Get package changelog BOSS Skynet participant

%post -n boss-participant-getchangelog
if [ $1 -ge 1 ] ; then
        for i in \
            get_changelog \
            get_relevant_changelog \
        ; do

        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true

    done
fi

%files -n boss-participant-getchangelog
%defattr(-,root,root)
%{_datadir}/boss-skynet/get_relevant_changelog.py
%{_datadir}/boss-skynet/get_changelog.py


%package -n boss-participant-notify
Summary: Notify BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-notify
BOSS SkyNet participant for sending notifications about build results

%post -n boss-participant-notify
if [ $1 -ge 1 ] ; then
    skynet install -n notify -p /usr/share/boss-skynet/notify.py
    skynet reload notify || true
    skynet install -u bossmaintainer -n get_notify_recipients_obs -p /usr/share/boss-skynet/get_notify_recipients_obs.py
    skynet reload get_notify_recipients_obs || true
fi

%files -n boss-participant-notify
%defattr(-,root,root)
%config(noreplace) /etc/skynet/notify.conf
%{_datadir}/boss-skynet/notify.py
%{_datadir}/boss-skynet/get_notify_recipients_obs.py


%package -n boss-participant-mark-project
Summary: Project marking participant
Vendor: Aleksi Suomalainen <aleksi.suomalainen@nomovok.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-mark-project
Project marking participant, used for eg. nightly builds.

%post -n boss-participant-mark-project
if [ $1 -ge 1 ] ; then
        skynet install -u bossmaintainer -n mark_project -p /usr/share/boss-skynet/mark_project.py
        skynet reload mark_project || true
fi

%files -n boss-participant-mark-project
%defattr(-,root,root)
%{_datadir}/boss-skynet/mark_project.py


%package -n boss-participant-obsticket
Summary: Obsticket BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-obsticket
Obsticket BOSS participant, used to do locking in a process.

%post -n boss-participant-obsticket
if [ $1 -ge 1 ] ; then
    for i in \
            obsticket \
    ; do

        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true
    done
fi

%files -n boss-participant-obsticket
%defattr(-,root,root)
%attr(755,bossmaintainer,skynetadm) /var/run/obsticket
%{_datadir}/boss-skynet/obsticket.py
%config(noreplace) %{_sysconfdir}/skynet/obsticket.conf


%package -n boss-participant-ots
Summary: OTS BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires: python-cheetah
Requires(post): %{skynetreq}

%description -n boss-participant-ots
OTS BOSS participant

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%post -n boss-participant-ots
if [ $1 -ge 1 ] ; then
    for i in \
            test_image \
    ; do

        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true

    done

fi

%files -n boss-participant-ots
%defattr(-,root,root)
%{_datadir}/boss-skynet/test_image.py
%config(noreplace) %{_sysconfdir}/skynet/test_image.conf
%{python_sitelib}/ots


%package -n boss-participant-prechecks
Summary: Prechecks BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires: python-boss-common
Requires: rpm-python
Requires: python-debian
Requires: spectacle
Requires(post): %{skynetreq}

%description -n boss-participant-prechecks
Prechecks BOSS Skynet participant

%post -n boss-participant-prechecks
if [ $1 -ge 1 ] ; then
        for i in \
            check_already_testing \
            check_has_valid_repo \
            check_multiple_destinations \
            check_no_changes \
            check_package_built_at_source \
            check_package_is_complete \
            check_spec \
            check_submitter_maintainer \
            get_submitter_email \
            get_request \
            get_userdata \
            get_package_boss_conf \
            check_has_relevant_changelog \
            check_is_from_devel \
            check_mentions_bug \
            check_valid_changes \
	    check_yaml_matches_spec \
        ; do

        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true

    done
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
%{_datadir}/boss-skynet/check_yaml_matches_spec.py
%config(noreplace) %{_sysconfdir}/skynet/check_mentions_bug.conf
%config(noreplace) %{_sysconfdir}/skynet/check_yaml_matches_spec.conf


%package -n boss-participant-resolverequest
Summary: Resolve request BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.5
Requires(post): %{skynetreq}

%description -n boss-participant-resolverequest
Resolve request BOSS Skynet participant

%post -n boss-participant-resolverequest
if [ $1 -ge 1 ] ; then
    for i in \
        change_request_state \
        do_build_trial \
        do_revert_trial \
        get_build_trial_results \
        is_repo_published \
        setup_build_trial \
        remove_build_trial \
        ;
    do
        skynet install -u bossmaintainer -n $i \
	    -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true
    done
fi

%files -n boss-participant-resolverequest
%defattr(-,root,root)
%{_datadir}/boss-skynet/change_request_state.py
%{_datadir}/boss-skynet/do_build_trial.py
%{_datadir}/boss-skynet/do_revert_trial.py
%{_datadir}/boss-skynet/get_build_trial_results.py
%{_datadir}/boss-skynet/is_repo_published.py
%{_datadir}/boss-skynet/setup_build_trial.py
%{_datadir}/boss-skynet/remove_build_trial.py

%package -n boss-participant-standard-workflow
Summary: Standard workflow BOSS SkyNET participants

%description -n boss-participant-standard-workflow
Standard workflow BOSS SkyNET participant

%post -n boss-participant-standard-workflow
if [ $1 -ge 1 ] ; then
    skynet install -u bossmaintainer -n built_notice -r built_\.\* -p /usr/share/boss-skynet/built_notice.py
    skynet reload built_notice || true
    skynet install -u bossmaintainer -n request_notice -r req_changed_\.\* -p /usr/share/boss-skynet/request_notice.py
    skynet reload request_notice || true
fi

%files -n boss-participant-standard-workflow
%defattr(-,root,root)
%{_datadir}/boss-skynet/built_notice.py
%{_datadir}/boss-skynet/request_notice.py
%{_datadir}/boss-skynet/notify_irc.py

%package -n boss-participant-update-patterns
Summary: OBS Pattern updating participant
Vendor: Aleksi Suomalainen <aleksi.suomalainen@nomovok.com>

Requires: python >= 2.5
Requires: python-buildservice >= 0.3.13
Requires: python-boss-common >= %{version}
Requires: %{bossreq}
Requires(post): %{skynetreq}

%description -n boss-participant-update-patterns
OBS Pattern updating participant

%post -n boss-participant-update-patterns
if [ $1 -ge 1 ] ; then
    for i in \
        update_patterns get_provides
    do
        skynet install -u bossmaintainer -n $i \
            -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true
    done
fi

%files -n boss-participant-update-patterns
%defattr(-,root,root)
%{_datadir}/boss-skynet/update_patterns.py
%{_datadir}/boss-skynet/get_provides.py


%package -n boss-participant-get-kickstarts
Summary: Participant for downloading kickstart files
Vendor: Pami Ketolainen <ext-pami.o.ketolainen@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-boss-common >= %{version}
Requires(post): %{skynetreq}

%description -n boss-participant-get-kickstarts
This participant fetches the image configuration RPM and extracts kickstart
files from it.

%post -n boss-participant-get-kickstarts
if [ $1 -ge 1 ] ; then
    for i in \
        get_kickstarts
    do
        skynet install -u bossmaintainer -n $i \
            -p /usr/share/boss-skynet/$i.py
        skynet reload $i || true
    done
fi

%files -n boss-participant-get-kickstarts
%defattr(-,root,root)
%{_datadir}/boss-skynet/get_kickstarts.py


%package -n boss-launcher-robogrator
Summary: Robogrator BOSS SkyNET launcher
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires(post): %{skynetreq}

%description -n boss-launcher-robogrator
Robogrator BOSS SkyNET launcher

%post -n boss-launcher-robogrator
if [ $1 -ge 1 ] ; then
    # robogrator is special and neeeds to listen to the obs_event queue
    # Note that it still needs skynet register -n obs_event
    skynet install -u bossmaintainer -n robogrator -q obs_event -r obs_event -p /usr/share/boss-skynet/robogrator.py
    echo "robogrator should be registered using:"
    echo "  skynet register -n obs_event"
    skynet reload robogrator || true

fi

%files -n boss-launcher-robogrator
%defattr(-,root,root)
%{_datadir}/boss-skynet/robogrator.py
%config(noreplace) %{_sysconfdir}/skynet/robogrator.conf


%package -n python-boss-common
Summary: Common python libraries for BOSS
Vendor: Pami Ketolainen <ext-pami.o.ketolainen@nokia.com>

Requires: python >= 2.5
Requires: python-ruote-amqp
Requires: python-buildservice
Requires: rpm
Requires: cpio

%description -n python-boss-common
Common python libraries used in BOSS participants

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%files -n python-boss-common
%defattr(-,root,root)
%{python_sitelib}/boss
%{python_sitelib}/*.egg-info
