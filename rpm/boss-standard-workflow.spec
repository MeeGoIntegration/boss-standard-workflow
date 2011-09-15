%define name boss-standard-workflow
%define version 0.5.0
%define release 1
%define bossreq python-boss-skynet >= 0.2.2, python-ruote-amqp >= 2.1.1, boss-standard-workflow-common

Summary: Implement the BOSS standard workflow
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-standard-workflow

BuildRequires: python-sphinx, python-ruote-amqp, python-boss-skynet
BuildRequires: python-nose, python-mock, python-coverage
BuildRequires: python-buildservice, python-cheetah
Requires(post): boss-skynet >= 0.3.0-1

%description
This package provides the workflow definitions and tools to enable projects to use them.

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/srv/BOSS/processes
/srv/BOSS/kickstarts
/srv/BOSS/templates
/usr/bin/boss_swf_enable
/usr/bin/platform_setup


%package common
Summary: Common files used by Standard workflow for BOSS

%description common
This package provides the common files used by the standard workflow definitions and the participants used in it.

%post common
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer
    chown bossmaintainer %{_sysconfdir}/skynet/oscrc.conf
    chmod 600 %{_sysconfdir}/skynet/oscrc.conf
    
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
%{_sysconfdir}/skynet/oscrc.conf
%{_datadir}/boss-skynet/__init__.py


%package -n boss-participant-bugzilla
Summary: BOSS participant for Bugzilla
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-bugzilla
BOSS participant for Bugzilla

%post -n boss-participant-bugzilla
if [ $1 -eq 1 ] ; then
    for i in \
            bugzilla \
            check_mentions_bug \
    ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done

    ln -s %{_sysconfdir}/skynet/bugzilla.conf %{_sysconfdir}/skynet/check_mentions_bug.conf

fi

%files -n boss-participant-bugzilla
%defattr(-,root,root)
%{_datadir}/boss-skynet/bz.py
%config(noreplace) %{_sysconfdir}/skynet/bugzilla.conf


%package -n boss-participant-defineimage 
Summary: defineimage BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-defineimage 
defineimage BOSS participant

%post -n boss-participant-defineimage 
if [ $1 -eq 1 ] ; then
        for i in \
            defineimage \
        ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%files -n boss-participant-defineimage
%defattr(-,root,root)
/usr/share/boss-skynet/defineimage.py
%config(noreplace) %{_sysconfdir}/skynet/defineimage.conf


%package -n boss-participant-getbuildlog 
Summary: getbuildlog BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-getbuildlog 
getbuildlog BOSS participant

%post -n boss-participant-getbuildlog 
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer
    for i in \
            getbuildlog \
    ; do
        
        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py

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
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-getchangelog
Get package changelog BOSS Skynet participant

%post -n boss-participant-getchangelog
if [ $1 -eq 1 ] ; then
        for i in \
            get_changelog \
            get_relevant_changelog \
        ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%files -n boss-participant-getchangelog
