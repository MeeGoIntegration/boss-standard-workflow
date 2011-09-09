%define name boss-standard-workflow
%define version 0.0.1
%define release 1

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

Requires(post): boss-skynet

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
/srv/BOSS
/srv/BOSS/processes
/srv/BOSS/processes/StandardWorkflow
/srv/BOSS/processes/StandardWorkflow/BOSS_handle_SR
/srv/BOSS/processes/StandardWorkflow/trial_build_monitor
/usr/bin/swf_enable
%define name boss-participant-bugzilla
%define version 0.4.4
%define release 1

Summary: BOSS participant for Bugzilla
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-bugzilla

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet

%description
BOSS participant for Bugzilla

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install


%post
if [ $1 -eq 1 ] ; then
    for i in \
            bugzilla \
            check_mentions_bug \
    ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done

    ln -s %{_sysconfdir}/skynet/bugzilla.conf %{_sysconfdir}/skynet/check_mentions_bug.conf

fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_datadir}/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/bugzilla.conf

%define name boss-participant-defineimage 
%define version 0.2.1
%define release 1

Summary: defineimage BOSS participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-defineimage

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet

%description
defineimage BOSS participant

%prep
%setup -q -n %{name}-%{version}

%build
make faketest
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ $1 -eq 1 ] ; then
        for i in \
            defineimage \
        ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
fi



%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/defineimage.conf


%changelog
* Thu Aug 16 2011 Islam Amer <islam.amer@nokia.com> 0.2.0
- Ported to SkyNet
- Sphinx docs

* Thu Aug 19 2010 Islam Amer <islam.amer at nokia.com>
- packaged 0.1

%define name boss-participant-getbuildlog 
%define version 0.2.2
%define release 1

Summary: getbuildlog BOSS participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-getbuildlog

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet

%description
getbuildlog BOSS participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Add a user who's allowed to see the oscrc
    useradd bossmaintainer --system --home /home/bossmaintainer
    for i in \
            getbuildlog \
    ; do
        
        skynet install -u bossmaintainer -n $i -p /usr/share/boss-skynet/$i.py

    done
    
fi


%files
%defattr(-,root,root)
%{_datadir}/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/getbuildlog.conf

%changelog
* Fri Aug 12 2011 Islam Amer <islam.amer@nokia.com> 0.2.0
- Ported to skynet
- Sphinx documentation

* Thu Aug 19 2010 Islam Amer <islam.amer at nokia.com>
- packaged 0.1

%define name boss-participant-getchangelog
%define version 0.3.4
%define release 1

Summary: Get package changelog BOSS SkyNet participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-getchangelog

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet

%description
Get package changelog BOSS Skynet participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install


%post
if [ $1 -eq 1 ] ; then
        for i in \
            get_changelog \
            get_relevant_changelog \
        ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
Summary: Notify BOSS SkyNet participant
Name: boss-participant-notify
Version: 0.5.2
Release: 1
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-notify

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet
Requires(post): boss-skynet

%description
Notify BOSS Skynet participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%post
if [ $1 -eq 1 ] ; then
    skynet make_participant -n notify -p /usr/share/boss-skynet/notify.py
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%config(noreplace) /etc/skynet/notify.conf
/usr/share/boss-skynet/notify.py
/etc/skynet
/usr/share/boss-skynet
Summary: Obsticket BOSS participant
Name: boss-participant-obsticket
Version: 0.3.1
Release: 1

Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages/Python
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-obsticket

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-ruote-amqp >= 2.1.1
Requires: python-cheetah
Requires: python-ruote-amqp >= 2.1.1-1
Requires(post): boss-skynet

%description
Obsticket BOSS participant, used to do locking in a process.

%prep
%setup -q -n %{name}-%{version}

%build
make faketest
make

%install
make DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ $1 -eq 1 ] ; then
    for i in \
            obsticket \
    ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done

    mkdir --mode 744 /var/run/obsticket
    chown nobody:nobody /var/run/obsticket

fi

%files
%defattr(-,root,root)
%attr(744,nobody,nobody) /var/run/obsticket
%{_datadir}/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/obsticket.conf

%changelog
Summary: OTS BOSS participant
Name: boss-participant-ots
Version: 0.6.1
Release: 1

Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-ots

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires: python-cheetah
Requires(post): boss-skynet


%description
OTS BOSS participant


%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ $1 -eq 1 ] ; then
    for i in \
            test_image \
    ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done

fi


%files
%defattr(-,root,root)
%{_datadir}/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/test_image.conf
%{python_sitelib}/ots
%{python_sitelib}/*.egg-info


%changelog
* Fri Aug 19 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> 0.6.1
- Add unit tests

* Tue Aug 16 2011 Islam Amer <islam.amer@nokia.com> 0.6.0
- Sphinx documentation
- Use image namespace

* Mon May 23 2011 Aleksi Suomalainen <aleksi.suomalainen at nomovok.com>
- Packaged 0.5 : Skynet support

* Fri Dec 10 2010 Islam Amer <islam.amer at nokia.com>
- packaged 0.4 : Parallel execution init script and latest template

* Thu Aug 19 2010 Islam Amer <islam.amer at nokia.com>
- packaged 0.1

%define name boss-participant-prechecks
%define version 0.2.3
%define release 1

Summary: Prechecks BOSS SkyNet participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-prechecks

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires: python-buildservice >= 0.3.1
Requires(post): boss-skynet

%description
Prechecks BOSS Skynet participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install


%post
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

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
%define name boss-participant-resolverequest
%define version 0.3.4
%define release 1

Summary: Resolve request BOSS SkyNet participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-resolverequest

BuildRequires: python-sphinx

Requires: python >= 2.5
Requires: python-boss-skynet
Requires: python-buildservice >= 0.3.3
Requires(post): boss-skynet

%description
Resolve request BOSS Skynet participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install


%post
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
        skynet make_participant -u bossmaintainer -n $i \
	    -p /usr/share/boss-skynet/$i.py
    done

    # Add an [obs] section to skynet.conf
    if ! grep oscrc /etc/skynet/skynet.conf >/dev/null 2>&1; then
	cat << EOF >> /etc/skynet/skynet.conf
[obs]
oscrc = /etc/skynet/oscrc
EOF
    fi
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
%defattr(600,obsmaintainer,root)
/etc/skynet/oscrc
Summary: Robogrator BOSS SkyNET launcher
Name: boss-launcher-robogrator
Version: 0.4.3
Release: 1

Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-launcher-robogrator

BuildRequires: python-sphinx, python-ruote-amqp, python-boss-skynet
Requires: python >= 2.5
Requires: python-boss-skynet >= 0.2.2
Requires(post): boss-skynet

%description
Robogrator BOSS SkyNET launcher

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%post
if [ $1 -eq 1 ] ; then
    for i in \
            built_notice \
            standard_workflow_handler \
    ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
    # robogrator is special and neeeds to listen to the obs_event queue
    # Note that it still needs skynet register -n obs_event
    skynet make_participant -n robogrator -q obs_event -p /usr/share/boss-skynet/robogrator.py
    echo "robogrator should be registered using:"
    echo "  skynet register -n obs_event"

fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_datadir}/boss-skynet/*.py
%config(noreplace) %{_sysconfdir}/skynet/robogrator.conf