%defattr(-,root,root)
%{_datadir}/boss-skynet/*.py


%package -n boss-participant-notify
Summary: Notify BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-notify
Notify BOSS Skynet participant

%post -n boss-participant-notify
if [ $1 -eq 1 ] ; then
    skynet install -n notify -p /usr/share/boss-skynet/notify.py
fi

%files -n boss-participant-notify
%defattr(-,root,root)
%config(noreplace) /etc/skynet/notify.conf
%{_datadir}/boss-skynet/notify.py


%package -n boss-participant-obsticket
Summary: Obsticket BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-cheetah
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-obsticket
Obsticket BOSS participant, used to do locking in a process.

%post -n boss-participant-obsticket
if [ $1 -eq 1 ] ; then
    for i in \
            obsticket \
    ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done

    mkdir --mode 744 /var/run/obsticket
    chown nobody:nobody /var/run/obsticket

fi

%files -n boss-participant-obsticket
%defattr(-,root,root)
%attr(744,nobody,nobody) /var/run/obsticket
%{_datadir}/boss-skynet/obsticket.py
%config(noreplace) %{_sysconfdir}/skynet/obsticket.conf


%package -n boss-participant-ots
Summary: OTS BOSS participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-ots
OTS BOSS participant

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%post -n boss-participant-ots
if [ $1 -eq 1 ] ; then
    for i in \
            test_image \
    ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done

fi

%files -n boss-participant-ots
%defattr(-,root,root)
%{_datadir}/boss-skynet/test_image.py
%config(noreplace) %{_sysconfdir}/skynet/test_image.conf
%{python_sitelib}/ots
%{python_sitelib}/*.egg-info


%package -n boss-participant-prechecks
Summary: Prechecks BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-prechecks
Prechecks BOSS Skynet participant

%post -n boss-participant-prechecks
if [ $1 -eq 1 ] ; then
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
            check_has_relevant_changelog \
            check_is_from_devel \
        ; do

        skynet install -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%files -n boss-participant-prechecks
%defattr(-,root,root)
${_datadir}/boss-skynet/check_already_testing.py
${_datadir}/boss-skynet/check_has_relevant_changelog.py
${_datadir}/boss-skynet/check_has_valid_repo.py
${_datadir}/boss-skynet/check_is_from_devel.py
${_datadir}/boss-skynet/check_multiple_destinations.py
${_datadir}/boss-skynet/check_no_changes.py
${_datadir}/boss-skynet/check_package_built_at_source.py
${_datadir}/boss-skynet/check_package_is_complete.py
${_datadir}/boss-skynet/check_spec.py
${_datadir}/boss-skynet/check_submitter_maintainer.py
${_datadir}/boss-skynet/check_valid_changes.py
${_datadir}/boss-skynet/check_yaml_matches_spec.py
${_datadir}/boss-skynet/get_submitter_email.py
${_datadir}/boss-skynet/check_mentions_bug.py
%config(noreplace) %{_sysconfdir}/skynet/check_mentions_bug.conf
%config(noreplace) %{_sysconfdir}/skynet/check_yaml_matches_spec.conf


%package -n boss-participant-resolverequest
Summary: Resolve request BOSS SkyNet participant
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires: python-buildservice >= 0.3.3
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-participant-resolverequest
Resolve request BOSS Skynet participant

%post -n boss-participant-resolverequest
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer

    for i in \
        change_request_state \
        do_build_trial \
        do_revert_trial \
        get_build_trial_results \
        is_repo_published \
        ;
    do
        skynet install -u bossmaintainer -n $i \
	    -p /usr/share/boss-skynet/$i.py
    done
fi

%files -n boss-participant-resolverequest
%defattr(-,root,root)
%{_datadir}/boss-skynet/do_build_trial.py
%{_datadir}/boss-skynet/do_revert_trial.py
%{_datadir}/boss-skynet/get_build_trial_results.py
%{_datadir}/boss-skynet/is_repo_published.py


%package -n boss-participant-standard-workflow
Summary: Standard workflow BOSS SkyNET participants

%description -n boss-participant-standard-workflow
Standard workflow BOSS SkyNET participant

%post -n boss-participant-standard-workflow
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer

    for i in \
        built_notice \
        standard_workflow_handler \
        ;
    do
        skynet install -u bossmaintainer -n $i \
            -p /usr/share/boss-skynet/$i.py
    done
fi

%files -n boss-participant-standard-workflow
%defattr(-,root,root)
%{_datadir}/boss-skynet/built_notice.py
%{_datadir}/boss-skynet/standard_workflow_handler.py


%package -n boss-launcher-robogrator
Summary: Robogrator BOSS SkyNET launcher
Vendor: Islam Amer <islam.amer@nokia.com>

Requires: python >= 2.5
Requires: %{bossreq}
Requires(post): boss-skynet >= 0.3.0-1

%description -n boss-launcher-robogrator
Robogrator BOSS SkyNET launcher

%post -n boss-launcher-robogrator
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer

    # robogrator is special and neeeds to listen to the obs_event queue
    # Note that it still needs skynet register -n obs_event
    skynet install -u bossmaintainer -n robogrator -q obs_event -p /usr/share/boss-skynet/robogrator.py
    echo "robogrator should be registered using:"
    echo "  skynet register -n obs_event"

fi

%files -n boss-launcher-robogrator
%defattr(-,root,root)
%{_datadir}/boss-skynet/robogrator.py
%config(noreplace) %{_sysconfdir}/skynet/robogrator.conf
